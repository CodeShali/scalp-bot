# 🚀 Auto-Deploy Quickstart (5 Minutes)

Webhook endpoint is now built into your Flask app! Just 3 steps to enable auto-deploy.

---

## Step 1: Generate Secret Token

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Copy the output (e.g., `a1b2c3d4e5f6...`)

---

## Step 2: Add to config.yaml on Pi

```bash
# SSH to your Pi
ssh pi@your-pi-ip

# Edit config
nano /path/to/scalp-bot/config.yaml

# Add this line anywhere in the file:
webhook_secret: "paste-your-token-here"

# Save (Ctrl+X, Y, Enter)
```

---

## Step 3: Give Restart Permission

```bash
# Still on Pi
sudo visudo

# Add this line at the end:
pi ALL=(ALL) NOPASSWD: /bin/systemctl restart scalp-bot

# Save and exit (Ctrl+X, Y, Enter)
```

---

## Step 4: Pull Code and Restart

```bash
# Pull latest code (includes webhook endpoint)
cd /path/to/scalp-bot
git pull origin main

# Restart bot
sudo systemctl restart scalp-bot

# Check it's running
sudo systemctl status scalp-bot
```

---

## Step 5: Test Webhook

```bash
# Test health endpoint
curl https://your-ngrok-url/webhook/health

# Should return:
# {"status":"healthy","service":"scalp-bot","webhook":"enabled","ngrok_url":"https://..."}
```

---

## Step 6: Setup GitHub Webhook

1. Go to: https://github.com/CodeShali/scalp-bot/settings/hooks
2. Click **"Add webhook"**
3. Fill in:
   - **Payload URL**: `https://your-ngrok-url/webhook`
   - **Content type**: `application/json`
   - **Secret**: Paste your generated token from Step 1
   - **Events**: Select "Just the push event"
   - **Active**: ✅ Check this box
4. Click **"Add webhook"**
5. GitHub will send a ping - check "Recent Deliveries" to see if it succeeded

---

## Step 7: Test Auto-Deploy! 🎉

```bash
# On your local machine
cd /path/to/scalp-bot
echo "# Test auto-deploy" >> README.md
git add README.md
git commit -m "Test auto-deploy"
git push origin main

# Watch Discord for notifications!
# You should see:
# 🔄 Auto-Deploy Started
# ✅ Code Updated
# 🎉 Auto-Deploy Complete
```

---

## ✅ Done!

Now every time you push to main:
1. GitHub sends webhook to your ngrok URL
2. Your Flask app receives it
3. Verifies signature
4. Pulls latest code
5. Restarts service
6. Sends Discord notifications

**No SSH needed!** 🚀

---

## 🔍 Troubleshooting

### Webhook not working?

**Check logs:**
```bash
sudo journalctl -u scalp-bot -f
```

**Check GitHub webhook deliveries:**
1. Go to: https://github.com/CodeShali/scalp-bot/settings/hooks
2. Click on your webhook
3. Click "Recent Deliveries"
4. Click on a delivery to see request/response

**Common issues:**
- ❌ Secret mismatch: Make sure token in config.yaml matches GitHub
- ❌ Permission denied: Run `sudo visudo` and add the line
- ❌ Ngrok URL wrong: Use your actual ngrok URL from bot logs

### Test webhook manually:

```bash
# Generate test signature
SECRET="your-secret-here"
PAYLOAD='{"ref":"refs/heads/main","commits":[],"pusher":{"name":"test"}}'
SIGNATURE=$(echo -n "$PAYLOAD" | openssl dgst -sha256 -hmac "$SECRET" | sed 's/^.* //')

# Send test webhook
curl -X POST https://your-ngrok-url/webhook \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: push" \
  -H "X-Hub-Signature-256: sha256=$SIGNATURE" \
  -d "$PAYLOAD"
```

---

## 📊 What You Get

- ✅ Auto-deploy on every push
- ✅ Discord notifications for each step
- ✅ Secure signature verification
- ✅ Only deploys main branch
- ✅ Background deployment (no blocking)
- ✅ Full logging

---

## 🎯 Endpoints

- **Webhook**: `https://your-ngrok-url/webhook` (POST)
- **Health**: `https://your-ngrok-url/webhook/health` (GET)
- **Dashboard**: `https://your-ngrok-url/` (GET)

All running through your existing ngrok tunnel! 🎉
