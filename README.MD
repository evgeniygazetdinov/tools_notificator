# Telegram bot chat bot recognition voice to text

- you could use install.sh script to install all requirements and set up bot 
- or make that manually by following instructions below


### install requirements
```
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.11 python3.11-dev python3.11-venv
python3.11 -m venv env_py311
source env_py311/bin/activate
python --version
pip install -r requirements.txt
```
### set env variables into .env file
```
cp .env.example .env
TELEGRAM_BOT_TOKEN=YOUR TELEGRAM BOT TOKEN
```


### for use bot as demon create service file

```
sudo nano /etc/systemd/system/telegram-voice-bot.service
```
set your working directory and python path inside template
```
[Unit]
Description=Telegram Voice Recognition Bot
After=network.target

[Service]
Type=simple
User=ev
WorkingDirectory=YOUR WORKING DIRECTORY
ExecStart=YOUR PYTHON PATH YOUR WORKING DIRECTORY/main.py
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```
and some usefull preparation
 ```
sudo systemctl daemon-reload
sudo systemctl enable telegram-voice-bot
sudo systemctl start telegram-voice-bot

sudo systemctl status telegram-voice-bot
```