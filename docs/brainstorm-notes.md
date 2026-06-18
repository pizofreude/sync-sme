# Notes — sync-sme
<!-- Append-only brainstorm dump. Date-stamp each entry. -->

## [2026-06-18] Initial Seed — Hackathon Briefing

**Context**: Kracked Devs 4-Day Vibe-A-Thon. Theme: everyday operational pain in small teams/businesses. Focus on manual work, forgotten tasks, fragmented communication, inefficient processes.

**Core insight**: The pain isn't "we don't have tools" — it's "we have too many tools and tasks fall through the cracks between them." The gap is the unstructured-to-structured bridge: chat text → actionable tasks.

**Key design decisions noted**:
- Dedicated channel approach (monitor #action-items, not all channels) — reduces noise, easier demo
- Three feature pillars: NLP parsing, meeting minutes, gap detection
- 9router.com for LLM routing — single API key, multi-model access

**Initial gaps identified**:
1. **Scope vs timeline**: 3 major features in 4 days is aggressive. Need MVP scoping.
2. **WhatsApp API friction**: Business API requires approval, takes days. Telegram Bot API is instant — better for hackathon.
3. **Meeting transcript dependency**: Need to verify which platforms expose transcript APIs. MS Teams Graph API does, Google Meet has limited API, Jitsi has webhook-based transcription.
4. **9router.com unknown**: Need to test latency, model availability, and pricing. May need fallback to direct OpenAI/Anthropic API for demo reliability.

## [2026-06-18] Direction Lock — MVP Stack Decided

**Decisions made**:
- **Option C chosen**: All three features (NLP parsing + meeting minutes + gap detection)
- **MVP stack locked**: Discord → Plane.so → Obsidian
  - Other platforms (WhatsApp, Slack, Telegram, Trello, Asana, Notion, etc.) deferred to post-hackathon
- **Chat platform**: Discord (instant bot setup, free, developer-friendly API)
- **LLM**: 9router.com confirmed (demo video can be sped up if latency is slow)
- **Meeting**: Discord voice/video calls (need to verify transcription approach)

**Rationale**: Focused stack = focused demo. Three tools that work well together. Discord handles both chat AND meetings — one integration point. Plane.so has clean API. Obsidian is just markdown files (simplest possible integration).

**Remaining unknowns**:
1. Discord voice transcription approach (audio stream vs Whisper vs built-in)
2. Plane.so API auth + task creation flow
3. Obsidian: local file writes vs Sync API
4. 9router.com model availability and response times

## [2026-06-18] Brainstorm Session #2 — Toolchain Deep Dive

**Key decisions made**:

### Voice Recording: Craig (craig.chat)
- Multi-track Discord voice recorder — each speaker gets isolated audio
- Output: FLAC (default), Opus, AAC, WAV — 17 codecs across 6 containers
- **REST API**: Full programmatic access — `/api/recording/:id/cook` to export, `/api/recording/:id/raw` to download
- Slash commands: `/join`, `/stop`, `/note` (timestamped bookmarks)
- Free tier: 6 hours max, 7-day retention, 512 MB — plenty for hackathon
- **Why Craig wins**: Multi-track = per-speaker transcription. Whisper gets clean single-voice audio instead of messy overlapping speakers.

### Transcription: Whisper (Python library, NOT Colab notebook)
- Skip the Colab notebook — it's a dead end for automation
- Use OpenAI's whisper library directly: `whisper.load_model("large")`
- Per-speaker transcription: Craig's multi-track → transcribe each track separately → better accuracy
- `result["segments"]` gives timestamps for SRT if needed
- For hackathon: use `faster-whisper` (GPU) or `whisper` (CPU, slower but works)

### Obsidian: CLI + Direct Filesystem
- **Obsidian CLI** (obsidian.md/cli): IPC-based, 115 commands, `obsidian create/append/daily:append`
- Requires Obsidian desktop running — acceptable for hackathon
- Vault path: `C:\Users\AbdulHafeez\OneDrive\EMAI` (synced to WSL2 via OneDrive)
- **Backup**: Direct filesystem writes — Obsidian auto-detects new `.md` files
- For headless/server: use Local REST API plugin (`https://127.0.0.1:27124`)

### Bot Name: "Sync"
- Feels like a team member, not a utility
- "Sync caught that action item" / "Sync's morning briefing"

**Pipeline confirmed**:
```
Discord voice → Craig records (multi-track) → Craig REST API downloads FLAC
                                                    ↓
                                            Whisper transcribes per-speaker
                                                    ↓
                                            9router LLM structures minutes
                                                    ↓
                                  ┌─────────────────┴─────────────────┐
                                  ↓                                   ↓
                          Plane.so (tasks)                    Obsidian (minutes)
```

**Craig self-hosting note**: Free tier is enough for hackathon. Post-hackathon, self-hosting (Linux, Node.js, PostgreSQL, Redis) unlocks unlimited recording — no feature gates.

## [2026-06-18] Brainstorm Session #3 — Final Toolchain Confirmations

### Plane.so: Prime CLI
- Pizo has Plane.so account + workspace already set up
- Using **Prime CLI** (https://developers.plane.so/self-hosting/manage/prime-cli) — official CLI
- This means task creation can be CLI-based: `plane create-issue --project <name> --title "..." --assignee "..."`
- Simpler than REST API for hackathon — no auth token juggling, CLI handles it

### 9router: Confirmed + Enhanced
- NVIDIA NIM API key added (fast inference, good for demo)
- Ollama API key added (local fallback, zero latency for testing)
- Free providers available as additional fallback
- Multiple model options: can test which responds fastest for NLP parsing

**All unknowns resolved. Full toolchain:**

| Component | Tool | Status |
|-----------|------|--------|
| LLM | 9router (NVIDIA NIM + Ollama + free) | ✅ Ready |
| Chat | Discord Bot API | ✅ Ready |
| Tasks | Plane.so Prime CLI | ✅ Ready |
| Notes | Obsidian CLI | ✅ Ready |
| Recording | Craig (craig.chat) | ✅ Ready |
| Transcription | Whisper (Python) | ✅ Ready |
| Bot name | "Sync" | ✅ Locked |

**No remaining unknowns. Ready for challenge phase.**
