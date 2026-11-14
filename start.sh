#!/bin/bash
# One-command setup + launch for Kia-bot on macOS.
# First run: builds the Python environment. Every run after: just starts the chat.
cd "$(dirname "$0")"

# Stop early if the API key hasn't been pasted into .env yet
if grep -q "sk-ant-\.\.\." .env; then
  echo "👉 First paste your Anthropic API key into .env (opening it now), save, then rerun: bash start.sh"
  open -e .env
  exit 1
fi

# Build the virtual environment once
if [ ! -d .venv ]; then
  echo "Setting up Python environment (one time, ~1 min)..."
  python3 -m venv .venv || { echo "python3 not found. Install it from python.org, then rerun."; exit 1; }
  .venv/bin/pip install -q --upgrade pip
  .venv/bin/pip install -q -r requirements.txt
  .venv/bin/python -m pytest -q -p no:cacheprovider || exit 1
fi

# Load .env into the environment and start chatting
set -a; source .env; set +a
.venv/bin/python chat.py
