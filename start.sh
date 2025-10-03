#!/usr/bin/env bash
set -e

# Load .env if present
if [ -f ".env" ]; then
  export $(grep -v '^#' .env | xargs)
fi

exec python -u bot.py
