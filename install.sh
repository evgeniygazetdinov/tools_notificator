#!/bin/bash

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=== Установка Telegram бота для распознавания голосовых сообщений ===${NC}"

# Проверка наличия sudo прав
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}Для установки необходимы права администратора.${NC}"
  echo -e "${YELLOW}Запустите скрипт с sudo: sudo ./install.sh${NC}"
  exit 1
fi

# Проверка наличия необходимых утилит
echo -e "${GREEN}Проверка необходимых утилит...${NC}"
command -v apt >/dev/null 2>&1 || { echo -e "${RED}Требуется apt, но он не установлен.${NC}"; exit 1; }
command -v add-apt-repository >/dev/null 2>&1 || { echo -e "${RED}Требуется add-apt-repository, но он не установлен.${NC}"; exit 1; }

# Установка Python 3.11
echo -e "${GREEN}Добавление репозитория deadsnakes для Python 3.11...${NC}"
add-apt-repository -y ppa:deadsnakes/ppa

echo -e "${GREEN}Обновление списка пакетов...${NC}"
apt update

echo -e "${GREEN}Установка Python 3.11 и необходимых пакетов...${NC}"
apt install -y python3.11 python3.11-dev python3.11-venv

# Определение пользователя, от имени которого запущен sudo
SUDO_USER_HOME=$(eval echo ~${SUDO_USER})
PROJECT_DIR="$SUDO_USER_HOME/code/voice_recog_assist"

# Проверка существования директории проекта
if [ ! -d "$PROJECT_DIR" ]; then
  echo -e "${RED}Директория проекта не найдена: $PROJECT_DIR${NC}"
  echo -e "${YELLOW}Укажите путь к директории проекта:${NC}"
  read -p "> " PROJECT_DIR
  
  if [ ! -d "$PROJECT_DIR" ]; then
    echo -e "${RED}Директория не существует: $PROJECT_DIR${NC}"
    exit 1
  fi
fi

echo -e "${GREEN}Создание виртуального окружения Python 3.11...${NC}"
cd "$PROJECT_DIR"
python3.11 -m venv env_py311

# Активация виртуального окружения и установка зависимостей
echo -e "${GREEN}Установка зависимостей...${NC}"
source env_py311/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Проверка наличия файла .env
if [ ! -f "$PROJECT_DIR/.env" ]; then
  echo -e "${YELLOW}Файл .env не найден. Создаю из примера...${NC}"
  if [ -f "$PROJECT_DIR/.env.example" ]; then
    cp "$PROJECT_DIR/.env.example" "$PROJECT_DIR/.env"
    echo -e "${YELLOW}Файл .env создан. Пожалуйста, отредактируйте его и добавьте токен бота:${NC}"
    echo -e "${YELLOW}nano $PROJECT_DIR/.env${NC}"
  else
    echo -e "${YELLOW}Создаю файл .env...${NC}"
    echo "TELEGRAM_BOT_TOKEN=YOUR_BOT_TOKEN_HERE" > "$PROJECT_DIR/.env"
    echo -e "${YELLOW}Файл .env создан. Пожалуйста, отредактируйте его и добавьте токен бота:${NC}"
    echo -e "${YELLOW}nano $PROJECT_DIR/.env${NC}"
  fi
fi

# Настройка systemd сервиса
echo -e "${GREEN}Настройка systemd сервиса...${NC}"
SERVICE_FILE="/etc/systemd/system/telegram-voice-bot.service"

cat > "$SERVICE_FILE" << EOL
[Unit]
Description=Telegram Voice Recognition Bot
After=network.target

[Service]
Type=simple
User=${SUDO_USER}
WorkingDirectory=${PROJECT_DIR}
ExecStart=${PROJECT_DIR}/env_py311/bin/python ${PROJECT_DIR}/main.py
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOL

echo -e "${GREEN}Перезагрузка systemd...${NC}"
systemctl daemon-reload

echo -e "${GREEN}Включение автозапуска сервиса...${NC}"
systemctl enable telegram-voice-bot.service

echo -e "${GREEN}Запуск сервиса...${NC}"
systemctl start telegram-voice-bot.service

echo -e "${GREEN}Проверка статуса сервиса...${NC}"
systemctl status telegram-voice-bot.service

echo -e "${GREEN}=== Установка завершена ===${NC}"
echo -e "${YELLOW}Для проверки логов используйте:${NC} journalctl -u telegram-voice-bot -f"
echo -e "${YELLOW}Для перезапуска бота:${NC} sudo systemctl restart telegram-voice-bot"
echo -e "${YELLOW}Для остановки бота:${NC} sudo systemctl stop telegram-voice-bot"
