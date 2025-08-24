###for use bot as demon create service file

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
- and some usefull preparation
 ```
sudo systemctl daemon-reload
sudo systemctl enable telegram-voice-bot
sudo systemctl start telegram-voice-bot

sudo systemctl status telegram-voice-bot
```