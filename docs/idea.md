---
idea: sync-sme
created: 2026-06-18
status: exploring
tags: [hackathon, vibe-a-thon, kracked-devs, ai-agent, productivity, sme]
event: Kracked Devs 4-Day Vibe-A-Thon
---

## The Idea

A lightweight AI agent that monitors a dedicated Discord channel for actionable keywords and automatically creates structured tasks in Plane.so. Also generates meeting minutes from Discord calls and produces daily briefing summaries to Obsidian.

**MVP Stack**: Discord → Plane.so → Obsidian (expandable to other platforms later)

## Problem

Small teams fragment their work across too many tools:
- **Chat**: WhatsApp, Slack, Telegram, Discord
- **Tasks & Tracking**: Trello, Asana, Plane.so, GitHub Projects, spreadsheets
- **Notetaking**: Notion, Obsidian, Plane.so
- **Meetings**: MS Teams, Google Meet, Jitsi Meet, Discord

The result:
- Action items get lost in chat logs
- Status updates are manual
- Meeting minutes are written by hand
- No single source of truth for "what needs to get done"

## Proposed Solution

**Sync-SME** — Cross-Platform Task Unifier with three core capabilities:

### 1. NLP Parsing (Discord → Plane.so)
AI monitors a dedicated Discord channel for actionable keywords:
- "remind me to…"
- "assign to @person…"
- "deadline is…"
- "need to…", "todo…", "follow up on…"

Parses unstructured text into structured data: **Task, Assignee, Due Date** → creates task in Plane.so

### 2. Meeting Minutes Agent (Discord → Obsidian)
AI listens to Discord voice/video calls and:
- Generates structured meeting minutes
- Extracts action items with owners and deadlines
- Writes minutes to Obsidian vault + creates tasks in Plane.so

### 3. Gap Detection & Daily Briefing (Obsidian)
- **Gap Detection**: Alerts if a task mentioned in Discord hasn't been logged in Plane.so within 24 hours
- **Morning Briefing**: Daily summary written to Obsidian — pending tasks, upcoming deadlines, gaps

## Why Now?

- LLMs are now capable enough for reliable NLP parsing of conversational text
- Discord API is the most developer-friendly: bots, webhooks, voice channel access, all free
- 9router.com provides unified LLM routing — single API key, multi-model access
- Hackathon theme explicitly targets this pain: "manual work, forgotten tasks, fragmented communication"
- Plane.so has a clean REST API — perfect for hackathon integration

## Target User

Small teams (2-20 people) who:
- Use multiple communication tools daily
- Don't have a dedicated project manager
- Lose tasks in chat threads
- Need lightweight automation without enterprise complexity

## Revenue Model

- **Freemium**: 1 channel integration, 10 tasks/day free
- **Pro**: $5/user/month — unlimited channels, daily briefings, gap detection
- **Team**: $15/user/month — meeting minutes agent, multi-dashboard export

## Competition

| Tool | What it does | Why Sync-SME wins |
|------|-------------|-------------------|
| Zapier | Connects apps via triggers | No NLP — requires structured input, not chat text |
| Notion AI | Assists within Notion | Doesn't monitor external chat channels |
| Otter.ai | Meeting transcription | No task creation, no chat integration |
| Slack Workflow Builder | Automation within Slack | Limited NLP, no cross-platform, no meeting agent |
| Microsoft Copilot | AI in M365 ecosystem | Locked to MS ecosystem, expensive |

## Tech Stack (MVP — Hackathon)

- **LLM**: 9router.com (unified routing, single API key)
- **Chat**: Discord Bot API (discord.js / discord.py)
- **Tasks**: Plane.so REST API
- **Notes**: Obsidian CLI (`obsidian create/append/daily:append`) — vault at `C:\Users\AbdulHafeez\OneDrive\EMAI`
- **Meetings**: Craig bot (craig.chat) for multi-track recording → Whisper for per-speaker transcription
- **Backend**: Python or Node.js (lightweight, serverless-friendly)
- **Demo**: Video recording (can speed up slow LLM responses)

### Meeting Pipeline Detail
```
Discord voice → Craig /join → multi-track FLAC → Craig REST API download
                                                      ↓
                                              Whisper per-speaker transcribe
                                                      ↓
                                              9router LLM structure minutes
                                                      ↓
                                    ┌─────────────────┴─────────────────┐
                                    ↓                                   ↓
                            Plane.so (tasks)                    Obsidian (minutes)
```

## Gaps Identified
<!-- Populated by challenge sessions -->

- ~~Scope risk~~ → RESOLVED: MVP = Discord + Plane.so + Obsidian, expandable later
- ~~WhatsApp API delays~~ → RESOLVED: Using Discord (instant bot setup)
- ~~Discord voice transcription~~ → RESOLVED: Craig (multi-track recorder) + Whisper (per-speaker transcription)
- ~~Plane.so API~~ → RESOLVED: Prime CLI installed, workspace ready
- ~~Obsidian integration~~ → RESOLVED: Obsidian CLI (obsidian create/append) + direct filesystem fallback
- ~~9router.com~~ → RESOLVED: NVIDIA NIM + Ollama + free providers configured
- Craig free tier: 6 hours recording, 7-day retention — enough for hackathon, self-host later if needed
- **Revenue model** — needs real cost breakdown (Ollama vs API routing split). Current pricing undercooked.
- **Stretch features** — Craig+Whisper+Obsidian clearly labeled in pitch as stretch, not core MVP
- **Gap detection tuning** — confidence threshold needs calibration to avoid false positives

### Challenge Session #1 Result: 5/5 survived
Two killer defenses: "I'm my first user" (eliminates target-user problem) + "stack-agnostic moat" (refuses walled gardens).
