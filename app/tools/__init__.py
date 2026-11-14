"""Tool registry. To add a new ability: write a module with TOOL_SPEC + run(), then add it here."""
from . import calendar, surf

TOOLS = {m.TOOL_SPEC["name"]: m for m in (surf, calendar)}
SPECS = [m.TOOL_SPEC for m in TOOLS.values()]


def call(name: str, args: dict):
    if name not in TOOLS:
        return {"error": f"unknown tool {name}"}
    try:
        return TOOLS[name].run(**args)
    except Exception as e:  # report errors to the model so it can explain them out loud
        return {"error": str(e)}
