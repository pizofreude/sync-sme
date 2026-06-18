"""End-to-end meeting processing pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from integrations.obsidian import ObsidianWriter
from integrations.plane import PlaneCLI
from llm.parser import ParsedTask
from llm.summarizer import MeetingSummarizer
from meeting.recorder import CraigRecorder
from meeting.transcriber import WhisperTranscriber


@dataclass(slots=True)
class MeetingPipeline:
    recorder: CraigRecorder
    transcriber: WhisperTranscriber
    summarizer: MeetingSummarizer
    obsidian: ObsidianWriter
    plane: PlaneCLI

    def process_recording(self, recording_id: str, audio_path: Path, notes_path: str) -> str:
        audio_path.write_bytes(self.recorder.fetch_audio(recording_id))
        transcript = self.transcriber.transcribe(audio_path)
        minutes = self.summarizer.summarize(transcript)
        self.obsidian.write_markdown(notes_path, minutes)
        return minutes

    def create_action_item(self, task: ParsedTask):
        return self.plane.create_issue(task)
