"""Tests for GapDetector — overdue candidate detection and alert formatting."""

from datetime import UTC, datetime, timedelta

from gaps.detector import GapDetector
from gaps.tracker import GapTracker


def _tracker_with_candidates(tmp_path, candidates):
    """Helper: create a GapTracker pre-populated with candidates."""
    tracker = GapTracker(db_path=str(tmp_path / "test.db"))
    for msg_id, content, hours_ago in candidates:
        tracker.remember(
            message_id=msg_id,
            content=content,
            channel="action-items",
            author="testuser",
            created_at=datetime.now(UTC) - timedelta(hours=hours_ago),
        )
    return tracker


def test_detect_returns_overdue_candidates(tmp_path):
    """detect() returns candidates older than detection_hours."""
    tracker = _tracker_with_candidates(tmp_path, [
        (1, "old message", 48),
        (2, "recent message", 1),
    ])
    detector = GapDetector(tracker=tracker, detection_hours=24)

    candidates = detector.detect()
    assert len(candidates) == 1
    assert candidates[0].message_id == 1


def test_detect_respects_detection_hours(tmp_path):
    """detect() uses the configured detection_hours threshold."""
    tracker = _tracker_with_candidates(tmp_path, [
        (1, "12 hours old", 12),
        (2, "36 hours old", 36),
    ])
    detector = GapDetector(tracker=tracker, detection_hours=24)

    candidates = detector.detect()
    assert len(candidates) == 1
    assert candidates[0].message_id == 2


def test_format_alert_returns_none_when_empty(tmp_path):
    """format_alert() returns None when no candidates exist."""
    tracker = GapTracker(db_path=str(tmp_path / "test.db"))
    detector = GapDetector(tracker=tracker)

    assert detector.format_alert([]) is None


def test_format_alert_includes_candidate_info(tmp_path):
    """format_alert() includes author and content snippet."""
    tracker = GapTracker(db_path=str(tmp_path / "test.db"))
    detector = GapDetector(tracker=tracker)

    candidates = [
        type("C", (), {"content": "we should fix the login page", "author": "alice"})(),
    ]
    alert = detector.format_alert(candidates)

    assert "⚠️" in alert
    assert "alice" in alert
    assert "fix the login page" in alert
    assert "1 message(s)" in alert


def test_format_alert_caps_at_5_entries(tmp_path):
    """format_alert() shows at most 5 candidates to avoid Discord message limits."""
    tracker = GapTracker(db_path=str(tmp_path / "test.db"))
    detector = GapDetector(tracker=tracker)

    candidates = [
        type("C", (), {"content": f"task {i}", "author": f"user{i}"})()
        for i in range(10)
    ]
    alert = detector.format_alert(candidates)

    assert "10 message(s)" in alert
    assert "... and 5 more" in alert


def test_format_alert_truncates_long_content(tmp_path):
    """format_alert() truncates content longer than 100 characters."""
    tracker = GapTracker(db_path=str(tmp_path / "test.db"))
    detector = GapDetector(tracker=tracker)

    long_content = "A" * 200
    candidates = [
        type("C", (), {"content": long_content, "author": "bob"})(),
    ]
    alert = detector.format_alert(candidates)

    assert "..." in alert
    assert "A" * 200 not in alert


def test_format_briefing_section_with_candidates(tmp_path):
    """format_briefing_section() formats candidates for the daily briefing."""
    tracker = GapTracker(db_path=str(tmp_path / "test.db"))
    detector = GapDetector(tracker=tracker)

    candidates = [
        type("C", (), {"content": "deploy the new feature", "author": "alice"})(),
        type("C", (), {"content": "review PRs", "author": "bob"})(),
    ]
    section = detector.format_briefing_section(candidates)

    assert "2 unlogged task candidate(s)" in section
    assert "deploy the new feature" in section
    assert "review PRs" in section


def test_format_briefing_section_empty(tmp_path):
    """format_briefing_section() returns a no-gaps message when empty."""
    tracker = GapTracker(db_path=str(tmp_path / "test.db"))
    detector = GapDetector(tracker=tracker)

    section = detector.format_briefing_section([])

    assert "No unlogged task candidates" in section


def test_format_briefing_section_caps_at_10(tmp_path):
    """format_briefing_section() shows at most 10 candidates."""
    tracker = GapTracker(db_path=str(tmp_path / "test.db"))
    detector = GapDetector(tracker=tracker)

    candidates = [
        type("C", (), {"content": f"task {i}", "author": f"user{i}"})()
        for i in range(15)
    ]
    section = detector.format_briefing_section(candidates)

    assert "15 unlogged task candidate(s)" in section
    # Only 10 should be listed
    assert "task 14" not in section
