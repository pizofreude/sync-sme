"""Discord client bootstrap helpers."""

from __future__ import annotations

import logging
import os
import shutil
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

from bot.handlers import build_message_handler
from db.models import SQLiteStateStore
from integrations.plane import PlaneCLI
from llm.parser import TaskParser
from llm.router import NineRouterClient
from llm.summarizer import MeetingSummarizer
from integrations.obsidian import ObsidianWriter
from meeting.pipeline import MeetingPipeline
from meeting.recorder import CraigRecorder
from meeting.transcriber import WhisperTranscriber
from integrations.craig import CraigClient

logger = logging.getLogger(__name__)

try:
    import discord
except ImportError:  # pragma: no cover - exercised only in runtime environments without discord.py
    discord = None


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
    whisper_model: str = "base"
    plane_api_token: str = ""
    plane_project_id: str = ""

    @classmethod
    def from_env(cls) -> "BotSettings":
        load_dotenv()
        raw_assignee_map = os.getenv("PLANE_ASSIGNEE_MAP", "")
        assignee_map = {}
        for item in filter(None, (entry.strip() for entry in raw_assignee_map.split(","))):
            if ":" not in item:
                continue  # skip malformed entries instead of crashing
            discord_id, plane_member = item.split(":", 1)
            assignee_map[discord_id.strip()] = plane_member.strip()

        vault_path = os.getenv("OBSIDIAN_VAULT_PATH", "")
        # Expand ~ and $HOME to user home directory
        if vault_path.startswith("~"):
            vault_path = str(Path(vault_path).expanduser())
        elif "$HOME" in vault_path:
            vault_path = vault_path.replace("$HOME", str(Path.home()))

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
            whisper_model=os.getenv("WHISPER_MODEL", "base"),
            plane_api_token=os.getenv("PLANE_API_TOKEN", ""),
            plane_project_id=os.getenv("PLANE_PROJECT_ID", ""),
        )


def _detect_plane_cli() -> bool:
    """Check if the ``plane`` CLI binary is on PATH."""
    return shutil.which("plane") is not None


def create_client(settings: BotSettings):
    if discord is None:  # pragma: no cover - depends on optional runtime dependency
        raise RuntimeError("discord.py must be installed to create the Discord client")

    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)

    router = NineRouterClient(api_key=settings.ninerouter_api_key, model=settings.llm_model, endpoint=settings.ninerouter_endpoint)
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
    on_message = build_message_handler(
        task_parser=parser,
        plane_client=plane,
        state_store=state_store,
        action_items_channel=settings.action_items_channel,
    )

    # Day 2: Meeting pipeline (wired but triggered only when Craig recordings arrive)
    summarizer = MeetingSummarizer(router=router)
    obsidian = ObsidianWriter(vault_path=Path(settings.obsidian_vault_path)) if settings.obsidian_vault_path else None
    meeting_pipeline = None
    if settings.craig_api_key and obsidian:
        craig_client = CraigClient(api_key=settings.craig_api_key, base_url=settings.craig_api_base)
        recorder = CraigRecorder(client=craig_client)
        transcriber = WhisperTranscriber(model_name=settings.whisper_model)
        meeting_pipeline = MeetingPipeline(
            recorder=recorder,
            transcriber=transcriber,
            summarizer=summarizer,
            obsidian=obsidian,
            plane=plane,
        )
        logger.info("Meeting pipeline wired: Craig → Whisper → Obsidian → Plane")
    else:
        if not settings.craig_api_key:
            logger.info("CRAIG_API_KEY not set — meeting pipeline disabled")
        if not obsidian:
            logger.info("OBSIDIAN_VAULT_PATH not set — meeting pipeline disabled")

    @client.event
    async def on_ready():
        print(f"Logged in as {client.user}")
        if meeting_pipeline:
            print("Meeting pipeline: ACTIVE (Craig → Whisper → Obsidian → Plane)")
        else:
            print("Meeting pipeline: DISABLED (set CRAIG_API_KEY + OBSIDIAN_VAULT_PATH to enable)")

    @client.event
    async def on_message(message):
        await on_message(message)

    return client


def run() -> None:
    logging.basicConfig(level=logging.INFO)
    settings = BotSettings.from_env()
    if not settings.discord_bot_token:
        raise RuntimeError("DISCORD_BOT_TOKEN is required")
    client = create_client(settings)
    client.run(settings.discord_bot_token)


if __name__ == "__main__":  # pragma: no cover
    run()
