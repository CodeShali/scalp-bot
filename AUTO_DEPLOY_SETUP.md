# Auto-Deploy Setup for Raspberry Pi

This guide sets up automatic deployment when you push to GitHub. The bot will automatically pull changes and restart!

## 🎯 How It Works

```
You push to GitHub → GitHub webhook → Raspberry Pi → Auto pull + restart
```

## 📋 Setup Steps

### 1. Generate a Secret Token

```bash
# Generate a random secret token
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Copy the output - you'll need it for both GitHub and the Pi.

### 2. Setup on Raspberry Pi

```bash
# SSH to your Pi
ssh pi@your-pi-ip

# Navigate to repo
cd /path/to/scalp-bot

# Pull latest code (includes webhook_server.py)
git pull origin main

# Make webhook server executable
chmod +x webhook_server.py

# Edit webhook service file with your secret
nano webhook.service

# Replace 'your-secret-token-here' with your generated token
# Replace '/home/pi/scalp-bot' with your actual path if different

# Copy service file
sudo cp webhook.service /etc/systemd/system/

# Give pi user permission to restart scalp-bot service
sudo visudo

# Add this line at the end:
pi ALL=(ALL) NOPASSWD: /bin/systemctl restart scalp-bot

# Save and exit (Ctrl+X, Y, Enter)

# Reload systemd
sudo systemctl daemon-reload

# Enable webhook service
sudo systemctl enable webhook

# Start webhook service
sudo systemctl start webhook

# Check status
sudo systemctl status webhook
```

### 3. Setup Ngrok for Webhook (if not already running)

The webhook server runs on port 5000. You need to expose it:

**Option A: Separate ngrok tunnel**
```bash
# Start ngrok for webhook (in addition to your main bot ngrok)
ngrok http 5000
```

**Option B: Use nginx to proxy both**
```bash
# Install nginx
sudo apt-get install nginx

# Create config
sudo nano /etc/nginx/sites-available/tara

# Add:
server {
    listen 80;
    
    location / {
        proxy_pass http://localhost:8001;  # Main bot
        proxy_set_header Host $host;
    }
    
    location /webhook {
        proxy_pass http://localhost:5000;  # Webhook server
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# Enable site
sudo ln -s /etc/nginx/sites-available/tara /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx

# Then run ngrok on port 80
ngrok http 80
```

### 4. Setup GitHub Webhook

1. Go to your GitHub repo: `https://github.com/CodeShali/scalp-bot`
2. Click **Settings** → **Webhooks** → **Add webhook**
3. Configure:
   - **Payload URL**: `https://your-ngrok-url/webhook`
   - **Content type**: `application/json`
   - **Secret**: Paste your generated token
   - **Events**: Select "Just the push event"
   - **Active**: ✅ Checked
4. Click **Add webhook**

### 5. Test It!

```bash
# On your local machine, make a small change
echo "# Test auto-deploy" >> README.md
git add README.md
git commit -m "Test auto-deploy"
git push origin main

# Watch the logs on Pi
ssh pi@your-pi-ip
tail -f /path/to/scalp-bot/webhook.log

# You should see:
# - "Push event received"
# - "Pulling latest changes"
# - "Service restarted successfully"
```

## 📊 Monitoring

### Check Webhook Service Status
```bash
sudo systemctl status webhook
```

### View Webhook Logs
```bash
tail -f /path/to/scalp-bot/webhook.log
```

### View Bot Logs
```bash
sudo journalctl -u scalp-bot -f
```

### Test Webhook Endpoint
```bash
curl https://your-ngrok-url/webhook/health
```

## 🔧 Troubleshooting

### Webhook not triggering?
1. Check GitHub webhook delivery status (Settings → Webhooks → Recent Deliveries)
2. Verify ngrok is running: `curl https://your-ngrok-url/webhook/health`
3. Check webhook logs: `tail -f webhook.log`

### Git pull fails?
```bash
# Make sure git is configured
cd /path/to/scalp-bot
git config pull.rebase false
```

### Service restart fails?
```bash
# Verify sudo permissions
sudo -l | grep scalp-bot

# Should show:
# pi ALL=(ALL) NOPASSWD: /bin/systemctl restart scalp-bot
```

### Port 5000 already in use?
```bash
# Check what's using port 5000
sudo lsof -i :5000

# Kill it or change webhook port in webhook_server.py
```

## 🎉 Success!

Once setup, every time you:
```bash
git push origin main
```

Your Raspberry Pi will automatically:
1. ✅ Receive webhook from GitHub
2. ✅ Pull latest code
3. ✅ Restart the bot
4. ✅ Log everything

**No manual SSH needed!** 🚀

## 🔒 Security Notes

- Keep your webhook secret token safe
- Never commit the secret to git
- Use environment variables for secrets
- GitHub webhook is signed and verified
- Only responds to pushes to main branch

## 📝 Logs Location

- Webhook logs: `/path/to/scalp-bot/webhook.log`
- Bot logs: `sudo journalctl -u scalp-bot`
- Webhook service: `sudo journalctl -u webhook`
