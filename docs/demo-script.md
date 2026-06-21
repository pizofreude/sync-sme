# Sync-SME Demo Script

**Duration**: ~2 minutes
**Event**: Kracked Devs 4-Day Vibe-A-Thon

---

## Scene 1: Core Loop

**What to show**: Discord `#action-items` channel + Plane.so dashboard

1. Open Discord, navigate to `#action-items`
2. Type a message with a trigger phrase:
   ```
   todo: Deploy the new auth middleware to staging by Friday
   ```
3. Bot reacts with ✅
4. Switch to Plane.so — show the newly created issue with title, assignee, due date
5. Send a second message:
   ```
   need to update the API docs for the /users endpoint
   ```
6. Bot reacts with ✅ — second issue appears in Plane

**Narration**: "Sync-SME watches a dedicated Discord channel for actionable messages. When it detects a trigger phrase like 'todo' or 'need to', it uses a local LLM to extract a structured task — title, assignee, due date — and creates an issue in Plane.so automatically."

---

## Scene 2: Meeting Pipeline

**What to show**: Discord voice channel → Obsidian vault

1. Start a voice channel recording with Craig:
   ```
   /join
   ```
2. Speak for 15-20 seconds (or play sample audio):
   ```
   "Alright team, let's sync up. Sarah, can you handle the frontend refactor?
   Target is next Wednesday. Also, we need to set up the staging environment
   before the client demo on Thursday."
   ```
3. Stop recording:
   ```
   /leave
   ```
4. Show Craig API returning the recording
5. Show Speechmatics transcription output
6. Show LLM-generated meeting minutes in Obsidian:
   ```markdown
   # Meeting Notes — June 21, 2026

   ## Summary
   - Frontend refactor assigned to Sarah, due next Wednesday
   - Staging environment needed before Thursday client demo

   ## Action Items
   - [ ] Frontend refactor — Sarah — Due: 2026-06-25
   - [ ] Set up staging environment — Due: 2026-06-26
   ```
7. Show Plane issues created from action items

**Narration**: "Craig records multi-track audio from Discord voice channels — each speaker gets an isolated track. Speechmatics transcribes the audio, the LLM structures it into meeting minutes, and action items are automatically extracted and created as Plane issues."

---

## Scene 3: Gap Detection

**What to show**: Discord alert for unlogged task

1. Send a message in `#action-items` that looks like a task but doesn't use a trigger phrase:
   ```
   someone should really look into the memory leak in the worker process
   ```
2. Bot does NOT react (no trigger phrase detected)
3. Show the message tracked as a "gap candidate" in SQLite
4. After detection window (demo: show the alert formatting):
   ```
   ⚠️ This might be a task but hasn't been logged yet:
   > "someone should really look into the memory leak in the worker process"
   — posted by @user, 26 hours ago
   ```

**Narration**: "Not everything actionable uses a trigger phrase. Sync-SME tracks messages that look like tasks but weren't processed. After 24 hours without a Plane issue, it posts a gentle reminder — catching tasks that would otherwise slip through the cracks."

---

## Scene 4: Daily Briefing

**What to show**: Obsidian daily note with briefing

1. Show the scheduled briefing trigger (9 AM MYT via `discord.ext.tasks`)
2. Show the generated briefing in Obsidian:
   ```markdown
   # Daily Briefing — June 21, 2026

   ## Pending Tasks
   - Deploy auth middleware — assigned to @user — due Friday
   - Update API docs — unassigned

   ## Gaps Detected
   - ⚠️ Memory leak investigation — 26 hours unlogged

   ## Upcoming Deadlines
   - Frontend refactor — 2026-06-25 (Sarah)
   - Staging environment — 2026-06-26
   ```
3. Show the briefing also posted to Discord

**Narration**: "Every morning at 9 AM, Sync-SME generates a daily briefing — pending tasks from Plane, gap candidates that need attention, and upcoming deadlines. It's written to the Obsidian vault and posted to Discord, so the team starts each day with a clear picture."

---

## Scene 5: Architecture Overview

**What to show**: Stack diagram or project layout

```
Discord #action-items
    ↓
discli serve (JSONL stdin/stdout)
    ↓
Sync-SME Bot (Python)
    ↓
9router LLM (local, NVIDIA NIM)
    ↓
Plane.so (CLI + REST API)

Discord Voice → Craig → Speechmatics → LLM → Obsidian + Plane

SQLite (state + gaps) → Gap Detector → Discord Alerts
                       → Daily Briefing → Obsidian
```

**Narration**: "The full stack: discli handles Discord via a simple CLI protocol, 9router is the local LLM brain, Plane.so manages tasks, Craig and Speechmatics handle meeting transcription, Obsidian stores notes, and SQLite tracks state — all running as a single lightweight Python agent."

---

## Closing

**What to show**: Test results + repo

1. Show `pytest` output: `94 passed`
2. Show GitHub repo: `github.com/pizofreude/sync-sme`

**Narration**: "94 tests passing, fully open-source. I'm my first user — this solves a real problem I have every day. Sync-SME: turning Discord chaos into structured productivity."

---

## Recording Tips

- Use OBS or similar screen capture
- Resolution: 1920x1080
- Keep terminal font size large (16pt+)
- Pre-load the Discord channel and Plane dashboard before recording
- For the meeting pipeline demo, pre-record a short audio clip if live recording feels risky
- Practice the transitions between scenes 2-3 times
