#!/bin/bash
# Quick Nginx Setup Script for Scalp Bot
# Run this on your Raspberry Pi

set -e  # Exit on error

echo "=========================================="
echo "🚀 Nginx Setup for Scalp Bot"
echo "=========================================="
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "❌ Please run as root: sudo ./setup_nginx.sh"
    exit 1
fi

# Step 1: Install Nginx
echo "📦 Step 1: Installing Nginx..."
apt update
apt install nginx -y
echo "✅ Nginx installed"
echo ""

# Step 2: Get domain name
echo "🌐 Step 2: Domain Configuration"
read -p "Enter your domain (e.g., yourbot.duckdns.org): " DOMAIN

if [ -z "$DOMAIN" ]; then
    echo "❌ Domain cannot be empty"
    exit 1
fi

# Step 3: Create Nginx config
echo "⚙️ Step 3: Creating Nginx configuration..."
cat > /etc/nginx/sites-available/scalp-bot <<EOF
server {
    listen 80;
    server_name $DOMAIN;
    
    # Increase timeouts
    proxy_read_timeout 300;
    proxy_connect_timeout 300;
    proxy_send_timeout 300;
    
    # Bot dashboard
    location / {
        proxy_pass http://localhost:8001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_cache_bypass \$http_upgrade;
    }
    
    # GitHub webhook
    location /webhook {
        proxy_pass http://localhost:8001/webhook;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

# Step 4: Enable site
echo "🔗 Step 4: Enabling site..."
ln -sf /etc/nginx/sites-available/scalp-bot /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default  # Remove default site

# Step 5: Test config
echo "🧪 Step 5: Testing Nginx configuration..."
nginx -t

if [ $? -ne 0 ]; then
    echo "❌ Nginx configuration test failed"
    exit 1
fi

# Step 6: Restart Nginx
echo "🔄 Step 6: Restarting Nginx..."
systemctl restart nginx
systemctl enable nginx

echo ""
echo "=========================================="
echo "✅ Nginx Setup Complete!"
echo "=========================================="
echo ""
echo "📋 Next Steps:"
echo ""
echo "1. Set up port forwarding on your router:"
echo "   - Forward port 80 to $(hostname -I | awk '{print $1}')"
echo "   - Forward port 443 to $(hostname -I | awk '{print $1}')"
echo ""
echo "2. Set up DuckDNS (if using):"
echo "   - Visit: https://www.duckdns.org"
echo "   - Create subdomain: $DOMAIN"
echo "   - Run: ./setup_duckdns.sh"
echo ""
echo "3. Install SSL certificate:"
echo "   - Run: sudo certbot --nginx -d $DOMAIN"
echo ""
echo "4. Update bot config:"
echo "   - Edit: ~/scalp-bot/config.yaml"
echo "   - Set: use_ngrok: false"
echo "   - Set: custom_url: \"https://$DOMAIN\""
echo "   - Restart: sudo systemctl restart scalp-bot"
echo ""
echo "5. Test access:"
echo "   - Local: http://localhost"
echo "   - External: http://$DOMAIN"
echo ""
echo "=========================================="
