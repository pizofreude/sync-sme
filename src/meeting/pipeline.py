"""End-to-end meeting processing pipeline."""

from __future__ import annotations

import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path

from integrations.obsidian import ObsidianWriter
from integrations.plane import CreatedIssue, PlaneCLI
from llm.parser import ParsedTask, TaskParser
from llm.summarizer import MeetingSummarizer
from meeting.recorder import CraigRecorder
from meeting.transcriber import WhisperTranscriber

logger = logging.getLogger(__name__)

# Prompt for extracting action items from meeting minutes
ACTION_ITEM_PROMPT = """Extract action items from the following meeting minutes.
Return a JSON array of tasks. Each task has:
{"title": "short task title", "assignee": "name or null", "due_date": "YYYY-MM-DD or null", "details": "context or null"}
Return [] if no action items found. Return ONLY valid JSON, no markdown fences."""


@dataclass(slots=True)
class MeetingPipeline:
    recorder: CraigRecorder
    transcriber: WhisperTranscriber
    summarizer: MeetingSummarizer
    obsidian: ObsidianWriter
    plane: PlaneCLI

    def process_recording(self, recording_id: str, audio_path: Path, notes_path: str) -> str:
        """Full pipeline: fetch audio → transcribe → summarize → write to Obsidian.

        Args:
            recording_id: Craig recording ID.
            audio_path: Local path to save the downloaded audio.
            notes_path: Relative path in vault for the meeting notes.

        Returns:
            The generated meeting minutes markdown.
        """
        logger.info("Fetching recording %s", recording_id)
        audio_path.write_bytes(self.recorder.fetch_audio(recording_id))

        logger.info("Transcribing audio with Whisper")
        transcript = self.transcriber.transcribe(audio_path)

        logger.info("Summarizing transcript")
        minutes = self.summarizer.summarize(transcript)

        logger.info("Writing minutes to Obsidian vault: %s", notes_path)
        self.obsidian.write_markdown(notes_path, minutes)

        return minutes

    def extract_action_items(self, minutes: str, router) -> list[ParsedTask]:
        """Extract action items from meeting minutes using the LLM.

        Args:
            minutes: The meeting minutes markdown text.
            router: A Router-compatible object for LLM completions.

        Returns:
            List of parsed tasks extracted from the minutes.
        """
        raw_response = router.complete(
            system_prompt=ACTION_ITEM_PROMPT,
            user_prompt=minutes,
        )
        # Strip markdown code fences if LLM wraps the response
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw_response.strip(), flags=re.MULTILINE).strip()
        try:
            items = json.loads(cleaned)
        except json.JSONDecodeError:
            logger.warning("Failed to parse action items from LLM response: %s", raw_response[:200])
            return []

        tasks = []
        for item in items:
            title = str(item.get("title", "")).strip()
            if not title:
                continue
            tasks.append(ParsedTask(
                title=title,
                assignee=TaskParser._optional_text(item.get("assignee")),
                due_date=TaskParser._optional_text(item.get("due_date")),
                details=TaskParser._optional_text(item.get("details")),
            ))
        return tasks

    def create_action_items(self, tasks: list[ParsedTask]) -> list[CreatedIssue]:
        """Create Plane issues for extracted action items.

        Args:
            tasks: List of parsed tasks from meeting minutes.

        Returns:
            List of created issue references.
        """
        issues = []
        for task in tasks:
            try:
                issue = self.plane.create_issue(task)
                issues.append(issue)
                logger.info("Created issue: %s", issue.identifier)
            except Exception:
                logger.exception("Failed to create issue for task: %s", task.title)
        return issues

    def process_and_extract(
        self,
        recording_id: str,
        audio_path: Path,
        notes_path: str,
        router,
    ) -> tuple[str, list[CreatedIssue]]:
        """Full pipeline + action item extraction and issue creation.

        Combines process_recording, extract_action_items, and create_action_items.
        Returns (minutes, created_issues).
        """
        minutes = self.process_recording(recording_id, audio_path, notes_path)
        tasks = self.extract_action_items(minutes, router)
        issues = self.create_action_items(tasks)
        return minutes, issues
