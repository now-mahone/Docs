#!/bin/bash
# Created: 2026-02-23
# One-command setup: Nginx + Let's Encrypt SSL for solver.kerne.ai
# Run this on the DigitalOcean droplet AFTER adding the DNS A record.
#
# Usage:
#   chmod +x setup_solver_ssl.sh
#   sudo ./setup_solver_ssl.sh

set -e

DOMAIN="solver.kerne.ai"
EMAIL="team@kerne.ai"

echo "=== Kerne Solver SSL Setup ==="
echo "Domain: $DOMAIN"
echo ""

# 1. Install Nginx and Certbot
echo "[1/5] Installing Nginx and Certbot..."
apt-get update -qq
apt-get install -y nginx certbot python3-certbot-nginx

# 2. Write Nginx config (HTTP only first, Certbot will upgrade to HTTPS)
echo "[2/5] Writing Nginx config..."
cat > /etc/nginx/sites-available/solver-kerne << 'EOF'
server {
    listen 80;
    server_name solver.kerne.ai;

    # Health check (no auth needed)
    location /health {
        proxy_pass http://127.0.0.1:8081/health;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 30s;
        proxy_connect_timeout 10s;
    }

    # All other requests → solver API
    location / {
        proxy_pass http://127.0.0.1:8081;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
        proxy_connect_timeout 10s;
        proxy_send_timeout 60s;

        # CoW Protocol driver sends large auction payloads
        client_max_body_size 10M;
    }
}
EOF

# 3. Enable the site
echo "[3/5] Enabling Nginx site..."
ln -sf /etc/nginx/sites-available/solver-kerne /etc/nginx/sites-enabled/solver-kerne
nginx -t
systemctl reload nginx

# 4. Obtain SSL certificate via Let's Encrypt
echo "[4/5] Obtaining SSL certificate..."
certbot --nginx \
    -d "$DOMAIN" \
    --email "$EMAIL" \
    --agree-tos \
    --non-interactive \
    --redirect

# 5. Verify
echo "[5/5] Verifying..."
systemctl reload nginx
echo ""
echo "=== Setup Complete ==="
echo "Solver is now live at: https://$DOMAIN"
echo ""
echo "Test it:"
echo "  curl https://$DOMAIN/health"
echo "  curl https://$DOMAIN/staging/arbitrum/health"
echo ""
echo "Send Tamir this endpoint:"
echo "  https://$DOMAIN"
echo "  (e.g. https://$DOMAIN/staging/arbitrum)"