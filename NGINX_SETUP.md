# Nginx Reverse Proxy Setup (Free Alternative to Ngrok)

Replace ngrok with nginx + port forwarding for unlimited requests!

---

## 🎯 **What You'll Get:**

- ✅ **Unlimited requests** (no rate limits!)
- ✅ **Free forever** (no monthly fees)
- ✅ **Your own domain** (looks professional)
- ✅ **HTTPS/SSL** (secure connection)
- ✅ **Faster** (no ngrok overhead)

---

## 📋 **Prerequisites:**

1. **Router access** (to set up port forwarding)
2. **Static IP or Dynamic DNS** (free options available)
3. **Domain name** (optional, can use DuckDNS for free)

---

## 🚀 **Step 1: Install Nginx**

```bash
# Install nginx
sudo apt update
sudo apt install nginx -y

# Start nginx
sudo systemctl start nginx
sudo systemctl enable nginx

# Check status
sudo systemctl status nginx
```

---

## 🔧 **Step 2: Configure Nginx**

Create nginx config for the bot:

```bash
sudo nano /etc/nginx/sites-available/scalp-bot
```

**Add this configuration:**

```nginx
server {
    listen 80;
    server_name your-domain.com;  # Change this to your domain
    
    # Increase timeout for long-running requests
    proxy_read_timeout 300;
    proxy_connect_timeout 300;
    proxy_send_timeout 300;
    
    # Bot dashboard
    location / {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
    
    # GitHub webhook endpoint
    location /webhook {
        proxy_pass http://localhost:8001/webhook;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

**Enable the site:**

```bash
# Create symbolic link
sudo ln -s /etc/nginx/sites-available/scalp-bot /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

---

## 🌐 **Step 3: Get a Free Domain (DuckDNS)**

If you don't have a domain, use DuckDNS (free dynamic DNS):

### **3.1: Sign up for DuckDNS**

1. Go to https://www.duckdns.org
2. Sign in with Google/GitHub
3. Create a subdomain: `yourbot.duckdns.org`
4. Copy your token

### **3.2: Install DuckDNS updater**

```bash
# Create directory
mkdir ~/duckdns
cd ~/duckdns

# Create update script
nano duck.sh
```

**Add this (replace TOKEN and DOMAIN):**

```bash
#!/bin/bash
echo url="https://www.duckdns.org/update?domains=YOUR_DOMAIN&token=YOUR_TOKEN&ip=" | curl -k -o ~/duckdns/duck.log -K -
```

**Make executable and set up cron:**

```bash
chmod +x duck.sh

# Test it
./duck.sh
cat duck.log  # Should show "OK"

# Add to crontab (updates every 5 minutes)
crontab -e

# Add this line:
*/5 * * * * ~/duckdns/duck.sh >/dev/null 2>&1
```

---

## 🔌 **Step 4: Port Forwarding**

Forward port 80 (HTTP) and 443 (HTTPS) to your server:

### **4.1: Find your server's local IP**

```bash
hostname -I
# Example output: 192.168.1.100
```

### **4.2: Set up port forwarding on router**

1. Open router admin panel (usually http://192.168.1.1)
2. Find "Port Forwarding" or "Virtual Server"
3. Add these rules:

```
External Port: 80
Internal IP: 192.168.1.100 (your server)
Internal Port: 80
Protocol: TCP

External Port: 443
Internal IP: 192.168.1.100
Internal Port: 443
Protocol: TCP
```

---

## 🔒 **Step 5: Add SSL/HTTPS (Free with Let's Encrypt)**

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx -y

# Get SSL certificate (replace with your domain)
sudo certbot --nginx -d yourbot.duckdns.org

# Follow prompts:
# - Enter email
# - Agree to terms
# - Choose redirect HTTP to HTTPS (option 2)

# Auto-renewal is set up automatically
# Test renewal:
sudo certbot renew --dry-run
```

**Nginx will be automatically updated with SSL!**

---

## ⚙️ **Step 6: Update Bot Configuration**

```bash
nano ~/scalp-bot/config.yaml
```

**Change these settings:**

```yaml
# Disable ngrok
use_ngrok: false

# Set your custom URL
custom_url: "https://yourbot.duckdns.org"  # Use your domain
```

**Restart the bot:**

```bash
sudo systemctl restart scalp-bot
```

---

## 🧪 **Step 7: Test Everything**

### **7.1: Test local access**

```bash
curl http://localhost:8001
# Should return HTML
```

### **7.2: Test nginx**

```bash
curl http://localhost
# Should return HTML
```

### **7.3: Test external access**

From another device or phone:
```
https://yourbot.duckdns.org
```

Should show your dashboard!

### **7.4: Test webhook**

```bash
# Update GitHub webhook URL to:
https://yourbot.duckdns.org/webhook

# Test with a commit:
git commit --allow-empty -m "Test webhook"
git push origin main
```

---

## 📊 **Comparison:**

| Feature | Ngrok Free | Nginx + DuckDNS |
|---------|-----------|-----------------|
| **Cost** | Free | Free |
| **Rate Limit** | 40 req/min ❌ | Unlimited ✅ |
| **Custom Domain** | No | Yes ✅ |
| **SSL/HTTPS** | Yes | Yes ✅ |
| **Persistent URL** | Changes | Fixed ✅ |
| **Speed** | Slower | Faster ✅ |
| **Setup** | Easy | Medium |

---

## 🔧 **Troubleshooting:**

### **Can't access from outside:**

```bash
# Check nginx is running
sudo systemctl status nginx

# Check firewall
sudo ufw status
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Check port forwarding
# Use https://www.yougetsignal.com/tools/open-ports/
# Enter your public IP and port 80
```

### **SSL certificate issues:**

```bash
# Check certificate
sudo certbot certificates

# Renew manually
sudo certbot renew

# Check nginx config
sudo nginx -t
```

### **DuckDNS not updating:**

```bash
# Check log
cat ~/duckdns/duck.log

# Should show "OK"
# If not, check token and domain name
```

---

## 🎉 **Done!**

You now have:
- ✅ Free custom domain
- ✅ Unlimited requests
- ✅ HTTPS/SSL encryption
- ✅ No monthly fees
- ✅ Professional setup

**Access your bot at:** `https://yourbot.duckdns.org`

---

## 📱 **Bonus: Mobile Access**

Your dashboard is now accessible from:
- ✅ Phone
- ✅ Tablet
- ✅ Any computer
- ✅ Anywhere in the world

Just visit: `https://yourbot.duckdns.org`

---

## 🔄 **Maintenance:**

```bash
# Check nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# Restart nginx
sudo systemctl restart nginx

# Renew SSL (automatic, but can force)
sudo certbot renew

# Update DuckDNS IP (automatic via cron)
~/duckdns/duck.sh
```

---

## 💡 **Tips:**

1. **Keep router on** - Port forwarding needs router running
2. **Static local IP** - Set server to static IP in router DHCP
3. **Backup config** - Save nginx config before changes
4. **Monitor logs** - Check nginx logs for issues
5. **Test regularly** - Ensure DuckDNS is updating

---

**No more ngrok rate limits!** 🎉
