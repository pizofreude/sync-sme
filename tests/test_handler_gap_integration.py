"""Integration tests for message handler + gap tracker interaction."""

from dataclasses import dataclass, field

from bot.handlers import build_message_handler
from llm.parser import ParsedTask

from test_handlers import FakeParser, FakePlane, FakeStateStore, FakeAuthor, FakeChannel, FakeMessage


class FakeGapTracker:
    """In-memory gap tracker for testing handler integration."""

    def __init__(self):
        self.remembered = []
        self.resolved = []

    def remember(self, message_id, content, channel="", author=""):
        self.remembered.append({
            "message_id": str(message_id),
            "content": content,
            "channel": channel,
            "author": author,
        })

    def resolve(self, message_id):
        self.resolved.append(str(message_id))


def _noop_reaction(channel_id: str, message_id: str, emoji: str) -> None:
    pass


def test_non_actionable_message_tracked_as_gap_candidate():
    """Non-actionable messages in the target channel are tracked as gap candidates."""
    parser = FakeParser(ParsedTask(title="unused"))
    plane = FakePlane()
    store = FakeStateStore()
    gap_tracker = FakeGapTracker()
    handler = build_message_handler(parser, plane, store, gap_tracker=gap_tracker, add_reaction=_noop_reaction)

    message = FakeMessage(id=50, content="just chatting about the weather")
    result = handler(message)

    assert result == "ignored-non-actionable"
    assert len(gap_tracker.remembered) == 1
    assert gap_tracker.remembered[0]["message_id"] == "50"
    assert gap_tracker.remembered[0]["content"] == "just chatting about the weather"


def test_actionable_message_not_tracked_as_gap():
    """Actionable messages are NOT tracked as gap candidates."""
    parser = FakeParser(ParsedTask(title="Deploy"))
    plane = FakePlane()
    store = FakeStateStore()
    gap_tracker = FakeGapTracker()
    handler = build_message_handler(parser, plane, store, gap_tracker=gap_tracker, add_reaction=_noop_reaction)

    message = FakeMessage(id=51, content="todo: deploy the app")
    result = handler(message)

    assert result == "created"
    assert len(gap_tracker.remembered) == 0


def test_successful_creation_resolves_gap_candidate():
    """When a task is created, the message ID is resolved in the gap tracker."""
    parser = FakeParser(ParsedTask(title="Deploy"))
    plane = FakePlane()
    store = FakeStateStore()
    gap_tracker = FakeGapTracker()
    handler = build_message_handler(parser, plane, store, gap_tracker=gap_tracker, add_reaction=_noop_reaction)

    message = FakeMessage(id=52, content="todo: deploy the app")
    handler(message)

    assert "52" in gap_tracker.resolved


def test_wrong_channel_messages_not_tracked():
    """Messages from other channels are ignored without gap tracking."""
    parser = FakeParser(None)
    plane = FakePlane()
    store = FakeStateStore()
    gap_tracker = FakeGapTracker()
    handler = build_message_handler(parser, plane, store, gap_tracker=gap_tracker, add_reaction=_noop_reaction)

    message = FakeMessage(id=53, content="random message", channel=FakeChannel(name="general"))
    result = handler(message)

    assert result == "ignored-channel"
    assert len(gap_tracker.remembered) == 0


def test_bot_messages_not_tracked():
    """Bot-authored messages are ignored without gap tracking."""
    parser = FakeParser(None)
    plane = FakePlane()
    store = FakeStateStore()
    gap_tracker = FakeGapTracker()
    handler = build_message_handler(parser, plane, store, gap_tracker=gap_tracker, add_reaction=_noop_reaction)

    message = FakeMessage(id=54, content="bot says hi", author=FakeAuthor(bot=True))
    result = handler(message)

    assert result == "ignored-bot"
    assert len(gap_tracker.remembered) == 0


def test_handler_works_without_gap_tracker():
    """Handler works normally when gap_tracker is None (backward compat)."""
    parser = FakeParser(ParsedTask(title="Task"))
    plane = FakePlane()
    store = FakeStateStore()
    handler = build_message_handler(parser, plane, store, gap_tracker=None, add_reaction=_noop_reaction)

    message = FakeMessage(id=55, content="just chatting")
    result = handler(message)

    assert result == "ignored-non-actionable"


def test_gap_tracker_receives_channel_and_author():
    """Gap tracker receives the channel name and author info."""
    parser = FakeParser(None)
    plane = FakePlane()
    store = FakeStateStore()
    gap_tracker = FakeGapTracker()
    handler = build_message_handler(parser, plane, store, gap_tracker=gap_tracker, add_reaction=_noop_reaction)

    message = FakeMessage(
        id=56,
        content="maybe this is a task?",
        channel=FakeChannel(name="action-items"),
        author=FakeAuthor(bot=False),
    )
    handler(message)

    assert len(gap_tracker.remembered) == 1
    assert gap_tracker.remembered[0]["channel"] == "action-items"
