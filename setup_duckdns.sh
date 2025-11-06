#!/bin/bash
# DuckDNS Setup Script for Dynamic IP Updates
# Run this after setting up your DuckDNS account

set -e

echo "=========================================="
echo "🦆 DuckDNS Setup"
echo "=========================================="
echo ""

# Get DuckDNS details
read -p "Enter your DuckDNS domain (without .duckdns.org): " DOMAIN
read -p "Enter your DuckDNS token: " TOKEN

if [ -z "$DOMAIN" ] || [ -z "$TOKEN" ]; then
    echo "❌ Domain and token cannot be empty"
    exit 1
fi

# Create directory
echo "📁 Creating DuckDNS directory..."
mkdir -p ~/duckdns
cd ~/duckdns

# Create update script
echo "📝 Creating update script..."
cat > duck.sh <<EOF
#!/bin/bash
echo url="https://www.duckdns.org/update?domains=$DOMAIN&token=$TOKEN&ip=" | curl -k -o ~/duckdns/duck.log -K -
EOF

chmod +x duck.sh

# Test it
echo "🧪 Testing DuckDNS update..."
./duck.sh
sleep 2

if grep -q "OK" duck.log; then
    echo "✅ DuckDNS update successful!"
else
    echo "❌ DuckDNS update failed. Check your domain and token."
    cat duck.log
    exit 1
fi

# Add to crontab
echo "⏰ Setting up automatic updates (every 5 minutes)..."
(crontab -l 2>/dev/null | grep -v "duckdns/duck.sh"; echo "*/5 * * * * ~/duckdns/duck.sh >/dev/null 2>&1") | crontab -

echo ""
echo "=========================================="
echo "✅ DuckDNS Setup Complete!"
echo "=========================================="
echo ""
echo "📋 Details:"
echo "   Domain: $DOMAIN.duckdns.org"
echo "   Update script: ~/duckdns/duck.sh"
echo "   Log file: ~/duckdns/duck.log"
echo "   Updates: Every 5 minutes (automatic)"
echo ""
echo "🧪 Test your domain:"
echo "   ping $DOMAIN.duckdns.org"
echo ""
echo "📝 Next: Install SSL certificate"
echo "   sudo apt install certbot python3-certbot-nginx -y"
echo "   sudo certbot --nginx -d $DOMAIN.duckdns.org"
echo ""
echo "=========================================="
