# Kia-bot 🌊

A personal voice AI agent. Ask it out loud in the car ("Hey Siri, Kia bot") or chat on your laptop. Claude decides which live-data tools to call, then answers in one or two spoken sentences.

```
iPhone (Siri Shortcut) ─┐
                        ├─► FastAPI /ask ─► Claude (tool use) ─► tools/ ─► Open-Meteo, NOAA, Google Calendar
Laptop (chat.py) ───────┘
```

**Current tools**
| Tool | Source | Example question |
|---|---|---|
| `get_surf_forecast` | Open-Meteo marine + wind, NOAA Scripps Pier tides | "How's the surf tomorrow morning?" |
| `get_calendar` | Google Calendar (read-only) | "When am I free Friday to surf?" |

## 1. Run it on your laptop (~10 min)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # add ANTHROPIC_API_KEY (console.anthropic.com) and a KIA_BOT_TOKEN
set -a; source .env; set +a
python chat.py                # surf works right away
pytest -q                     # offline tests
```

## 2. Connect Google Calendar (~10 min, one time)

1. Google Cloud Console → new project → enable **Google Calendar API**.
2. OAuth consent screen → External → add yourself as a test user.
3. Credentials → Create OAuth client ID → **Desktop app** → download as `credentials.json` into this folder.
4. `python scripts/google_auth.py` → log in → creates `token.json`.

Access is read-only. `token.json` and `credentials.json` are gitignored, so never commit them.

> Note: while the Google app is in "Testing" mode, tokens can expire after about 7 days. If calendar stops working, either rerun step 4 or publish the app (it's fine for personal use).

## 3. Put it online (~15 min)

Your phone needs a public URL. Easiest path is Railway or Render:
1. Push this repo to GitHub (secrets stay out because of `.gitignore`).
2. New project from the repo. The `Procfile` sets the start command.
3. Add env vars: `ANTHROPIC_API_KEY`, `KIA_BOT_TOKEN`, `GOOGLE_TOKEN_JSON` (paste the contents of `token.json`).
4. Test it:
   ```bash
   curl -X POST https://YOUR-APP/ask -H "Authorization: Bearer $KIA_BOT_TOKEN" \
        -H "Content-Type: application/json" -d '{"text":"surf tomorrow?"}'
   ```

Free tiers that "sleep" add a 30–60 s delay on the first request, which feels bad for voice. A small always-on plan (around $5/mo, check current pricing) fixes that.

## 4. Siri Shortcut (talk to it from the car)

In the **Shortcuts** app → **+** → add these actions in order:
1. **Dictate Text** (Stop Listening: After Pause)
2. **Get Contents of URL**
   - URL: `https://YOUR-APP/ask`, Method: **POST**
   - Headers: `Authorization` = `Bearer YOUR_TOKEN`
   - Request Body: **JSON**, key `text` = *Dictated Text*
3. **Get Dictionary Value** → key `reply` from *Contents of URL*
4. **Speak Text** → *Dictionary Value*

Name the shortcut **Kia bot**. In the car, with the phone on the Tesla's Bluetooth: *"Hey Siri, Kia bot"* → ask your question → it answers through the car speakers.

## 5. Add a new tool

1. Create `app/tools/<name>.py` with a `TOOL_SPEC` dict (name, description, input_schema) and a `run(**args)` function that returns a dict.
2. Register it in `app/tools/__init__.py`.
3. Add a test in `tests/`.

Next on the roadmap: stock debrief, workout logger (SQLite), Tesla Fleet API (precondition, charge level), and a surf-quality ML model trained on your own session ratings.

## Resume blurb

> **Kia-bot: Personal Voice AI Agent** (Python, FastAPI, Claude API, Google Calendar API)
> Built a voice-driven LLM agent that uses tool calling to answer real-time questions about surf conditions, tides, and schedule, accessible hands-free via an iOS Shortcut. Designed a pluggable tool registry, token-authenticated API, and offline test suite with mocked external services.
