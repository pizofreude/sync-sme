"""Detect overdue candidate tasks."""

from __future__ import annotations

from datetime import timedelta

from gaps.tracker import CandidateTask, GapTracker


class GapDetector:
    def __init__(self, tracker: GapTracker, detection_hours: int = 24):
        self.tracker = tracker
        self.detection_hours = detection_hours

    def detect(self) -> list[CandidateTask]:
        return self.tracker.overdue(timedelta(hours=self.detection_hours))
