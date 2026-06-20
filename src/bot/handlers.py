"""Message event handlers for Discord task ingestion."""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Sequence
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


def build_message_handler(
    task_parser: TaskParser,
    plane_client: PlaneIssueCreator,
    state_store: MessageStateStore,
    action_items_channel: str = "action-items",
    trigger_keywords: Sequence[str] = DEFAULT_TRIGGER_KEYWORDS,
    gap_tracker: object | None = None,
) -> Callable[[object], Awaitable[str]]:
    """Build the on_message handler for Discord.

    Args:
        task_parser: LLM-backed task parser.
        plane_client: Plane issue creator.
        state_store: SQLite-backed dedup store.
        action_items_channel: Channel name to monitor.
        trigger_keywords: Phrases that indicate a message is actionable.
        gap_tracker: Optional GapTracker for tracking non-actionable messages
            as potential task candidates (Day 3 gap detection).
    """
    async def on_message(message: object) -> str:
        channel = getattr(getattr(message, "channel", None), "name", "")
        if channel != action_items_channel:
            return "ignored-channel"

        author = getattr(message, "author", None)
        if getattr(author, "bot", False):
            return "ignored-bot"

        message_id = getattr(message, "id")
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
            await message.add_reaction("❌")
            return "parse-failed"

        plane_client.create_issue(task)
        state_store.mark_processed(message_id)
        # If this message was previously a gap candidate, resolve it
        if gap_tracker is not None:
            gap_tracker.resolve(message_id)
        await message.add_reaction("✅")
        return "created"

    return on_message
