#!/usr/bin/env bash
set -e

echo "=== Proxy Provider Worker — Setup ==="

# Install Docker if needed
if ! command -v docker &> /dev/null; then
    echo "[1/3] Installing Docker..."
    curl -fsSL https://get.docker.com | sudo sh
    sudo systemctl enable docker
    sudo systemctl start docker
    sudo usermod -aG docker "$USER"
else
    echo "[1/3] Docker already installed."
fi

# Install Docker Compose if needed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "[2/3] Installing Docker Compose..."
    sudo apt-get update -y && sudo apt-get install -y docker-compose-plugin
else
    echo "[2/3] Docker Compose already installed."
fi

# Clone and configure
echo "[3/3] Setting up worker..."
REPO_DIR="proxy-provider-bot"
if [ ! -d "$REPO_DIR" ]; then
    git clone https://github.com/Hagly1337/proxy-provider-bot.git
fi
cd "$REPO_DIR/worker"

echo ""
read -p "Master server IP (e.g. 123.45.67.89): " MASTER_IP
read -p "API_SECRET (from master .env): " API_SECRET

sed -i "s|MASTER_IP|$MASTER_IP|" docker-compose.yml
sed -i "s|change-me-secret|$API_SECRET|" docker-compose.yml

echo ""
echo "Starting worker..."
docker compose up -d --build || docker-compose up -d --build

echo ""
echo "=== Worker started! ==="
echo "Logs: docker compose logs -f"
echo "Stop: docker compose down"
