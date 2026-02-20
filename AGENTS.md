# Agent Guide – Faceless Shorts Automator MVP

Guidance for AI coding agents (Cursor, Copilot, etc.) working on this codebase.

## Project Overview

**Faceless Shorts Automator** — automated pipeline for faceless YouTube Shorts. Input a topic → output uploaded Short. Flow: **Topic → Gemini (script) → ElevenLabs (voice) → Video assembly → YouTube upload.**

- **Language:** Python 3
- **Run from:** Repo root
- **Main entry:** `python scripts/run_pipeline.py "Topic here"`

## Folder Structure

```
├── config/           # Secrets (.env, client_secrets.json, youtube-oauth.json) — NEVER commit
├── docs/             # Architecture, setup, terminology
├── scripts/          # All executable Python scripts
│   ├── run_pipeline.py   # Full pipeline: topic → Short
│   ├── auth_youtube.py   # One-time OAuth for YouTube
│   └── setup.py          # Validator (folders, keys)
├── workflows/        # Make.com blueprints (optional)
├── output/           # Generated audio + video (gitignored)
├── tests/            # Placeholder; validator = python scripts/setup.py
└── requirements.txt
```

## Key Conventions

1. **Secrets** — All in `config/`. Copy `config/.env.example` → `config/.env`. Never commit `.env`, `client_secrets.json`, or `youtube-oauth.json`. Keys: `GEMINI_API_KEY`, `ELEVENLABS_API_KEY`; optional `ELEVENLABS_VOICE_ID`.

2. **Repo root** — Scripts resolve paths from repo root via `Path(__file__).resolve().parent.parent`. Run commands from repo root.

3. **Python style** — Use type hints; prefer `pathlib.Path`. Log with `[pipeline]` prefix where applicable.

4. **AI disclosure** — Upload description includes: "Script and voice generated with AI."

## Commands

| Command | Purpose |
|---------|---------|
| `pip install -r requirements.txt` | Install deps |
| `python scripts/setup.py` | Validate config and keys |
| `python scripts/auth_youtube.py` | One-time YouTube OAuth (save token) |
| `python scripts/run_pipeline.py "Topic"` | Full pipeline |
| `python scripts/run_pipeline.py "Topic" --no-upload` | Build video only, no upload |

## Important Docs

- `docs/SETUP-API-KEYS.md` — API key setup (never paste keys in README)
- `docs/architecture.md` — Flow, components, quotas
- `docs/BIBLE-OF-TERMS.md` — Video production / AI terminology

## API Dependencies

- **Gemini** — script generation (free tier OK; 429 → fallback script)
- **ElevenLabs** — TTS
- **YouTube Data API v3** — OAuth 2.0 Desktop app; token in `config/`
- **Creatomate / JSON2Video** — video assembly (optional, paid)

## Guardrails for Agents

- Do **not** commit or hardcode secrets (API keys, OAuth tokens).
- Do **not** scope-creep; stay within the requested task.
- Preserve existing fallbacks (Gemini 429, ElevenLabs 401) unless explicitly changing behavior.
- When adding env vars, update `config/.env.example` and `docs/SETUP-API-KEYS.md`.
- Run `python scripts/setup.py` after config changes to validate.

## Handoff

Status updates for handoff: `docs/CLAUDE-CURSOR-HANDOFF.md`.
