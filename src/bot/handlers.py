"""Message event handlers for Discord task ingestion."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass

from llm.parser import ParsedTask, TaskParser

DEFAULT_TRIGGER_KEYWORDS = (
    "remind me to",
    "assign to",
    "deadline",
    "need to",
    "todo",
    "follow up",
)

# Type for the reaction callback: (channel_id, message_id, emoji) -> None
AddReactionFn = Callable[[str, str, str], None]


@dataclass(slots=True)
class TaskCreated:
    identifier: str


class MessageStateStore:
    def is_processed(self, message_id: int) -> bool:
        raise NotImplementedError

    def mark_processed(self, message_id: int) -> None:
        raise NotImplementedError


class PlaneIssueCreator:
    def create_issue(self, task: ParsedTask) -> TaskCreated:
        raise NotImplementedError


def is_actionable_message(content: str, trigger_keywords: Sequence[str] = DEFAULT_TRIGGER_KEYWORDS) -> bool:
    lowered = content.lower()
    return any(keyword in lowered for keyword in trigger_keywords)


def _noop_reaction(channel_id: str, message_id: str, emoji: str) -> None:
    """Default no-op reaction callback for testing."""


def build_message_handler(
    task_parser: TaskParser,
    plane_client: PlaneIssueCreator,
    state_store: MessageStateStore,
    action_items_channel: str = "action-items",
    trigger_keywords: Sequence[str] = DEFAULT_TRIGGER_KEYWORDS,
    gap_tracker: object | None = None,
    add_reaction: AddReactionFn | None = None,
) -> Callable[[object], str]:
    """Build the on_message handler for Discord.

    Args:
        task_parser: LLM-backed task parser.
        plane_client: Plane issue creator.
        state_store: SQLite-backed dedup store.
        action_items_channel: Channel name to monitor.
        trigger_keywords: Phrases that indicate a message is actionable.
        gap_tracker: Optional GapTracker for tracking non-actionable messages
            as potential task candidates (Day 3 gap detection).
        add_reaction: Callback ``(channel_id, message_id, emoji) -> None``
            for adding reactions. Falls back to a no-op if not provided.
    """
    react = add_reaction or _noop_reaction

    def on_message(message: object) -> str:
        channel = getattr(getattr(message, "channel", None), "name", "")
        if channel != action_items_channel:
            return "ignored-channel"

        author = getattr(message, "author", None)
        if getattr(author, "bot", False):
            return "ignored-bot"

        message_id = str(getattr(message, "id"))
        if state_store.is_processed(message_id):
            return "ignored-duplicate"

        content = getattr(message, "content", "")
        if not is_actionable_message(content, trigger_keywords):
            # Track non-actionable messages as gap candidates
            if gap_tracker is not None:
                author_name = getattr(author, "name", "") or getattr(author, "display_name", "")
                gap_tracker.remember(
                    message_id=message_id,
                    content=content,
                    channel=channel,
                    author=author_name,
                )
            return "ignored-non-actionable"

        task = task_parser.parse_message(content)
        if not task:
            react(channel, message_id, "❌")
            return "parse-failed"

        plane_client.create_issue(task)
        state_store.mark_processed(message_id)
        # If this message was previously a gap candidate, resolve it
        if gap_tracker is not None:
            gap_tracker.resolve(message_id)
        react(channel, message_id, "✅")
        return "created"

    return on_message
