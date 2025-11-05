# Webhook Setup for Python-Managed Ngrok

Since your bot manages ngrok in Python (port 8001), we have **two simple options**:

---

## 🎯 Option 1: Run Webhook Through Main Bot (EASIEST)

Add webhook endpoint to your existing Flask app - no nginx, no extra ngrok needed!

### Step 1: Add Webhook Route to main.py

Add this code to your `main.py` after the other Flask routes:

```python
# Add at the top with other imports
import hmac
import hashlib

# Add after your other Flask routes (around line 1200)
@app.route('/webhook', methods=['POST'])
def github_webhook():
    """Handle GitHub webhook for auto-deploy."""
    try:
        # Get secret from environment or config
        secret = os.environ.get('WEBHOOK_SECRET', bot.config.get('webhook_secret', ''))
        
        if not secret:
            logger.warning("Webhook secret not configured")
            return jsonify({'error': 'Webhook not configured'}), 500
        
        # Verify signature
        signature = request.headers.get('X-Hub-Signature-256')
        if signature:
            hash_object = hmac.new(
                secret.encode('utf-8'),
                msg=request.data,
                digestmod=hashlib.sha256
            )
            expected_signature = "sha256=" + hash_object.hexdigest()
            
            if not hmac.compare_digest(expected_signature, signature):
                logger.warning("Invalid webhook signature")
                return jsonify({'error': 'Invalid signature'}), 403
        
        # Get event type
        event = request.headers.get('X-GitHub-Event', 'ping')
        
        if event == 'ping':
            logger.info("Received ping from GitHub webhook")
            return jsonify({'message': 'Pong!'}), 200
        
        if event == 'push':
            payload = request.json
            ref = payload.get('ref', '')
            
            # Only deploy on push to main
            if ref == 'refs/heads/main':
                logger.info("Push to main detected - starting auto-deploy")
                
                # Run git pull and restart in background
                def deploy():
                    try:
                        # Git pull
                        result = subprocess.run(
                            ['git', 'pull', 'origin', 'main'],
                            cwd=os.path.dirname(os.path.abspath(__file__)),
                            capture_output=True,
                            text=True,
                            timeout=30
                        )
                        
                        if result.returncode == 0:
                            logger.info(f"Git pull successful: {result.stdout}")
                            
                            # Restart service
                            subprocess.run(
                                ['sudo', 'systemctl', 'restart', 'scalp-bot'],
                                timeout=30
                            )
                            logger.info("Service restart initiated")
                        else:
                            logger.error(f"Git pull failed: {result.stderr}")
                    except Exception as e:
                        logger.error(f"Deploy error: {e}")
                
                # Run in background thread
                import threading
                threading.Thread(target=deploy, daemon=True).start()
                
                return jsonify({'message': 'Deploy started'}), 200
            else:
                return jsonify({'message': 'Ignored - not main branch'}), 200
        
        return jsonify({'message': 'Event received'}), 200
        
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/webhook/health', methods=['GET'])
def webhook_health():
    """Health check for webhook."""
    return jsonify({
        'status': 'healthy',
        'service': 'scalp-bot',
        'webhook': 'enabled'
    }), 200
```

### Step 2: Add Webhook Secret to config.yaml

```yaml
# Add to your config.yaml
webhook_secret: "your-secret-token-here"
```

Generate secret:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

### Step 3: Give Permission to Restart Service

```bash
# SSH to Pi
ssh pi@your-pi-ip

# Edit sudoers
sudo visudo

# Add this line at the end:
pi ALL=(ALL) NOPASSWD: /bin/systemctl restart scalp-bot

# Save and exit (Ctrl+X, Y, Enter)
```

### Step 4: Restart Bot

```bash
sudo systemctl restart scalp-bot
```

### Step 5: Setup GitHub Webhook

Your ngrok URL is already running! Just add webhook:

1. Go to: `https://github.com/CodeShali/scalp-bot/settings/hooks`
2. Click **"Add webhook"**
3. Fill in:
   - **Payload URL**: `https://your-existing-ngrok-url/webhook`
   - **Content type**: `application/json`
   - **Secret**: Your generated token
   - **Events**: "Just the push event"
   - **Active**: ✅
4. Click **"Add webhook"**

### Step 6: Test!

```bash
# Make a change
echo "# Test" >> README.md
git add .
git commit -m "Test auto-deploy"
git push origin main

# Check logs on Pi
ssh pi@your-pi-ip
sudo journalctl -u scalp-bot -f
```

**Done!** ✅ No nginx, no extra ngrok, webhook runs in your existing Flask app!

---

## 🎯 Option 2: Use Nginx + Separate Webhook Service

If you prefer to keep webhook separate:

### Step 1: Install Nginx

```bash
sudo apt-get install nginx
```

### Step 2: Configure Nginx

```bash
sudo nano /etc/nginx/sites-available/tara
```

Add:
```nginx
server {
    listen 80;
    server_name _;
    
    # Main bot (your Python-managed ngrok points here)
    location / {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # Webhook service
    location /webhook {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/tara /etc/nginx/sites-enabled/
sudo rm /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx
```

### Step 3: Update Your Python Ngrok

Edit `main.py` line 116:

```python
# Change from:
["ngrok", "http", "8001", "--host-header", "rewrite"],

# To:
["ngrok", "http", "80", "--host-header", "rewrite"],
```

This makes ngrok point to nginx (port 80) instead of directly to Flask (port 8001).

### Step 4: Setup Webhook Service

Follow the original `AUTO_DEPLOY_SETUP.md` steps 1-2 to setup the webhook service.

### Step 5: Restart Everything

```bash
sudo systemctl restart scalp-bot
sudo systemctl restart webhook
sudo systemctl restart nginx
```

---

## 📊 Comparison

| Feature | Option 1 (Flask) | Option 2 (Nginx) |
|---------|------------------|------------------|
| Setup Time | 5 minutes | 15 minutes |
| Components | Just Flask | Flask + Nginx + Webhook Service |
| Complexity | Simple | More complex |
| Separation | Webhook in main app | Separate webhook service |
| Recommended | ✅ Yes (easier) | If you want separation |

---

## 💡 Recommendation

**Use Option 1** - it's simpler, uses your existing ngrok, and works perfectly!

Just add the webhook route to your Flask app and you're done! 🚀
