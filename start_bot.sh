#!/bin/bash
# Startup script for scalp-bot with ngrok

# Kill any existing ngrok processes
pkill -9 ngrok 2>/dev/null || killall -9 ngrok 2>/dev/null || true
sleep 2

# Start ngrok in background
ngrok http 8001 </dev/null >/dev/null 2>&1 &
sleep 5

# Start the bot
exec /home/pi/scalp-bot/venv/bin/python3 /home/pi/scalp-bot/main.py
