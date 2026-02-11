# coffee-roast-monitoring

## TODO:
[x] History: Add tasting notes field with submit button \
[x] History: Show/edit bean info \
[x] History: Delete button \
[x] History: Clean-up refresh button
[x] Collect: 3 min window \
[x] Collect: Move thermocouple creation to thread \
[x] Collect: Use deque for recording \
[x] Collect: Use event for recording \
[x] Auto start app \
[x] Graceful shutdown \
[x] display only works with if first and second crack are not none \
[x] add home page \

Low priority: \
[] config file \
[] Collect: Button to start temperature read \
[] Debounce switch instead of submit button \


## Commands
Run without activating env
`uv run app.py`
`uv run --extra pi app.py`

`uv sync` Update the project's environment

## Raspberry Pi
Run on boot
`sudo vim /etc/systemd/system/coffee-roast-monitor.service`
```
[Unit]
Description=Coffee Roast Monitoring Dash App
After=network.target

[Service]
User=pi
WorkingDirectory=/home/pi/coffee-roast-monitoring
ExecStart=/home/pi/coffee-roast-monitoring/.venv/bin/python app.py
Restart=always                    # Restart the app if it crashes
RestartSec=10                     # Wait 10 seconds before restarting
StandardOutput=journal            # Log output to journald
StandardError=journal             # Log errors to journald
Environment="PYTHONUNBUFFERED=1"  # Ensure Python output is unbuffered

[Install]
WantedBy=multi-user.target
```
Enable to start on boot
`sudo systemctl enable coffee-roast-monitor.service`
Start it now
`sudo systemctl start coffee-roast-monitor.service`
Check status
`systemctl status coffee-roast-monitor.service`
View live logs
`journalctl -u coffee-roast-monitor.service -f`
