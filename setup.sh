#!/usr/bin/env bash
set -e

echo "=== Proxy Provider Bot — Auto Setup ==="

# 1. Обновление пакетов
echo "[1/5] Обновление системы..."
sudo apt-get update -y && sudo apt-get upgrade -y

# 2. Установка Docker (если не установлен)
if ! command -v docker &> /dev/null; then
    echo "[2/5] Установка Docker..."
    curl -fsSL https://get.docker.com | sudo sh
    sudo systemctl enable docker
    sudo systemctl start docker
    sudo usermod -aG docker "$USER"
    echo "  Docker установлен."
else
    echo "[2/5] Docker уже установлен — пропускаю."
fi

# 3. Установка Docker Compose (если не установлен)
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo "[3/5] Установка Docker Compose..."
    sudo apt-get install -y docker-compose-plugin
    echo "  Docker Compose установлен."
else
    echo "[3/5] Docker Compose уже установлен — пропускаю."
fi

# 4. Установка Git (если не установлен)
if ! command -v git &> /dev/null; then
    echo "[4/5] Установка Git..."
    sudo apt-get install -y git
else
    echo "[4/5] Git уже установлен — пропускаю."
fi

# 5. Клонирование и запуск
REPO_DIR="proxy-provider-bot"
if [ -d "$REPO_DIR" ]; then
    echo "[5/5] Папка $REPO_DIR уже существует — обновляю..."
    cd "$REPO_DIR"
    git pull origin main
else
    echo "[5/5] Клонирование репозитория..."
    git clone https://github.com/Hagly1337/proxy-provider-bot.git
    cd "$REPO_DIR"
fi

# Создание .env если не существует
if [ ! -f .env ]; then
    cp .env.example .env
    echo ""
    echo "============================================"
    echo "  ВАЖНО: Укажите BOT_TOKEN и ADMIN_ID!"
    echo "============================================"
    echo ""
    read -p "Введите BOT_TOKEN: " BOT_TOKEN
    read -p "Введите ADMIN_ID: " ADMIN_ID
    sed -i "s|your-telegram-bot-token-here|$BOT_TOKEN|" .env
    sed -i "s|123456789|$ADMIN_ID|" .env
    echo ".env создан."
else
    echo ".env уже существует — пропускаю."
fi

# Запуск
echo ""
echo "Запускаю бота..."
docker compose up -d --build || docker-compose up -d --build

echo ""
echo "=== Готово! ==="
echo "Бот запущен в фоне."
echo "Логи: docker compose logs -f"
echo "Остановка: docker compose down"
