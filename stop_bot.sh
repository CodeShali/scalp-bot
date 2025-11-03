#!/bin/bash
# Stop script for scalp-bot - kills ngrok

pkill -9 ngrok 2>/dev/null || killall -9 ngrok 2>/dev/null || true
