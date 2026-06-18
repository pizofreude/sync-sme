# sync-sme

Sync-SME is a lightweight Python agent that turns Discord action items into structured tasks, meeting notes, and daily briefings.

## First milestone

The current implementation focuses on the demo-ready core loop:

1. Watch a dedicated Discord `#action-items` channel.
2. Detect actionable messages with trigger phrases.
3. Ask the LLM layer to return a structured task.
4. Create a Plane issue via the Prime CLI.
5. React with `✅` on success or `❌` when parsing fails.

## Project layout

```text
src/
├── bot/
├── db/
├── gaps/
├── integrations/
├── llm/
└── meeting/
prompts/
tests/
```

## Development

```bash
PYTHONPATH=src python -m pytest
```
