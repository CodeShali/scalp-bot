#!/bin/bash
# Replace YOUR_USERNAME with your actual GitHub username
# Example: If your username is "shashank123", replace YOUR_USERNAME with shashank123

echo "Enter your GitHub username:"
read USERNAME

git remote add origin https://github.com/$USERNAME/scalp-bot.git
git branch -M main
git push -u origin main

echo ""
echo "✓ Done! Check: https://github.com/$USERNAME/scalp-bot"
