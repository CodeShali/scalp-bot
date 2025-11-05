# Simple Webhook Setup (Using Your Existing Ngrok)

Since you already have ngrok running on port 8001, we'll use nginx to route both your dashboard AND webhook through the same ngrok tunnel!

## 🎯 Architecture

```
GitHub → ngrok URL → nginx (port 80) → {
    /          → bot dashboard (port 8001)
    /webhook   → webhook server (port 5000)
}
```

**One ngrok tunnel, two services!**

---

## 📋 Quick Setup (15 minutes)

### Step 1: Generate Secret Token

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

Copy the output - you'll need it later.

---

### Step 2: Setup on Raspberry Pi

```bash
# SSH to your Pi
ssh pi@your-pi-ip

# Go to repo
cd /path/to/scalp-bot

# Pull latest code
git pull origin main

# Edit webhook.service with your secret and correct path
nano webhook.service

# Change these lines:
# WorkingDirectory=/home/pi/scalp-bot  (use your actual path)
# Environment="WEBHOOK_SECRET=paste-your-token-here"
# ExecStart=/usr/bin/python3 /home/pi/scalp-bot/webhook_server.py

# Save (Ctrl+X, Y, Enter)

# Install webhook service
sudo cp webhook.service /etc/systemd/system/

# Give pi user permission to restart bot
sudo visudo

# Add this line at the end:
pi ALL=(ALL) NOPASSWD: /bin/systemctl restart scalp-bot

# Save and exit (Ctrl+X, Y, Enter)

# Start webhook service
sudo systemctl daemon-reload
sudo systemctl enable webhook
sudo systemctl start webhook

# Check it's running
sudo systemctl status webhook
```

---

### Step 3: Install and Configure Nginx

```bash
# Install nginx
sudo apt-get update
sudo apt-get install nginx -y

# Create nginx config
sudo nano /etc/nginx/sites-available/tara

# Paste this (adjust port 8001 if your bot uses different port):
```

```nginx
server {
    listen 80;
    server_name _;
    
    # Dashboard (your existing bot)
    location / {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    # Webhook endpoint
    location /webhook {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# Enable the site
sudo ln -s /etc/nginx/sites-available/tara /etc/nginx/sites-enabled/

# Remove default site
sudo rm /etc/nginx/sites-enabled/default

# Test nginx config
sudo nginx -t

# Should say: "syntax is ok" and "test is successful"

# Restart nginx
sudo systemctl restart nginx

# Enable nginx on boot
sudo systemctl enable nginx
```

---

### Step 4: Update Your Ngrok

```bash
# Stop your current ngrok
# (Press Ctrl+C in the terminal where ngrok is running)

# Start ngrok on port 80 instead of 8001
ngrok http 80
```

**Copy the new ngrok URL** (e.g., `https://abc123.ngrok-free.app`)

---

### Step 5: Test Everything Works

```bash
# Test dashboard (should work as before)
curl https://your-ngrok-url/

# Test webhook health endpoint
curl https://your-ngrok-url/webhook/health

# Should return:
# {"status":"healthy","service":"scalp-bot","repo_path":"/path/to/scalp-bot"}
```

---

### Step 6: Setup GitHub Webhook

1. Go to: `https://github.com/CodeShali/scalp-bot/settings/hooks`
2. Click **"Add webhook"**
3. Fill in:
   - **Payload URL**: `https://your-ngrok-url/webhook`
   - **Content type**: `application/json`
   - **Secret**: Paste your generated token from Step 1
   - **Which events**: Select "Just the push event"
   - **Active**: ✅ Check this box
4. Click **"Add webhook"**

---

### Step 7: Test Auto-Deploy!

```bash
# On your local machine
cd /path/to/scalp-bot
echo "# Test auto-deploy" >> README.md
git add README.md
git commit -m "Test auto-deploy"
git push origin main

# Watch the magic happen on Pi!
ssh pi@your-pi-ip
tail -f /path/to/scalp-bot/webhook.log

# You should see:
# [INFO] Push event received from <your-name>
# [INFO] Pulling latest changes from git...
# [INFO] Git pull successful
# [INFO] Restarting scalp-bot service...
# [INFO] Service scalp-bot restarted successfully
# [INFO] Auto-deploy completed successfully!
```

---

## ✅ What You Now Have

- ✅ Dashboard: `https://your-ngrok-url/`
- ✅ Webhook: `https://your-ngrok-url/webhook`
- ✅ One ngrok tunnel for both
- ✅ Auto-deploy on every push to main

---

## 🔧 Troubleshooting

### Dashboard not loading?
```bash
# Check bot is running
sudo systemctl status scalp-bot

# Check nginx
sudo systemctl status nginx

# Check nginx logs
sudo tail -f /var/log/nginx/error.log
```

### Webhook not working?
```bash
# Check webhook service
sudo systemctl status webhook

# Check webhook logs
tail -f /path/to/scalp-bot/webhook.log

# Test webhook directly
curl http://localhost:5000/webhook/health
```

### GitHub webhook failing?
1. Go to GitHub webhook settings
2. Click on your webhook
3. Scroll to "Recent Deliveries"
4. Click on a delivery to see the error
5. Check the response

### Nginx errors?
```bash
# Test config
sudo nginx -t

# Restart nginx
sudo systemctl restart nginx

# Check logs
sudo tail -f /var/log/nginx/error.log
```

---

## 📊 Monitoring

### View all logs in real-time:
```bash
# Terminal 1: Webhook logs
tail -f /path/to/scalp-bot/webhook.log

# Terminal 2: Bot logs
sudo journalctl -u scalp-bot -f

# Terminal 3: Nginx logs
sudo tail -f /var/log/nginx/access.log
```

---

## 🎉 Done!

Now every time you push to GitHub:
1. ✅ GitHub sends webhook to your ngrok URL
2. ✅ Nginx routes to webhook server
3. ✅ Webhook server pulls latest code
4. ✅ Webhook server restarts bot
5. ✅ Your changes are live!

**No manual SSH needed!** 🚀

---

## 💡 Pro Tips

### Make ngrok persistent
```bash
# Install ngrok as a service
sudo nano /etc/systemd/system/ngrok.service

# Add:
[Unit]
Description=Ngrok
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi
ExecStart=/usr/local/bin/ngrok http 80
Restart=always

[Install]
WantedBy=multi-user.target

# Enable and start
sudo systemctl enable ngrok
sudo systemctl start ngrok
```

### View ngrok URL without terminal
```bash
# Get ngrok URL via API
curl http://localhost:4040/api/tunnels | jq -r '.tunnels[0].public_url'
```

### Auto-update GitHub webhook URL
If your ngrok URL changes, you'll need to update GitHub webhook manually, or use ngrok's paid plan for a fixed domain.
