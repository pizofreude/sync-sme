"""Discord client bootstrap — powered by discli (serve mode)."""

from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
import threading
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

from bot.handlers import build_message_handler
from db.models import SQLiteStateStore
from gaps.briefing import DailyBriefingGenerator
from gaps.detector import GapDetector
from gaps.tracker import GapTracker
from integrations.craig import CraigClient
from integrations.obsidian import ObsidianWriter
from integrations.plane import PlaneCLI
from llm.parser import TaskParser
from llm.router import NineRouterClient
from llm.summarizer import MeetingSummarizer
from meeting.pipeline import MeetingPipeline
from meeting.recorder import CraigRecorder
from meeting.transcriber import SpeechmaticsTranscriber

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class BotSettings:
    discord_bot_token: str
    ninerouter_api_key: str
    plane_workspace_slug: str
    action_items_channel: str = "action-items"
    llm_model: str = "nvidia/llama-3.1-70b-instruct"
    ninerouter_endpoint: str = "https://9router.com/api/v1/chat/completions"
    state_db_path: str = "sync_sme.db"
    plane_assignee_map: dict[str, str] = field(default_factory=dict)
    # Day 2: meeting pipeline
    craig_api_key: str = ""
    craig_api_base: str = "https://craig.chat/api"
    obsidian_vault_path: str = ""
    speechmatics_api_key: str = ""
    plane_api_token: str = ""
    plane_project_id: str = ""
    # Day 3: gap detection + briefing
    gap_detection_hours: int = 24
    briefing_cron_hour: int = 9
    briefing_cron_minute: int = 0

    @classmethod
    def from_env(cls) -> "BotSettings":
        load_dotenv()
        raw_assignee_map = os.getenv("PLANE_ASSIGNEE_MAP", "")
        assignee_map = {}
        for item in filter(None, (entry.strip() for entry in raw_assignee_map.split(","))):
            if ":" not in item:
                continue
            discord_id, plane_member = item.split(":", 1)
            assignee_map[discord_id.strip()] = plane_member.strip()

        vault_path = os.getenv("OBSIDIAN_VAULT_PATH", "")
        if vault_path.startswith("~"):
            vault_path = str(Path(vault_path).expanduser())
        elif "$HOME" in vault_path:
            vault_path = vault_path.replace("$HOME", str(Path.home()))

        # Parse BRIEFING_CRON (format: "MM HH * * *")
        cron_hour, cron_minute = 9, 0
        raw_cron = os.getenv("BRIEFING_CRON", "0 9 * * *")
        parts = raw_cron.split()
        if len(parts) >= 2:
            try:
                cron_minute = int(parts[0])
                cron_hour = int(parts[1])
            except ValueError:
                pass

        return cls(
            discord_bot_token=os.getenv("DISCORD_BOT_TOKEN", ""),
            ninerouter_api_key=os.getenv("NINEROUTER_API_KEY", ""),
            plane_workspace_slug=os.getenv("PLANE_WORKSPACE_SLUG", ""),
            action_items_channel=os.getenv("ACTION_ITEMS_CHANNEL", "action-items"),
            llm_model=os.getenv("LLM_MODEL", "nvidia/llama-3.1-70b-instruct"),
            ninerouter_endpoint=os.getenv("NINEROUTER_ENDPOINT", "https://9router.com/api/v1/chat/completions"),
            state_db_path=os.getenv("SYNC_SME_DB_PATH", "sync_sme.db"),
            plane_assignee_map=assignee_map,
            craig_api_key=os.getenv("CRAIG_API_KEY", ""),
            craig_api_base=os.getenv("CRAIG_API_BASE", "https://craig.chat/api"),
            obsidian_vault_path=vault_path,
            speechmatics_api_key=os.getenv("SPEECHMATICS_API_KEY", ""),
            plane_api_token=os.getenv("PLANE_API_TOKEN", ""),
            plane_project_id=os.getenv("PLANE_PROJECT_ID", ""),
            gap_detection_hours=int(os.getenv("GAP_DETECTION_HOURS", "24")),
            briefing_cron_hour=cron_hour,
            briefing_cron_minute=cron_minute,
        )


def _detect_plane_cli() -> bool:
    return shutil.which("plane") is not None


def _send_action(proc: subprocess.Popen, action: dict) -> None:
    """Write a JSON action to discli's stdin."""
    proc.stdin.write(json.dumps(action) + "\n")
    proc.stdin.flush()


def _add_reaction(proc: subprocess.Popen, channel_id: str, message_id: str, emoji: str) -> None:
    """Add a reaction to a message via discli CLI command."""
    subprocess.run(
        ["discli", "-y", "reaction", "add", channel_id, message_id, emoji],
        capture_output=True,
        text=True,
    )


def run() -> None:
    """Run the sync-sme bot using discli serve mode."""
    logging.basicConfig(level=logging.INFO)
    settings = BotSettings.from_env()

    if not settings.discord_bot_token:
        raise RuntimeError("DISCORD_BOT_TOKEN is required")

    router = NineRouterClient(
        api_key=settings.ninerouter_api_key,
        model=settings.llm_model,
        endpoint=settings.ninerouter_endpoint,
    )
    parser = TaskParser(router=router)

    # Plane issue creator — try CLI first, fall back to dry-run
    plane_cli_available = _detect_plane_cli()
    if not plane_cli_available and not settings.plane_api_token:
        logger.warning("Plane CLI not found and PLANE_API_TOKEN not set — running in dry-run mode")
    plane = PlaneCLI(
        workspace_slug=settings.plane_workspace_slug,
        assignee_map=settings.plane_assignee_map,
        dry_run=not plane_cli_available and not settings.plane_api_token,
    )

    state_store = SQLiteStateStore(settings.state_db_path)

    # Day 3: Gap tracker + detector
    gap_tracker = GapTracker(db_path=settings.state_db_path)
    gap_detector = GapDetector(tracker=gap_tracker, detection_hours=settings.gap_detection_hours)

    # Day 3: Daily briefing generator
    briefing_generator = DailyBriefingGenerator(router=router)
    obsidian = ObsidianWriter(vault_path=Path(settings.obsidian_vault_path)) if settings.obsidian_vault_path else None

    def add_reaction(channel_id: str, message_id: str, emoji: str) -> None:
        """Callback for the handler to add reactions."""
        _add_reaction(None, channel_id, message_id, emoji)

    on_message = build_message_handler(
        task_parser=parser,
        plane_client=plane,
        state_store=state_store,
        action_items_channel=settings.action_items_channel,
        gap_tracker=gap_tracker,
        add_reaction=add_reaction,
    )

    # Day 2: Meeting pipeline
    summarizer = MeetingSummarizer(router=router)
    meeting_pipeline = None
    if settings.craig_api_key and settings.speechmatics_api_key and obsidian:
        craig_client = CraigClient(api_key=settings.craig_api_key, base_url=settings.craig_api_base)
        recorder = CraigRecorder(client=craig_client)
        transcriber = SpeechmaticsTranscriber(api_key=settings.speechmatics_api_key)
        meeting_pipeline = MeetingPipeline(
            recorder=recorder,
            transcriber=transcriber,
            summarizer=summarizer,
            obsidian=obsidian,
            plane=plane,
        )
        logger.info("Meeting pipeline wired: Craig → Speechmatics → Obsidian → Plane")

    # Status summary
    print("sync-sme starting (discli serve mode)")
    features = []
    if meeting_pipeline:
        features.append("Meeting pipeline: ACTIVE")
    else:
        features.append("Meeting pipeline: DISABLED")
    features.append(f"Gap detection: ACTIVE ({settings.gap_detection_hours}h window)")
    features.append(f"Daily briefing: {settings.briefing_cron_hour:02d}:{settings.briefing_cron_minute:02d} MYT")
    if obsidian:
        features.append(f"Obsidian vault: {settings.obsidian_vault_path}")
    else:
        features.append("Obsidian: DISABLED")
    for f in features:
        print(f"  {f}")

    # Daily briefing scheduler (background thread)
    def _run_daily_briefing() -> None:
        """Generate and post the daily briefing."""
        if not obsidian:
            return
        candidates = gap_detector.detect()
        gaps_section = gap_detector.format_briefing_section(candidates)
        pending_tasks = "Plane integration pending — set PLANE_API_TOKEN to enable."
        upcoming_deadlines = "No deadline data available yet."
        try:
            briefing, path = briefing_generator.generate_and_write(
                pending_tasks=pending_tasks,
                upcoming_deadlines=upcoming_deadlines,
                gaps_detected=gaps_section,
                obsidian=obsidian,
            )
            logger.info("Daily briefing written to %s", path)
        except Exception:
            logger.exception("Failed to generate daily briefing")

    def _briefing_loop() -> None:
        """Background loop that runs the daily briefing."""
        import time
        while True:
            time.sleep(24 * 60 * 60)  # 24 hours
            _run_daily_briefing()

    briefing_thread = threading.Thread(target=_briefing_loop, daemon=True)
    briefing_thread.start()

    # --- discli serve mode event loop ---
    logger.info("Starting discli serve mode...")
    proc = subprocess.Popen(
        ["discli", "--json", "serve"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    try:
        for line in proc.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                logger.warning("Invalid JSON from discli: %s", line[:100])
                continue

            event_type = event.get("event")

            if event_type == "ready":
                bot_name = event.get("bot_name", "unknown")
                logger.info("Bot connected as %s", bot_name)
                continue

            if event_type == "message":
                # Skip bot's own messages
                if event.get("is_bot"):
                    continue

                # Extract fields from discli event
                channel_name = event.get("channel_name", "")
                message_id = str(event.get("message_id", ""))
                content = event.get("content", "")
                author_name = event.get("author", "")
                is_mention = event.get("mentions_bot", False)

                # Build a lightweight message-like object for the handler
                msg = _DiscliMessage(
                    id=message_id,
                    content=content,
                    channel_name=channel_name,
                    author_name=author_name,
                    is_bot=False,
                )

                result = on_message(msg)
                logger.info("Message %s → %s", message_id, result)

    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        proc.terminate()
        proc.wait()


class _DiscliMessage:
    """Lightweight message adapter for discli events."""

    __slots__ = ("id", "content", "_channel_name", "_author_name", "_is_bot")

    def __init__(self, id: str, content: str, channel_name: str, author_name: str, is_bot: bool) -> None:
        self.id = id
        self.content = content
        self._channel_name = channel_name
        self._author_name = author_name
        self._is_bot = is_bot

    @property
    def channel(self) -> _DiscliChannel:
        return _DiscliChannel(self._channel_name)

    @property
    def author(self) -> _DiscliAuthor:
        return _DiscliAuthor(self._author_name, self._is_bot)


class _DiscliChannel:
    __slots__ = ("name",)
    def __init__(self, name: str) -> None:
        self.name = name


class _DiscliAuthor:
    __slots__ = ("name", "display_name", "bot")
    def __init__(self, name: str, is_bot: bool) -> None:
        self.name = name
        self.display_name = name
        self.bot = is_bot


if __name__ == "__main__":  # pragma: no cover
    run()
