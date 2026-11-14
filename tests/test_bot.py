"""Offline tests: external APIs and Claude are mocked, so these run without keys."""
from datetime import datetime
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from fastapi.testclient import TestClient

from app import agent, tools
from app.tools import calendar, surf

TZ = ZoneInfo("America/Los_Angeles")


def test_surf_parses_and_filters(monkeypatch):
    times = [f"2026-10-14T{h:02d}:00" for h in range(24)]
    monkeypatch.setattr(surf, "_fetch_waves", lambda d: {
        "time": times, "wave_height": [1.0] * 24, "swell_wave_height": [0.8] * 24,
        "swell_wave_period": [12] * 24, "swell_wave_direction": [270] * 24})
    monkeypatch.setattr(surf, "_fetch_wind", lambda d: {
        "wind_speed_10m": [10.0] * 24, "wind_direction_10m": [90] * 24, "temperature_2m": [20.0] * 24})
    monkeypatch.setattr(surf, "_fetch_tides", lambda d: [{"time": "2026-10-14 06:12", "type": "low", "ft": 0.4}])

    out = surf.run()
    assert all(5 <= int(h["time"][11:13]) <= 19 for h in out["hourly"])  # daylight only
    first = out["hourly"][0]
    assert first["wave_ft"] == 3.3 and first["wind"] == "offshore" and first["air_f"] == 68
    assert out["tides"][0]["type"] == "low"


def test_free_gaps():
    day = datetime(2026, 10, 14, tzinfo=TZ)
    events = [{"start": "2026-10-14T09:00:00-07:00", "end": "2026-10-14T17:00:00-07:00"}]
    gaps = calendar._free_gaps(events, day.replace(hour=6), day.replace(hour=21))
    assert gaps == ["Wed 06:00AM-09:00AM", "Wed 05:00PM-09:00PM"]


def test_tool_errors_are_returned_not_raised(monkeypatch):
    def boom(**_):
        raise RuntimeError("no calendar")
    monkeypatch.setattr(calendar, "run", boom)
    assert tools.call("get_calendar", {}) == {"error": "no calendar"}


def test_agent_loop_runs_tool_then_answers(monkeypatch):
    # Fake Claude: first asks for the surf tool, then answers
    calls = []
    replies = iter([
        SimpleNamespace(stop_reason="tool_use", content=[
            SimpleNamespace(type="tool_use", id="t1", name="get_surf_forecast", input={})]),
        SimpleNamespace(stop_reason="end_turn", content=[
            SimpleNamespace(type="text", text="3 to 4 feet and clean at 7 AM.")]),
    ])
    fake = SimpleNamespace(messages=SimpleNamespace(create=lambda **kw: calls.append(kw) or next(replies)))
    monkeypatch.setattr(agent, "_client", fake)
    monkeypatch.setattr(tools, "call", lambda n, a: {"spot": "La Jolla Shores"})

    reply, history = agent.ask("how's the surf?")
    assert reply == "3 to 4 feet and clean at 7 AM."
    assert len(calls) == 2 and history[2]["content"][0]["tool_use_id"] == "t1"


def test_api_requires_token(monkeypatch):
    from app import main
    monkeypatch.setattr(main, "TOKEN", "secret")
    monkeypatch.setattr(main, "ask", lambda t: ("hi", []))
    c = TestClient(main.app)
    assert c.post("/ask", json={"text": "yo"}).status_code == 401
    r = c.post("/ask", json={"text": "yo"}, headers={"Authorization": "Bearer secret"})
    assert r.json() == {"reply": "hi"}
