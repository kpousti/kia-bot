"""Calendar tool: read-only access to Kia's Google Calendar."""
import json
import os
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/Los_Angeles")
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]  # read-only on purpose

TOOL_SPEC = {
    "name": "get_calendar",
    "description": (
        "List Kia's Google Calendar events between two dates, including free gaps. "
        "Use for 'what's on today', 'when am I free', or planning around surf/gym."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "start_date": {"type": "string", "description": "YYYY-MM-DD, default today"},
            "end_date": {"type": "string", "description": "YYYY-MM-DD inclusive, default same as start"},
        },
    },
}


def _service():
    from google.oauth2.credentials import Credentials
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build

    # Token comes from env (for cloud hosting) or a local file made by scripts/google_auth.py
    raw = os.getenv("GOOGLE_TOKEN_JSON")
    if raw:
        info = json.loads(raw)
    elif os.path.exists("token.json"):
        with open("token.json") as f:
            info = json.load(f)
    else:
        raise RuntimeError("Google Calendar not connected. Run: python scripts/google_auth.py")
    creds = Credentials.from_authorized_user_info(info, SCOPES)
    if not creds.valid:
        creds.refresh(Request())  # refresh token keeps it working long-term
    return build("calendar", "v3", credentials=creds, cache_discovery=False)


def _free_gaps(events: list[dict], day_start: datetime, day_end: datetime) -> list[str]:
    # Walk through timed events in order and record gaps of 60+ minutes
    gaps, cursor = [], day_start
    for e in sorted((e for e in events if "T" in e["start"]), key=lambda e: e["start"]):
        s, end = datetime.fromisoformat(e["start"]), datetime.fromisoformat(e["end"])
        if (s - cursor) >= timedelta(minutes=60):
            gaps.append(f"{cursor:%a %I:%M%p}-{s:%I:%M%p}")
        cursor = max(cursor, end)
    if (day_end - cursor) >= timedelta(minutes=60):
        gaps.append(f"{cursor:%a %I:%M%p}-{day_end:%I:%M%p}")
    return gaps


def run(start_date: str | None = None, end_date: str | None = None) -> dict:
    today = datetime.now(TZ).date()
    start = datetime.fromisoformat(start_date).date() if start_date else today
    end = datetime.fromisoformat(end_date).date() if end_date else start
    t_min = datetime.combine(start, datetime.min.time(), TZ)
    t_max = datetime.combine(end + timedelta(days=1), datetime.min.time(), TZ)

    items = _service().events().list(
        calendarId="primary", timeMin=t_min.isoformat(), timeMax=t_max.isoformat(),
        singleEvents=True, orderBy="startTime", maxResults=50,
    ).execute().get("items", [])

    events = [{
        "title": e.get("summary", "(busy)"),
        "start": e["start"].get("dateTime", e["start"].get("date")),
        "end": e["end"].get("dateTime", e["end"].get("date")),
    } for e in items]

    # Free windows per day, counted from 6am to 9pm
    gaps = []
    d = start
    while d <= end:
        day_events = [e for e in events if e["start"].startswith(d.isoformat())]
        gaps += _free_gaps(day_events,
                           datetime.combine(d, datetime.min.time(), TZ).replace(hour=6),
                           datetime.combine(d, datetime.min.time(), TZ).replace(hour=21))
        d += timedelta(days=1)
    return {"events": events, "free_windows": gaps}
