"""Laptop chat: talk to Kia-bot in your terminal, with memory within the session.

Usage: python chat.py   (type 'quit' to exit)
"""
from app.agent import ask

history = []
print("Kia-bot ready. Ask about surf, your calendar, or plans. ('quit' to exit)\n")
while True:
    try:
        text = input("you > ").strip()
    except (EOFError, KeyboardInterrupt):
        break
    if text.lower() in {"quit", "exit"}:
        break
    if not text:
        continue
    reply, history = ask(text, history)  # pass history so follow-ups make sense
    print(f"bot > {reply}\n")
