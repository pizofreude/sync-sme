# Getting Started with Sync-SME

A complete step-by-step guide to set up and run Sync-SME from scratch. Follow this guide in order — each section builds on the previous one.

**Estimated time**: 20–30 minutes (excluding 9router setup)

---

## Table of Contents

1. [Prerequisites](#1-prerequisites)
2. [Create Your Discord Server](#2-create-your-discord-server)
3. [Discord Bot Setup](#3-discord-bot-setup)
4. [Install discli](#4-install-discli)
5. [9router Setup (Local LLM)](#59router-setup-local-llm)
6. [Plane.so Setup](#6planeso-setup)
7. [Obsidian Setup (Optional)](#7obsidian-setup-optional)
8. [Craig Setup (Optional)](#8craig-setup-optional)
9. [Speechmatics Setup (Optional)](#9speechmatics-setup-optional)
10. [Clone & Install sync-sme](#10-clone--install-sync-sme)
11. [Configure Environment](#11-configure-environment)
12. [Run Tests](#12-run-tests)
13. [Start the Bot](#13-start-the-bot)
14. [Test the Core Loop](#14-test-the-core-loop)
15. [Test the Meeting Pipeline](#15-test-the-meeting-pipeline)
16. [Test Gap Detection](#16-test-gap-detection)
17. [Quick Demo Flow (For Recording)](#17-quick-demo-flow-for-recording)
18. [Troubleshooting](#18-troubleshooting)

---

## 1. Prerequisites

Make sure you have these installed:

| Tool | Version | Check | Install |
|------|---------|-------|---------|
| Python | 3.11+ | `python --version` | [python.org](https://www.python.org/downloads/) |
| pip | any | `pip --version` | Comes with Python |
| Git | any | `git --version` | [git-scm.com](https://git-scm.com/) |

**Accounts you'll need:**

- **Discord** — with a server where you have admin permissions
- **Plane.so** — free account at [plane.so](https://plane.so)

**Optional accounts** (for meeting pipeline):

- **Craig** — [craig.chat](https://craig.chat) (free tier: 6 hours recording)
- **Speechmatics** — [speechmatics.com](https://www.speechmatics.com) (free trial available)

---

## 2. Create Your Discord Server

> **Skip this section** if you already have a Discord server with admin permissions.

This section walks you through creating a professional multi-client workspace on Discord — with full privacy between clients, video calls, and clean sync-sme integration.

### 2.1 Create the Server

1. Open [discord.com](https://discord.com) → click the **"+"** in the left sidebar
2. Select **"Create My Own"** → **"For me and my friends"**
3. Name it (e.g., `Freuden Reisen` or your brand name) → click **"Create"**

### 2.2 Server Architecture Overview

The server uses **role-based category isolation** — `@everyone` is denied access everywhere by default. Each person only sees the category their role unlocks. The sync-sme bot is added to **every** category so it can read chats, process attachments, and write meeting notes back.

```
📁 🔐 COMMAND CENTER               [you + @sync-sme]
  📝 #action-items                 ← sync-sme monitors for task keywords
  📝 #daily-briefing               ← sync-sme posts morning briefing
  📝 #gap-alerts                   ← sync-sme posts gap detection warnings
  📝 #bot-logs                     ← bot status messages
  🔊 Internal Voice

📁 ☕ PROSPECT: [Company]          [you + @sync-sme + @Craig + @Prospect-Company]
  📝 #[company]-chat               ← text, files, images, video — bot can read & summarize
  🔊 [Company] Call                ← video call; @Craig can record if invited

📁 📋 CLIENT: [Company]            [you + @sync-sme + @Craig + @Client-Company]
  📝 #[company]-general            ← async comms — bot can read & summarize
  📝 #[company]-action-items       ← client-facing task updates
  📝 #[company]-meeting-notes      ← sync-sme writes meeting minutes here automatically
  🔊 [Company] Meeting Room        ← video call + Craig records for full transcription pipeline
```

**Why `@sync-sme` needs to be in every category:**

| Capability | What it needs |
|-----------|---------------|
| Write meeting minutes to `#[company]-meeting-notes` | Send Messages ✅ in that channel |
| Summarize chat history on demand | Read Message History ✅ |
| Process shared attachments/files | Attach Files ✅ |
| Post gap alerts or task confirmations | Send Messages ✅ |

**Why `@Craig` needs to be in every voice channel:**

| Capability | What it needs |
|-----------|---------------|
| Join a voice channel to record | Connect ✅ |
| Capture audio | Speak ✅ (so Discord allows Craig to receive audio) |

### 2.3 Set the Default Permission (deny everyone)

This is the single most important step — it makes all future categories private by default.

1. Open **Server Settings** → **Roles** → click **"@everyone"**
2. Scroll to **"Text Channel Permissions"** and set:
   - **View Channels** → ✖️ Denied
3. Click **"Save Changes"**

Now no one can see any channel unless explicitly granted access via their role.

### 2.4 Create Bot Roles

1. Go to **Server Settings** → **Roles** → **"Create Role"**
2. Create two bot roles:
   - `sync-sme` (color: blue or grey)
   - `Craig` (color: red or purple)
3. Save each role

### 2.5 Create the COMMAND CENTER Category

1. Right-click the channel list → **"Create Category"** → name it `🔐 COMMAND CENTER`
2. Click the **lock icon** on the category → **"Edit Category"** → **"Permissions"**
3. Under **Roles/Members**, click **"+"** → find **your own username** → set:
   - **View Channel** → ✅ Allow
4. Click **"+"** again → find `sync-sme` role → set:
   - **View Channel** → ✅ Allow
   - **Read Message History** → ✅ Allow
   - **Send Messages** → ✅ Allow
   - **Attach Files** → ✅ Allow
5. Add these text channels inside the category:
   - `action-items`
   - `daily-briefing`
   - `gap-alerts`
   - `bot-logs`
6. Add one voice channel: `Internal Voice`

### 2.6 Invite a Prospect (repeatable per prospect/company)

**Step 1 — Create the prospect role (~30 seconds)**
1. **Server Settings** → **Roles** → **"Create Role"**
2. Name it `Prospect-[Company]` (e.g., `Prospect-Acme`) → color: orange → Save

**Step 2 — Create the prospect category (~2 minutes)**
1. Right-click channel list → **"Create Category"** → name it `☕ PROSPECT: [Company]`
2. Edit category permissions (deny `@everyone` is already inherited from step 2.3):
   - Allow your username → View Channel ✅
   - Allow `Prospect-[Company]` → View Channel ✅, Send Messages ✅
   - Allow `sync-sme` → View Channel ✅, Read Message History ✅, Send Messages ✅, Attach Files ✅
   - Allow `Craig` → Connect ✅, Speak ✅ *(enables recording this voice channel if needed)*
3. Add inside the category:
   - Text channel: `[company]-chat`
   - Voice channel: `[Company] Call`

**Step 3 — Generate invite link**
1. Right-click `#[company]-chat` → **"Invite People"**
2. Click **"Edit invite link"** → set expiry (7 days recommended) → Copy Link
3. Send the link via email, WhatsApp, or LinkedIn

**Step 4 — When they join**
1. You see a join notification — click their name → **"Manage"** → **"Add Role"**
2. Assign `Prospect-[Company]` to each person from that company
3. They now see only `☕ PROSPECT: [Company]` — nothing else is visible

> 💡 **Same link works for the whole company team.** All members with `Prospect-[Company]` share the same channels — they see each other within their category but nothing outside it.

### 2.7 Prospect → Client (when a deal closes)

No re-invitation needed. They already have server access. The `@sync-sme` and `@Craig` roles are already on the category from the prospect stage.

1. **Rename the role**: `Prospect-[Company]` → `Client-[Company]`
2. **Rename the category**: `☕ PROSPECT: [Company]` → `📋 CLIENT: [Company]`
3. **Add channels** to the category:
   - Text: `[company]-action-items`
   - Text: `[company]-meeting-notes` *(sync-sme will auto-write meeting minutes here)*
4. **Verify category permissions** still include:
   - `sync-sme` → View Channel ✅, Read Message History ✅, Send Messages ✅, Attach Files ✅
   - `Craig` → Connect ✅, Speak ✅
5. Done — same people, same invite, now in full client mode

### 2.8 If the Deal Doesn't Close

1. Remove `Prospect-[Company]` role from all members (they instantly see nothing)
2. Delete the `☕ PROSPECT: [Company]` category (permanently removes all chat history)
3. Optionally kick them from the server

### 2.9 Add a New Client Directly (without prospect stage)

Same as the prospect flow above, but:
- Name the role `Client-[Company]` from the start
- Name the category `📋 CLIENT: [Company]`
- Create all 3 text channels + 1 voice channel directly
- Permissions must include `sync-sme` (text + history) and `Craig` (voice) from the start:
  - `sync-sme` → View Channel ✅, Read Message History ✅, Send Messages ✅, Attach Files ✅
  - `Craig` → Connect ✅, Speak ✅

### 2.10 Video Calls

No extra tools needed. Discord Voice Channels natively support:

| Feature | How |
|---------|-----|
| Camera video | Click the camera icon in the voice channel |
| Screen share | Click the screen icon in the voice channel |
| Group call | Multiple people join the same voice channel |
| Recording (any call) | Craig bot joins the voice channel (see [Section 8](#8-craig-setup-optional)) |

> 💡 **Prospect calls**: use `[Company] Call` in the PROSPECT category. Craig is already permitted there — just type `/join` in the voice channel to start recording if you want a transcript.
> **Client meetings**: use `[Company] Meeting Room` in the CLIENT category. Same Craig + full pipeline: audio → Speechmatics → LLM summary → `#meeting-notes` + Obsidian.

---

## 3. Discord Bot Setup

### 3.1 Create a Discord Application

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Click **"New Application"** in the top right
3. Name it `sync-sme` (or whatever you prefer)
4. Click **"Create"**

### 3.2 Create a Bot

1. In the left sidebar, click **"Bot"**
2. Click **"Reset Token"** → copy the token and save it somewhere safe
   - ⚠️ **This token is your `DISCORD_BOT_TOKEN`** — never share it or commit it to git
3. Under **"Privileged Gateway Intents"**, enable:
   - ✅ **Message Content Intent** (required — the bot needs to read message text)
4. Click **"Save Changes"**

### 3.3 Set Bot Permissions

1. In the left sidebar, click **"OAuth2"**
2. In the **"Redirects"** section at the top, click **"Add Redirect"** and enter:
   ```
   https://localhost
   ```
   Then click **"Save Changes"**. This is a placeholder — the bot never actually redirects, but Discord requires at least one URI.
3. Under **"OAuth2 URL Generator"**, check these scopes:
   - ✅ `bot`
4. Under **"Select redirect URI"**, choose `https://localhost` from the dropdown
5. Under **"Bot Permissions"**, check:
   - ✅ Send Messages
   - ✅ Add Reactions
   - ✅ Read Message History
   - ✅ Use Slash Commands (optional, for future)
6. Copy the **Generated URL** at the bottom

### 3.4 Invite the Bot to Your Server

1. Open the generated URL in your browser
2. Select your server from the dropdown
3. Click **"Authorize"**
4. The bot should now appear in your server's member list (offline until we start it)

### 3.5 Create the `#action-items` Channel

1. In your Discord server, navigate to your `🔐 COMMAND CENTER` category
2. Click **"+"** next to the category → **"Create Text Channel"**
3. Name it `action-items` (no `#` needed — Discord adds it)
4. Click **"Create Channel"**

> 💡 If you followed [Section 2](#2-create-your-discord-server), this channel already exists inside COMMAND CENTER — skip this step.

---

## 4. Install discli

[discli](https://discli.rohitk06.in/) is the Discord CLI for AI Agents. It handles all Discord communication for sync-sme.

```bash
pip install discli
```

### 4.1 Configure the Bot Token

discli needs your Discord bot token. Set it in one of these ways:

**Option A — Environment variable (recommended):**

```bash
# Linux/macOS
export DISCORD_BOT_TOKEN="your-token-here"

# Windows PowerShell
$env:DISCORD_BOT_TOKEN = "your-token-here"

# Windows CMD
set DISCORD_BOT_TOKEN=your-token-here
```

**Option B — discli config:**

```bash
discli config set token YOUR_TOKEN_HERE
```

### 4.2 Verify discli Works

```bash
discli --version
```

You should see something like `discli 1.1.3`.

---

## 5. 9router Setup (Local LLM)

9router is the local LLM gateway that powers task parsing and meeting summarization.

### 5.1 Option A — Use 9router Cloud (Easiest)

If you have a 9router API key, just set `NINEROUTER_API_KEY` in your `.env` file. Skip to section 6.

### 5.2 Option B — Run 9router Locally

Follow the [9router installation guide](https://github.com/nine-router/9router) to run it locally on port `20128`.

Once running, verify it's working:

```bash
curl http://localhost:20128/v1/models
```

You should see a JSON response with available models.

### 5.3 Option C — Use Any OpenAI-Compatible API

If you have another LLM API (OpenAI, Ollama, etc.), you can point sync-sme at it by setting:

```env
NINEROUTER_ENDPOINT=https://your-api.com/v1/chat/completions
NINEROUTER_API_KEY=your-key
LLM_MODEL=your-model-name
```

---

## 6. Plane.so Setup

Plane.so is where tasks are created.

### 6.1 Get Your Workspace Slug

1. Log in to [plane.so](https://plane.so)
2. Look at the URL: `https://app.plane.so/your-workspace/projects/...`
3. The `your-workspace` part is your workspace slug

### 6.2 Option A — Use Plane CLI (Recommended)

Install the Plane CLI:

```bash
npm install -g @plane/cli
```

Or follow the [Plane CLI docs](https://docs.plane.so/cli).

### 6.3 Option B — Use Plane REST API

1. Go to **Settings → API Tokens** in Plane.so
2. Create a new token
3. Copy the token — this is your `PLANE_API_TOKEN`
4. Note your project ID from the project URL — this is your `PLANE_PROJECT_ID`

### 6.4 Option C — Dry-Run Mode

If you don't set up Plane, sync-sme will run in **dry-run mode** — it logs what it would create without actually creating issues. This is useful for testing.

---

## 7. Obsidian Setup (Optional)

Obsidian is where meeting notes and daily briefings are written.

### 7.1 Install Obsidian

Download from [obsidian.md](https://obsidian.md) and create or open a vault.

### 7.2 Find Your Vault Path

| OS | Typical Path |
|----|-------------|
| Windows | `C:\Users\YourName\Documents\MyVault` |
| macOS | `/Users/YourName/Documents/MyVault` |
| Linux | `/home/yourname/Documents/MyVault` |

### 7.3 Optional — Install notesmd-cli

For richer Obsidian integration, install [notesmd-cli](https://github.com/notesmd/cli):

```bash
npm install -g notesmd-cli
```

Sync-SME will automatically use notesmd-cli if available, otherwise it writes files directly to the vault filesystem.

---

## 8. Craig Setup (Optional)

Craig is a Discord voice channel recorder that provides multi-track audio.

### 8.1 Get a Craig API Key

1. Go to [craig.chat](https://craig.chat)
2. Sign in with Discord
3. Go to your dashboard
4. Copy your API key — this is your `CRAIG_API_KEY`

### 8.2 Invite Craig to Your Server

1. On craig.chat, click **"Invite Craig"**
2. Select your server
3. Authorize the bot

Craig is now ready to record voice channels in your server.

---

## 9. Speechmatics Setup (Optional)

Speechmatics provides cloud transcription for meeting recordings.

### 9.1 Get an API Key

1. Go to [speechmatics.com](https://www.speechmatics.com)
2. Sign up for a free trial
3. Go to **API Keys** in your dashboard
4. Create a new key — this is your `SPEECHMATICS_API_KEY`

---

## 10. Clone & Install sync-sme

```bash
# Clone the repository
git clone git@github.com:pizofreude/sync-sme.git
cd sync-sme

# Install with all dependencies (including meeting pipeline)
pip install -e ".[dev,meeting]"

# Or install without meeting dependencies (core loop only)
pip install -e ".[dev]"
```

### 10.1 Verify Installation

```bash
# Should show discli, python-dotenv, pytest, etc.
pip list | grep -iE "discli|pytest|dotenv|pipecat"
```

---

## 11. Configure Environment

### 11.1 Create .env File

```bash
cp .env.example .env
```

### 11.2 Edit .env

Open `.env` in your editor and fill in the values:

```env
# === REQUIRED ===
DISCORD_BOT_TOKEN=your-discord-bot-token-from-step-2
NINEROUTER_API_KEY=your-9router-api-key
PLANE_WORKSPACE_SLUG=your-plane-workspace-slug

# === OPTIONAL (core loop works without these) ===
PLANE_API_TOKEN=              # Plane REST API token (alternative to CLI)
PLANE_PROJECT_ID=             # Plane project ID (required for REST API)
PLANE_ASSIGNEE_MAP=           # Discord ID:Plane member mapping (e.g., "12345:alice,67890:bob")

# === MEETING PIPELINE (all three required together) ===
CRAIG_API_KEY=                # Craig recording API key
SPEECHMATICS_API_KEY=         # Speechmatics transcription API key
OBSIDIAN_VAULT_PATH=          # Path to your Obsidian vault

# === LLM CONFIG ===
NINEROUTER_ENDPOINT=http://localhost:20128/v1/chat/completions
LLM_MODEL=nvidia/minimaxai/minimax-m2.7

# === GAP DETECTION ===
GAP_DETECTION_HOURS=24        # Hours before flagging a gap candidate
BRIEFING_CRON=0 9 * * *       # Daily briefing schedule (minute hour * * *)
ACTION_ITEMS_CHANNEL=action-items  # Discord channel name to monitor
```

### 11.3 Minimum Viable .env

For the **core loop only** (no meeting pipeline), you need just these:

```env
DISCORD_BOT_TOKEN=your-token
NINEROUTER_API_KEY=your-key
PLANE_WORKSPACE_SLUG=your-slug
```

Everything else has sensible defaults or runs in dry-run mode.

---

## 12. Run Tests

Verify everything is working:

```bash
PYTHONPATH=src python -m pytest -v
```

You should see **94 tests passing**:

```
tests/test_briefing.py ....                         [  4%]
tests/test_craig.py ...                             [  7%]
tests/test_edge_cases.py .......                    [ 14%]
tests/test_gap_detector.py .........                [ 24%]
tests/test_gap_tracker.py .........                 [ 34%]
tests/test_handler_gap_integration.py .......       [ 41%]
tests/test_handlers.py ........                     [ 50%]
tests/test_meeting_pipeline.py ........             [ 58%]
tests/test_obsidian.py .....                        [ 63%]
tests/test_plane.py ...................             [ 85%]
tests/test_plane_api.py ...                         [ 88%]
tests/test_task_parser.py ...                       [ 91%]
tests/test_transcriber.py ........                  [100%]

======================= 94 passed =======================
```

---

## 13. Start the Bot

```bash
PYTHONPATH=src python -m bot.client
```

You should see:

```
sync-sme starting (discli serve mode)
  Meeting pipeline: DISABLED       # (or ACTIVE if configured)
  Gap detection: ACTIVE (24h window)
  Daily briefing: 09:00 MYT
  Obsidian: DISABLED               # (or path if configured)
Bot connected as sync-sme
```

The bot is now online in Discord! You'll see it appear as online in your server.

---

## 14. Test the Core Loop

### 14.1 Send an Actionable Message

In your Discord server, go to `#action-items` and type:

```
todo: Deploy the new authentication middleware to staging
```

**What happens:**
1. The bot detects the `todo` trigger keyword
2. Sends the message to 9router for parsing
3. Creates a Plane issue with title "Deploy the new authentication middleware to staging"
4. Reacts with ✅ on your message

### 14.2 Try Different Trigger Keywords

```
need to update the API documentation for the /users endpoint
assign to @alice: review the pull request
deadline: Submit the quarterly report by Friday
follow up on the client feedback from last week
remind me to back up the database before migration
```

All six trigger keywords: `todo`, `need to`, `assign to`, `deadline`, `follow up`, `remind me to`

### 14.3 Test Dry-Run Mode

If you haven't set up Plane CLI or API, the bot will run in dry-run mode. It will still parse the task and react with ✅, but log what it *would* create instead of creating real issues.

---

## 15. Test the Meeting Pipeline

**Requirements**: `CRAIG_API_KEY`, `SPEECHMATICS_API_KEY`, and `OBSIDIAN_VAULT_PATH` must all be set.

### 15.1 Record a Meeting

1. Join a voice channel in your Discord server
2. In any text channel, type:
   ```
   !join
   ```
   (or use Craig's slash command — Craig will join the voice channel and start recording)
3. Speak for 15–30 seconds
4. Type:
   ```
   !leave
   ```
   (Craig leaves and processes the recording)

### 15.2 Trigger the Pipeline

After Craig finishes processing, the meeting pipeline will:

1. Download the recording via Craig's REST API
2. Transcribe it with Speechmatics
3. Summarize the transcript with the LLM
4. Write meeting minutes to your Obsidian vault
5. Extract action items and create Plane issues

---

## 16. Test Gap Detection

### 16.1 Send a Non-Actionable Message

In `#action-items`, type something that looks like a task but **doesn't** use a trigger keyword:

```
someone should really look into the memory leak in the worker process
```

**What happens:**
- The bot does NOT react (no trigger keyword detected)
- The message is silently tracked as a "gap candidate"

### 16.2 Wait for the Gap Alert

After `GAP_DETECTION_HOURS` (default: 24 hours), if no Plane issue has been created for that message, the bot posts:

```
⚠️ This might be a task but hasn't been logged yet:
> "someone should really look into the memory leak in the worker process"
— posted by @user, 26 hours ago
```

### 16.3 Test Gap Resolution

If you later send an actionable message that gets processed, the gap candidate for that message ID is automatically resolved.

---

## 17. Quick Demo Flow (For Recording)

Follow this sequence for a ~3 minute demo video:

### Scene 1: Core Loop (45s)

```
# In #action-items:
todo: Deploy the new auth middleware to staging by Friday
```
→ Show ✅ reaction → Switch to Plane.so → Show the created issue

```
# In #action-items:
need to update the API docs for the /users endpoint
```
→ Show ✅ → Show second issue in Plane

### Scene 2: Meeting Pipeline (60s)

1. Join voice channel
2. `!join` (Craig starts recording)
3. Speak for 15s: *"Alright team, Sarah take the frontend refactor, due Wednesday. Also set up staging before Thursday's demo."*
4. `!leave`
5. Show Speechmatics transcription
6. Show meeting minutes in Obsidian
7. Show action items created as Plane issues

### Scene 3: Gap Detection (30s)

```
# In #action-items (no trigger keyword):
someone should look into the memory leak in the worker
```
→ Show no reaction → Explain the gap candidate → Show the alert (after delay)

### Scene 4: Daily Briefing (30s)

- Show the scheduled briefing (9 AM MYT)
- Show Obsidian daily note with: pending tasks, gaps detected, upcoming deadlines

### Scene 5: Architecture (15s)

```
Discord #action-items
    ↓
discli serve (JSONL stdin/stdout)
    ↓
Sync-SME Bot (Python)
    ↓
9router LLM (local) → Plane.so
Craig → Speechmatics → Obsidian
SQLite → Gap Detector → Discord Alerts
```

→ Show `94 passed` test output → Show GitHub repo

---

## 18. Troubleshooting

### Bot doesn't come online

- **Check the token**: `echo $DISCORD_BOT_TOKEN` should print your token (not empty)
- **Check discli**: `discli --version` should work
- **Check intents**: Make sure "Message Content Intent" is enabled in the Discord Developer Portal
- **Check the bot is invited**: The bot should appear in your server's member list

### Bot is online but doesn't react to messages

- **Check the channel name**: Must be exactly `action-items` (or whatever `ACTION_ITEMS_CHANNEL` is set to)
- **Check trigger keywords**: Messages must contain one of: `todo`, `need to`, `assign to`, `deadline`, `follow up`, `remind me to`
- **Check bot permissions**: The bot needs "Send Messages" and "Add Reactions" permissions in the channel
- **Check Message Content Intent**: Without this, the bot sees empty message content

### "RuntimeError: DISCORD_BOT_TOKEN is required"

- Make sure `.env` exists and contains `DISCORD_BOT_TOKEN=your-token`
- Or set the environment variable: `export DISCORD_BOT_TOKEN="your-token"`

### "RuntimeError: NINEROUTER_API_KEY is required"

- Set `NINEROUTER_API_KEY` in `.env`
- Or make sure 9router is running locally at `localhost:20128`

### Plane issues not created (dry-run mode)

This is expected if you haven't set up Plane CLI or API. The bot will log:

```
Plane CLI not found and PLANE_API_TOKEN not set — running in dry-run mode
```

To fix: install the Plane CLI (`npm install -g @plane/cli`) or set `PLANE_API_TOKEN` + `PLANE_PROJECT_ID` in `.env`.

### Meeting pipeline not active

The meeting pipeline requires **all three** of:
- `CRAIG_API_KEY`
- `SPEECHMATICS_API_KEY`
- `OBSIDIAN_VAULT_PATH`

If any is missing, the pipeline is disabled. Check the startup output:

```
Meeting pipeline: DISABLED    # ← fix by setting all three env vars
```

### Tests failing

Make sure you're using Python 3.11+ and have installed dev dependencies:

```bash
pip install -e ".[dev,meeting]"
PYTHONPATH=src python -m pytest -v
```

### discli command not found

```bash
pip install discli
# Verify:
discli --version
```

> ⚠️ **Important**: The `discli` package on PyPI (v1.1.3 by zenqii) is a Discord bot scaffolding tool — it does **not** support `serve` mode. sync-sme requires the **rohitk06 discli** (AI agent serve-mode CLI) from [discli.rohitk06.in](https://discli.rohitk06.in/). If `discli --json serve` does nothing, you have the wrong package installed. Install the correct one:
> ```bash
> pip uninstall discli -y
> pip install git+https://github.com/rohitk06/discli.git  # adjust URL if needed
> ```

---

## Architecture Reference

```text
src/
├── bot/
│   ├── client.py       # discli serve mode event loop, BotSettings, wiring
│   └── handlers.py     # Message handler, trigger keywords, reaction callback
├── db/
│   └── models.py       # SQLite state store (processed message dedup)
├── gaps/
│   ├── tracker.py      # GapTracker — SQLite-backed gap candidate storage
│   ├── detector.py     # GapDetector — finds overdue candidates
│   └── briefing.py     # DailyBriefingGenerator — LLM-powered briefing
├── integrations/
│   ├── craig.py        # Craig REST API client
│   ├── obsidian.py     # Obsidian vault writer (filesystem + notesmd-cli)
│   └── plane.py        # Plane.so CLI wrapper + REST API client
├── llm/
│   ├── router.py       # 9router HTTP client
│   ├── parser.py       # TaskParser — LLM-powered task extraction
│   └── summarizer.py   # MeetingSummarizer — LLM-powered meeting summary
└── meeting/
    ├── pipeline.py     # MeetingPipeline — full fetch→transcribe→summarize→write
    ├── recorder.py     # CraigRecorder — download recordings
    └── transcriber.py  # SpeechmaticsTranscriber — batch API transcription

prompts/                # LLM system prompts (task parsing, summarization, briefing)
tests/                  # 94 tests (all passing)
docs/                   # This file, demo script, idea docs
```

---

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DISCORD_BOT_TOKEN` | **Yes** | — | Discord bot authentication token |
| `NINEROUTER_API_KEY` | **Yes** | — | 9router API key |
| `PLANE_WORKSPACE_SLUG` | **Yes** | — | Plane.so workspace identifier |
| `NINEROUTER_ENDPOINT` | No | `https://9router.com/api/v1/chat/completions` | 9router API endpoint |
| `LLM_MODEL` | No | `nvidia/llama-3.1-70b-instruct` | LLM model for task parsing |
| `ACTION_ITEMS_CHANNEL` | No | `action-items` | Discord channel to monitor |
| `PLANE_API_TOKEN` | No | — | Plane.so REST API token |
| `PLANE_PROJECT_ID` | No | — | Plane.so project ID (for REST API) |
| `PLANE_ASSIGNEE_MAP` | No | — | Discord ID to Plane member mapping |
| `CRAIG_API_KEY` | No | — | Craig recording API key |
| `CRAIG_API_BASE` | No | `https://craig.chat/api` | Craig API base URL |
| `SPEECHMATICS_API_KEY` | No | — | Speechmatics transcription API key |
| `OBSIDIAN_VAULT_PATH` | No | — | Path to Obsidian vault |
| `GAP_DETECTION_HOURS` | No | `24` | Hours before flagging a gap |
| `BRIEFING_CRON` | No | `0 9 * * *` | Daily briefing cron (min hour dom mon dow) |
| `SYNC_SME_DB_PATH` | No | `sync_sme.db` | SQLite database file path |
| `DISCORD_ALERTS_CHANNEL_ID` | No | — | Channel ID for gap alert posts (right-click channel → Copy ID) |
| `DISCORD_BRIEFING_CHANNEL_ID` | No | — | Channel ID for daily briefing posts |
