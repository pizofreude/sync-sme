"""Tests for GapTracker — SQLite-backed candidate task tracking."""

from datetime import UTC, datetime, timedelta

from gaps.tracker import GapTracker


def test_remember_stores_candidate(tmp_path):
    """remember() stores a message as a gap candidate."""
    tracker = GapTracker(db_path=str(tmp_path / "test.db"))
    tracker.remember(message_id=1, content="might be a task", channel="action-items", author="alice")

    candidates = tracker.recent_candidates()
    assert len(candidates) == 1
    assert candidates[0].message_id == 1
    assert candidates[0].content == "might be a task"
    assert candidates[0].channel == "action-items"
    assert candidates[0].author == "alice"


def test_remember_ignores_duplicate(tmp_path):
    """remember() does not overwrite existing candidates."""
    tracker = GapTracker(db_path=str(tmp_path / "test.db"))
    tracker.remember(message_id=1, content="first version")
    tracker.remember(message_id=1, content="second version")

    candidates = tracker.recent_candidates()
    assert len(candidates) == 1
    assert candidates[0].content == "first version"


def test_resolve_marks_candidate(tmp_path):
    """resolve() marks a candidate as resolved."""
    tracker = GapTracker(db_path=str(tmp_path / "test.db"))
    tracker.remember(message_id=1, content="task")
    tracker.resolve(message_id=1)

    assert tracker.unresolved_count() == 0


def test_overdue_returns_old_unresolved(tmp_path):
    """overdue() returns only unresolved candidates older than the threshold."""
    tracker = GapTracker(db_path=str(tmp_path / "test.db"))

    old_time = datetime.now(UTC) - timedelta(hours=48)
    recent_time = datetime.now(UTC) - timedelta(hours=1)

    tracker.remember(message_id=1, content="old task", created_at=old_time)
    tracker.remember(message_id=2, content="recent task", created_at=recent_time)
    tracker.remember(message_id=3, content="resolved old task", created_at=old_time)
    tracker.resolve(message_id=3)

    overdue = tracker.overdue(timedelta(hours=24))
    assert len(overdue) == 1
    assert overdue[0].message_id == 1


def test_overdue_returns_empty_when_none_qualify(tmp_path):
    """overdue() returns empty list when no candidates are old enough."""
    tracker = GapTracker(db_path=str(tmp_path / "test.db"))
    tracker.remember(message_id=1, content="recent", created_at=datetime.now(UTC))

    assert tracker.overdue(timedelta(hours=24)) == []


def test_unresolved_count(tmp_path):
    """unresolved_count() returns the correct count."""
    tracker = GapTracker(db_path=str(tmp_path / "test.db"))
    assert tracker.unresolved_count() == 0

    tracker.remember(message_id=1, content="a")
    tracker.remember(message_id=2, content="b")
    assert tracker.unresolved_count() == 2

    tracker.resolve(message_id=1)
    assert tracker.unresolved_count() == 1


def test_recent_candidates_returns_in_order(tmp_path):
    """recent_candidates() returns candidates ordered by created_at DESC."""
    tracker = GapTracker(db_path=str(tmp_path / "test.db"))
    tracker.remember(message_id=1, content="first", created_at=datetime(2026, 6, 20, tzinfo=UTC))
    tracker.remember(message_id=2, content="second", created_at=datetime(2026, 6, 21, tzinfo=UTC))
    tracker.remember(message_id=3, content="third", created_at=datetime(2026, 6, 22, tzinfo=UTC))

    recent = tracker.recent_candidates(limit=2)
    assert len(recent) == 2
    assert recent[0].message_id == 3  # most recent first
    assert recent[1].message_id == 2


def test_recent_candidates_respects_limit(tmp_path):
    """recent_candidates() respects the limit parameter."""
    tracker = GapTracker(db_path=str(tmp_path / "test.db"))
    for i in range(20):
        tracker.remember(message_id=i, content=f"msg {i}")

    assert len(tracker.recent_candidates(limit=5)) == 5
    assert len(tracker.recent_candidates(limit=100)) == 20


def test_persistence_across_instances(tmp_path):
    """Data persists across GapTracker instances (same DB file)."""
    db_path = str(tmp_path / "test.db")
    tracker1 = GapTracker(db_path=db_path)
    tracker1.remember(message_id=42, content="persistent")

    tracker2 = GapTracker(db_path=db_path)
    candidates = tracker2.recent_candidates()
    assert len(candidates) == 1
    assert candidates[0].message_id == 42
