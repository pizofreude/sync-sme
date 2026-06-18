import asyncio
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
        self.processed = set(processed or [])

    def is_processed(self, message_id: int) -> bool:
        return message_id in self.processed

    def mark_processed(self, message_id: int) -> None:
        self.processed.add(message_id)


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
    reactions: list[str] = field(default_factory=list)

    async def add_reaction(self, emoji: str):
        self.reactions.append(emoji)


def test_handler_creates_issue_for_actionable_messages():
    parser = FakeParser(ParsedTask(title="Ship demo"))
    plane = FakePlane()
    store = FakeStateStore()
    handler = build_message_handler(parser, plane, store)
    message = FakeMessage(id=1, content="todo: ship the demo")

    result = asyncio.run(handler(message))

    assert result == "created"
    assert plane.created == [ParsedTask(title="Ship demo")]
    assert store.processed == {1}
    assert message.reactions == ["✅"]


def test_handler_ignores_bot_authored_messages():
    parser = FakeParser(ParsedTask(title="Ship demo"))
    plane = FakePlane()
    store = FakeStateStore()
    handler = build_message_handler(parser, plane, store)
    message = FakeMessage(
        id=2,
        content="todo: ship the demo",
        author=FakeAuthor(bot=True),
    )

    result = asyncio.run(handler(message))

    assert result == "ignored-bot"
    assert plane.created == []
    assert store.processed == set()
    assert message.reactions == []


def test_handler_reacts_with_failure_when_parser_returns_none():
    parser = FakeParser(None)
    plane = FakePlane()
    store = FakeStateStore()
    handler = build_message_handler(parser, plane, store)
    message = FakeMessage(id=2, content="need to clarify release")

    result = asyncio.run(handler(message))

    assert result == "parse-failed"
    assert plane.created == []
    assert message.reactions == ["❌"]


def test_handler_ignores_non_actionable_duplicate_and_wrong_channel_messages():
    parser = FakeParser(ParsedTask(title="ignored"))
    plane = FakePlane()
    store = FakeStateStore(processed={5})
    handler = build_message_handler(parser, plane, store)

    duplicate = FakeMessage(id=5, content="todo: already handled")
    quiet = FakeMessage(id=6, content="hello team")
    wrong_channel = FakeMessage(id=7, content="todo: elsewhere", channel=FakeChannel(name="general"))

    assert asyncio.run(handler(duplicate)) == "ignored-duplicate"
    assert asyncio.run(handler(quiet)) == "ignored-non-actionable"
    assert asyncio.run(handler(wrong_channel)) == "ignored-channel"
    assert plane.created == []

    # Ignored messages must not receive reactions
    assert duplicate.reactions == []
    assert quiet.reactions == []
    assert wrong_channel.reactions == []
