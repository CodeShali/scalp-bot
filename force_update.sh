#!/bin/bash
# Force update script - discards local changes and pulls latest from GitHub
# Run this on Raspberry Pi when git pull fails due to conflicts

echo "🔄 FORCE UPDATE FROM GITHUB"
echo "============================"
echo ""
echo "⚠️  WARNING: This will discard ALL local changes!"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo ""

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Aborted"
    exit 1
fi

cd ~/scalp-bot

echo ""
echo "1️⃣ Fetching latest from GitHub..."
git fetch origin

echo ""
echo "2️⃣ Resetting to match GitHub main branch..."
git reset --hard origin/main

echo ""
echo "3️⃣ Cleaning up any untracked files..."
git clean -fd

echo ""
echo "4️⃣ Verifying we're on main branch..."
git checkout main

echo ""
echo "5️⃣ Current version:"
git log --oneline -1

echo ""
echo "✅ UPDATE COMPLETE!"
echo ""
echo "🔄 Now restart the bot:"
echo "   sudo systemctl restart scalp-bot"
echo ""
echo "📋 Check status:"
echo "   sudo systemctl status scalp-bot"
echo ""
