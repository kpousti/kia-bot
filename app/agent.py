"""The agent loop: Claude decides which tools to call, we run them, Claude answers."""
import json
import os
from datetime import datetime
from zoneinfo import ZoneInfo

import anthropic

from . import tools

MODEL = os.getenv("KIA_BOT_MODEL", "claude-sonnet-5-5")
MAX_STEPS = 6  # safety cap on tool round-trips per question

# Personal context stays out of the code: set KIA_BOT_ABOUT in .env (kept out of git).
ABOUT = os.getenv("KIA_BOT_ABOUT", "Kia surfs in San Diego.")

SYSTEM = """You are Kia-bot, Kia's personal assistant. {about}

Your answers are often SPOKEN ALOUD while Kia drives, so:
- Answer in 1-3 short sentences. Lead with the answer.
- No markdown, lists, emojis, or URLs. Say times like "7 AM", heights like "3 to 4 feet".
- Use tools whenever the question needs live data; never guess conditions or events.
- If a tool errors, say briefly what's not working.
Current time: {now}"""

_client = None


def _get_client():
    # Lazy init so tests can run without an API key
    global _client
    if _client is None:
        _client = anthropic.Anthropic()
    return _client


def ask(text: str, history: list | None = None) -> tuple[str, list]:
    """Answer one message. Returns (reply, updated history) so the CLI can keep context."""
    messages = list(history or []) + [{"role": "user", "content": text}]
    now = datetime.now(ZoneInfo("America/Los_Angeles")).strftime("%A %B %d, %Y %I:%M %p")

    for _ in range(MAX_STEPS):
        resp = _get_client().messages.create(
            model=MODEL, max_tokens=600, system=SYSTEM.format(now=now, about=ABOUT),
            tools=tools.SPECS, messages=messages,
        )
        messages.append({"role": "assistant", "content": resp.content})

        if resp.stop_reason != "tool_use":
            reply = "".join(b.text for b in resp.content if b.type == "text").strip()
            return reply, messages

        # Run every tool Claude asked for and send the results back
        results = [{
            "type": "tool_result", "tool_use_id": b.id,
            "content": json.dumps(tools.call(b.name, b.input), default=str),
        } for b in resp.content if b.type == "tool_use"]
        messages.append({"role": "user", "content": results})

    return "Sorry, that took too many steps. Try asking more simply.", messages
