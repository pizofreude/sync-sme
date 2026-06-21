from dataclasses import dataclass, field

from bot.handlers import build_message_handler
from llm.parser import ParsedTask


class FakeParser:
    def __init__(self, parsed_task):
        self.parsed_task = parsed_task
        self.messages = []

    def parse_message(self, message: str):
        self.messages.append(message)
        return self.parsed_task


class FakePlane:
    def __init__(self):
        self.created = []

    def create_issue(self, task: ParsedTask):
        self.created.append(task)


class FakeStateStore:
    def __init__(self, processed=None):
        self.processed = set(str(p) for p in (processed or []))

    def is_processed(self, message_id) -> bool:
        return str(message_id) in self.processed

    def mark_processed(self, message_id) -> None:
        self.processed.add(str(message_id))


@dataclass
class FakeAuthor:
    bot: bool = False


@dataclass
class FakeChannel:
    name: str = "action-items"


@dataclass
class FakeMessage:
    id: int
    content: str
    author: FakeAuthor = field(default_factory=FakeAuthor)
    channel: FakeChannel = field(default_factory=FakeChannel)


def _make_reaction_tracker():
    """Return an add_reaction callback and the list of recorded reactions."""
    reactions = []

    def add_reaction(channel_id: str, message_id: str, emoji: str):
        reactions.append((channel_id, message_id, emoji))

    return add_reaction, reactions


def test_handler_creates_issue_for_actionable_messages():
    parser = FakeParser(ParsedTask(title="Ship demo"))
    plane = FakePlane()
    store = FakeStateStore()
    react, reactions = _make_reaction_tracker()
    handler = build_message_handler(parser, plane, store, add_reaction=react)
    message = FakeMessage(id=1, content="todo: ship the demo")

    result = handler(message)

    assert result == "created"
    assert plane.created == [ParsedTask(title="Ship demo")]
    assert store.processed == {"1"}
    assert reactions == [("action-items", "1", "✅")]


def test_handler_ignores_bot_authored_messages():
    parser = FakeParser(ParsedTask(title="Ship demo"))
    plane = FakePlane()
    store = FakeStateStore()
    react, reactions = _make_reaction_tracker()
    handler = build_message_handler(parser, plane, store, add_reaction=react)
    message = FakeMessage(
        id=2,
        content="todo: ship the demo",
        author=FakeAuthor(bot=True),
    )

    result = handler(message)

    assert result == "ignored-bot"
    assert plane.created == []
    assert store.processed == set()
    assert reactions == []


def test_handler_reacts_with_failure_when_parser_returns_none():
    parser = FakeParser(None)
    plane = FakePlane()
    store = FakeStateStore()
    react, reactions = _make_reaction_tracker()
    handler = build_message_handler(parser, plane, store, add_reaction=react)
    message = FakeMessage(id=2, content="need to clarify release")

    result = handler(message)

    assert result == "parse-failed"
    assert plane.created == []
    assert reactions == [("action-items", "2", "❌")]


def test_handler_ignores_non_actionable_duplicate_and_wrong_channel_messages():
    parser = FakeParser(ParsedTask(title="ignored"))
    plane = FakePlane()
    store = FakeStateStore(processed={5})
    react, reactions = _make_reaction_tracker()
    handler = build_message_handler(parser, plane, store, add_reaction=react)

    duplicate = FakeMessage(id=5, content="todo: already handled")
    quiet = FakeMessage(id=6, content="hello team")
    wrong_channel = FakeMessage(id=7, content="todo: elsewhere", channel=FakeChannel(name="general"))

    assert handler(duplicate) == "ignored-duplicate"
    assert handler(quiet) == "ignored-non-actionable"
    assert handler(wrong_channel) == "ignored-channel"
    assert plane.created == []

    # Ignored messages must not receive reactions
    assert reactions == []


def test_handler_uses_custom_action_items_channel():
    parser = FakeParser(ParsedTask(title="Custom channel task"))
    plane = FakePlane()
    store = FakeStateStore()
    react, reactions = _make_reaction_tracker()
    handler = build_message_handler(parser, plane, store, action_items_channel="team-tasks", add_reaction=react)
    message = FakeMessage(id=10, content="todo: ship feature", channel=FakeChannel(name="team-tasks"))

    result = handler(message)

    assert result == "created"
    assert plane.created == [ParsedTask(title="Custom channel task")]
    assert store.processed == {"10"}
    assert reactions == [("team-tasks", "10", "✅")]


def test_handler_ignores_default_channel_when_custom_configured():
    parser = FakeParser(ParsedTask(title="Should not be created"))
    plane = FakePlane()
    store = FakeStateStore()
    react, reactions = _make_reaction_tracker()
    handler = build_message_handler(parser, plane, store, action_items_channel="team-tasks", add_reaction=react)
    message = FakeMessage(id=11, content="todo: from default channel", channel=FakeChannel(name="action-items"))

    result = handler(message)

    assert result == "ignored-channel"
    assert plane.created == []
    assert store.processed == set()
    assert reactions == []


def test_handler_uses_custom_trigger_keywords():
    parser = FakeParser(ParsedTask(title="Triggered task"))
    plane = FakePlane()
    store = FakeStateStore()
    react, reactions = _make_reaction_tracker()
    handler = build_message_handler(parser, plane, store, trigger_keywords=["remind me to"], add_reaction=react)
    message = FakeMessage(id=12, content="remind me to deploy the app")

    result = handler(message)

    assert result == "created"
    assert plane.created == [ParsedTask(title="Triggered task")]
    assert reactions == [("action-items", "12", "✅")]


def test_handler_ignores_messages_without_custom_trigger_keywords():
    parser = FakeParser(ParsedTask(title="Should not be created"))
    plane = FakePlane()
    store = FakeStateStore()
    react, reactions = _make_reaction_tracker()
    handler = build_message_handler(parser, plane, store, trigger_keywords=["remind me to"], add_reaction=react)
    message = FakeMessage(id=13, content="todo: ship the demo")

    result = handler(message)

    assert result == "ignored-non-actionable"
    assert plane.created == []
    assert store.processed == set()
    assert reactions == []
