#!/bin/bash
# Debug script to check ngrok configuration on Raspberry Pi

echo "=========================================="
echo "ngrok Diagnostic Script"
echo "=========================================="
echo ""

echo "1️⃣  Checking if ngrok is installed..."
if command -v ngrok &> /dev/null; then
    NGROK_PATH=$(which ngrok)
    echo "✅ ngrok found at: $NGROK_PATH"
else
    echo "❌ ngrok not found in PATH"
    exit 1
fi

echo ""
echo "2️⃣  Checking ngrok version..."
ngrok version

echo ""
echo "3️⃣  Checking ngrok config..."
if [ -f ~/.config/ngrok/ngrok.yml ]; then
    echo "✅ Config found at: ~/.config/ngrok/ngrok.yml"
    echo "Authtoken configured: $(grep -q 'authtoken:' ~/.config/ngrok/ngrok.yml && echo 'Yes' || echo 'No')"
elif [ -f /root/.config/ngrok/ngrok.yml ]; then
    echo "✅ Config found at: /root/.config/ngrok/ngrok.yml (root)"
    sudo grep -q 'authtoken:' /root/.config/ngrok/ngrok.yml && echo "Authtoken configured: Yes" || echo "Authtoken configured: No"
else
    echo "❌ No ngrok config found"
    echo "Run: ngrok config add-authtoken YOUR_TOKEN"
fi

echo ""
echo "4️⃣  Testing ngrok manually..."
echo "Starting ngrok for 5 seconds..."
timeout 5 ngrok http 8001 > /tmp/ngrok_test.log 2>&1 &
NGROK_PID=$!
sleep 5

if ps -p $NGROK_PID > /dev/null 2>&1; then
    echo "✅ ngrok process is running (PID: $NGROK_PID)"
    kill $NGROK_PID 2>/dev/null
else
    echo "❌ ngrok process exited immediately"
    echo ""
    echo "Error output:"
    cat /tmp/ngrok_test.log
fi

echo ""
echo "5️⃣  Checking ngrok service status..."
sudo systemctl status ngrok --no-pager -l

echo ""
echo "6️⃣  Checking ngrok service logs..."
echo "Last 20 lines:"
sudo journalctl -u ngrok -n 20 --no-pager

echo ""
echo "=========================================="
echo "Diagnostic complete!"
echo "=========================================="
