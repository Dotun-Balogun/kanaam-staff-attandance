#!/usr/bin/env bash
# Starts the system. Open http://localhost:8000 afterwards.
cd "$(dirname "$0")/backend"
sudo systemctl stop fprintd 2>/dev/null   # frees the scanner for our app
exec python3 -m uvicorn main:app --host 127.0.0.1 --port 8000
