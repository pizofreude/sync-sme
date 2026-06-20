# sync-sme

Sync-SME is a lightweight Python agent that turns Discord action items into structured tasks, meeting notes, and daily briefings.

## Features

### Core Loop (Day 1) ✅
1. Watch a dedicated Discord `#action-items` channel.
2. Detect actionable messages with trigger phrases (`todo`, `need to`, `assign to`, `deadline`, `follow up`, `remind me to`).
3. Ask the LLM layer (9router) to return a structured task.
4. Create a Plane issue via the Prime CLI or REST API.
5. React with `✅` on success or `❌` when parsing fails.
6. SQLite deduplication prevents double-processing.
7. Dry-run mode when Plane CLI/API is unavailable.

### Meeting Pipeline (Day 2) ✅
1. Craig records Discord voice channels (multi-track, per-speaker).
2. Whisper transcribes each speaker's audio.
3. LLM summarizes transcript into structured meeting minutes.
4. Minutes written to Obsidian vault (filesystem or notesmd-cli).
5. Action items extracted from minutes → Plane issues created.

## Stack

| Component | Tool |
|-----------|------|
| LLM | 9router (local, `localhost:20128`) — model: `nvidia/minimaxai/minimax-m2.7` |
| Chat | Discord Bot API (`discord.py`) |
| Tasks | Plane.so Prime CLI or REST API |
| Notes | Obsidian vault (filesystem + notesmd-cli) |
| Recording | Craig (craig.chat) |
| Transcription | Whisper (`openai-whisper`) |

## Project layout

```text
src/
├── bot/            # Discord client, message handlers
├── db/             # SQLite state store
├── gaps/           # Gap detection + daily briefing (scaffolded)
├── integrations/   # Craig, Obsidian, Plane clients
├── llm/            # 9router client, task parser, summarizer
└── meeting/        # Meeting pipeline (record → transcribe → summarize)
prompts/            # LLM system prompts
tests/              # 62 tests (all passing)
```

## Development

```bash
# Install dependencies
pip install -e ".[dev,meeting]"

# Run tests
PYTHONPATH=src python -m pytest

# Start the bot
PYTHONPATH=src python -m bot.client
```

## Environment Variables

See `.env.example` for all required and optional configuration. Key variables:

| Variable | Required | Description |
|----------|----------|-------------|
| `DISCORD_BOT_TOKEN` | Yes | Discord bot authentication |
| `NINEROUTER_API_KEY` | Yes | 9router API key |
| `PLANE_WORKSPACE_SLUG` | Yes | Plane.so workspace identifier |
| `PLANE_API_TOKEN` | No | Plane.so REST API token (alternative to CLI) |
| `PLANE_PROJECT_ID` | No | Plane.so project ID (required for REST API) |
| `CRAIG_API_KEY` | No | Craig recording API key (enables meeting pipeline) |
| `OBSIDIAN_VAULT_PATH` | No | Path to Obsidian vault (enables meeting pipeline) |
| `WHISPER_MODEL` | No | Whisper model size: `tiny`, `base`, `small`, `medium`, `large` |
