"""Web server: the Siri Shortcut (and anything else) POSTs here."""
import os
import secrets

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel

from .agent import ask

app = FastAPI(title="Kia-bot")
TOKEN = os.getenv("KIA_BOT_TOKEN", "")


def check_auth(authorization: str = Header(default="")):
    # Simple bearer token so only your phone/laptop can use your agent (and your API credits)
    if not TOKEN:
        raise HTTPException(500, "Server missing KIA_BOT_TOKEN")
    if not secrets.compare_digest(authorization, f"Bearer {TOKEN}"):
        raise HTTPException(401, "Bad token")


class Ask(BaseModel):
    text: str


@app.get("/health")
def health():
    return {"ok": True}


@app.post("/ask", dependencies=[Depends(check_auth)])
def ask_endpoint(body: Ask):
    reply, _ = ask(body.text)  # stateless per request: each Siri question stands alone
    return {"reply": reply}
