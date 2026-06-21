# sync-sme

Sync-SME is a lightweight Python agent that turns Discord action items into structured tasks, meeting notes, and daily briefings. Built for the **Kracked Devs 4-Day Vibe-A-Thon**.

## Features

### Core Loop ✅
1. Watch a dedicated Discord `#action-items` channel.
2. Detect actionable messages with trigger phrases (`todo`, `need to`, `assign to`, `deadline`, `follow up`, `remind me to`).
3. Ask the LLM layer (9router) to return a structured task.
4. Create a Plane issue via the Prime CLI or REST API.
5. React with `✅` on success or `❌` when parsing fails.
6. SQLite deduplication prevents double-processing.
7. Dry-run mode when Plane CLI/API is unavailable.

### Meeting Pipeline ✅
1. Craig records Discord voice channels (multi-track, per-speaker).
2. Speechmatics transcribes each speaker's audio via Pipecat.
3. LLM summarizes transcript into structured meeting minutes.
4. Minutes written to Obsidian vault (filesystem or notesmd-cli).
5. Action items extracted from minutes → Plane issues created.

### Gap Detection + Daily Briefing ✅
1. Non-actionable messages in `#action-items` tracked as gap candidates.
2. After 24 hours without a Plane issue, a ⚠️ alert is posted to Discord.
3. Daily briefing generated at 9 AM MYT — pending tasks, gaps, deadlines.
4. Briefing written to Obsidian vault automatically.

## Stack

| Component | Tool |
|-----------|------|
| LLM | 9router (local, `localhost:20128`) — model: `nvidia/minimaxai/minimax-m2.7` |
| Chat | Discord CLI (`discli`) |
| Tasks | Plane.so Prime CLI or REST API |
| Notes | Obsidian vault (filesystem + notesmd-cli) |
| Recording | Craig (craig.chat) |
| Transcription | Speechmatics (via `pipecat-ai[speechmatics]`) |
| Storage | SQLite (state store + gap tracker) |

## Quick Start

### Prerequisites
- Python 3.11+
- Discord bot token ([Discord Developer Portal](https://discord.com/developers/applications))
- 9router running locally (`localhost:20128`) or API key
- Plane.so workspace slug

### Setup

```bash
# Clone and install
git clone git@github.com:pizofreude/sync-sme.git
cd sync-sme
pip install -e ".[dev,meeting]"

# Configure environment
cp .env.example .env
# Edit .env with your credentials

# Run tests
PYTHONPATH=src python -m pytest

# Start the bot
PYTHONPATH=src python -m bot.client
```

### Environment Variables

See `.env.example` for all configuration. Required:

| Variable | Required | Description |
|----------|----------|-------------|
| `DISCORD_BOT_TOKEN` | Yes | Discord bot authentication |
| `NINEROUTER_API_KEY` | Yes | 9router API key |
| `PLANE_WORKSPACE_SLUG` | Yes | Plane.so workspace identifier |
| `PLANE_API_TOKEN` | No | Plane.so REST API token (alternative to CLI) |
| `PLANE_PROJECT_ID` | No | Plane.so project ID (required for REST API) |
| `CRAIG_API_KEY` | No | Craig recording API key (enables meeting pipeline) |
| `OBSIDIAN_VAULT_PATH` | No | Path to Obsidian vault (enables meeting pipeline) |
| `SPEECHMATICS_API_KEY` | No | Speechmatics API key (enables transcription) |
| `GAP_DETECTION_HOURS` | No | Hours before flagging a gap (default: 24) |
| `BRIEFING_CRON` | No | Cron schedule for daily briefing (default: `0 9 * * *`) |

## Project Layout

```text
src/
├── bot/            # Discord client, message handlers, settings
├── db/             # SQLite state store
├── gaps/           # Gap detection + daily briefing
├── integrations/   # Craig, Obsidian, Plane clients
├── llm/            # 9router client, task parser, summarizer
└── meeting/        # Meeting pipeline (record → transcribe → summarize)
prompts/            # LLM system prompts
tests/              # 94 tests (all passing)
docs/               # Idea, brainstorm, challenge log
```

## Demo Script

See [`docs/demo-script.md`](docs/demo-script.md) for the full walkthrough:

1. **Core Loop**: Send a message in `#action-items` → Plane issue created
2. **Meeting Pipeline**: Record a voice meeting → minutes in Obsidian
3. **Gap Detection**: Unlogged task detected → Discord alert
4. **Daily Briefing**: Morning briefing generated → written to Obsidian

## Development

```bash
# Run tests
PYTHONPATH=src python -m pytest

# Run with verbose output
PYTHONPATH=src python -m pytest -v

# Start the bot
PYTHONPATH=src python -m bot.client
```

## License

MIT
