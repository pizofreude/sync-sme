"""Edge case tests for message handling — Day 1 remaining items.

Covers: very long messages, messages with only images, edited messages.
"""

import asyncio
from dataclasses import dataclass, field

from bot.handlers import build_message_handler
from llm.parser import ParsedTask

from test_handlers import FakeParser, FakePlane, FakeStateStore, FakeAuthor, FakeChannel, FakeMessage


def test_handler_processes_very_long_message():
    """A message exceeding Discord's 2000-char limit should still be parsed if actionable."""
    long_content = "todo: " + "A" * 3000  # Simulates a very long task description
    parser = FakeParser(ParsedTask(title="Long task"))
    plane = FakePlane()
    store = FakeStateStore()
    handler = build_message_handler(parser, plane, store)
    message = FakeMessage(id=100, content=long_content)

    result = asyncio.run(handler(message))

    assert result == "created"
    assert len(parser.messages) == 1
    assert parser.messages[0] == long_content
    assert message.reactions == ["✅"]


def test_handler_processes_message_with_only_image_attachment():
    """A message with only an image (no text) should be ignored as non-actionable."""
    # Discord messages with only attachments have empty content
    parser = FakeParser(ParsedTask(title="Should not parse"))
    plane = FakePlane()
    store = FakeStateStore()
    handler = build_message_handler(parser, plane, store)
    message = FakeMessage(id=101, content="")

    result = asyncio.run(handler(message))

    assert result == "ignored-non-actionable"
    assert plane.created == []
    assert message.reactions == []


def test_handler_processes_image_with_actionable_caption():
    """A message with an image + actionable text caption should be processed."""
    parser = FakeParser(ParsedTask(title="Fix this bug", details="See screenshot"))
    plane = FakePlane()
    store = FakeStateStore()
    handler = build_message_handler(parser, plane, store)
    # In Discord, the caption is the message content; the image is an attachment
    message = FakeMessage(id=102, content="todo: fix this bug — see attached screenshot")

    result = asyncio.run(handler(message))

    assert result == "created"
    assert plane.created == [ParsedTask(title="Fix this bug", details="See screenshot")]
    assert message.reactions == ["✅"]


def test_handler_processes_edited_message_only_once():
    """An edited message should only be processed once (dedup via message ID)."""
    parser = FakeParser(ParsedTask(title="Updated task"))
    plane = FakePlane()
    store = FakeStateStore()
    handler = build_message_handler(parser, plane, store)

    # First delivery of the message
    message_v1 = FakeMessage(id=103, content="todo: deploy the app")
    result1 = asyncio.run(handler(message_v1))

    # Edited message with same ID (Discord reuses the same message ID on edits)
    message_v2 = FakeMessage(id=103, content="todo: deploy the app to staging")
    result2 = asyncio.run(handler(message_v2))

    assert result1 == "created"
    assert result2 == "ignored-duplicate"
    assert len(plane.created) == 1  # Only one issue created
    assert store.processed == {103}


def test_handler_processes_unicode_message():
    """Messages with unicode characters should be handled correctly."""
    parser = FakeParser(ParsedTask(title="完成部署"))
    plane = FakePlane()
    store = FakeStateStore()
    handler = build_message_handler(parser, plane, store)
    message = FakeMessage(id=104, content="todo: 完成部署到生产环境")

    result = asyncio.run(handler(message))

    assert result == "created"
    assert plane.created == [ParsedTask(title="完成部署")]
    assert message.reactions == ["✅"]


def test_handler_processes_message_with_mentions():
    """Messages with Discord mentions should pass through to the parser."""
    parser = FakeParser(ParsedTask(title="Review PR", assignee="<@12345>"))
    plane = FakePlane()
    store = FakeStateStore()
    handler = build_message_handler(parser, plane, store)
    message = FakeMessage(id=105, content="assign to <@12345>: review the PR")

    result = asyncio.run(handler(message))

    assert result == "created"
    assert parser.messages[0] == "assign to <@12345>: review the PR"
    assert message.reactions == ["✅"]


def test_handler_multiple_trigger_keywords_in_one_message():
    """A message matching multiple trigger keywords should still be processed once."""
    parser = FakeParser(ParsedTask(title="Follow up on deadline"))
    plane = FakePlane()
    store = FakeStateStore()
    handler = build_message_handler(parser, plane, store)
    message = FakeMessage(id=106, content="need to follow up on the deadline for todo list review")

    result = asyncio.run(handler(message))

    assert result == "created"
    assert len(plane.created) == 1
    assert message.reactions == ["✅"]
