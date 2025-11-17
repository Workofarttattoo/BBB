# Fiverr Autonomous Manager - Setup Guide
**Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.**

## Overview

The Fiverr Autonomous Manager provides 24/7 automated monitoring and management of your Fiverr freelance business. It includes:

- **Inbox Scanning**: Automatic detection of new messages
- **Order Management**: Active order monitoring
- **Human-like Behavior**: Randomized check intervals to avoid detection
- **Autonomous Watchdog**: Self-healing with session recovery
- **Comprehensive Logging**: Full activity tracking

## Architecture

```
┌──────────────────────────────────────────────────┐
│  fiverr_autonomous_manager.py                    │
│  - Core Selenium-based automation                │
│  - Chrome profile attachment                     │
│  - Inbox/order scanning                          │
└──────────────────┬───────────────────────────────┘
                   │
┌──────────────────▼───────────────────────────────┐
│  fiverr_watchdog_autonomous.py                   │
│  - 24/7 watchdog service                         │
│  - Human-like sleep intervals                    │
│  - Auto-recovery on failures                     │
│  - Statistics tracking                           │
└──────────────────┬───────────────────────────────┘
                   │
┌──────────────────▼───────────────────────────────┐
│  ech0_autonomous_business.py                     │
│  - Integration with full business automation     │
│  - Multi-module coordination                     │
│  - Daily reporting                               │
└──────────────────────────────────────────────────┘
```

## Prerequisites

### 1. Install Dependencies

```bash
cd /Users/noone/repos/BBB
pip install selenium webdriver-manager
```

### 2. Chrome Profile Setup

**CRITICAL**: The system uses your existing Chrome profile to avoid repeated logins.

#### macOS:
```bash
export FIVERR_CHROME_PROFILE_PATH="/Users/$(whoami)/Library/Application Support/Google/Chrome"
export FIVERR_PROFILE_DIRECTORY="Default"  # or "Profile 1", etc.
```

#### Windows:
```powershell
$env:FIVERR_CHROME_PROFILE_PATH="C:\Users\$env:USERNAME\AppData\Local\Google\Chrome\User Data"
$env:FIVERR_PROFILE_DIRECTORY="Default"
```

#### Linux:
```bash
export FIVERR_CHROME_PROFILE_PATH="/home/$(whoami)/.config/google-chrome"
export FIVERR_PROFILE_DIRECTORY="Default"
```

### 3. Initial Login

**IMPORTANT**: You must manually log into Fiverr ONCE using the Chrome profile:

1. Close ALL Chrome windows
2. Open Chrome with your profile: `open -a "Google Chrome" --args --user-data-dir="$FIVERR_CHROME_PROFILE_PATH" --profile-directory="$FIVERR_PROFILE_DIRECTORY"`
3. Navigate to https://www.fiverr.com
4. Log in with your Fiverr credentials
5. Verify "Remember Me" is checked
6. Close Chrome completely

## Usage

### Standalone Watchdog Mode (Recommended)

Run the autonomous watchdog as a 24/7 service:

```bash
# Set environment variables
export FIVERR_CHROME_PROFILE_PATH="/Users/$(whoami)/Library/Application Support/Google/Chrome"
export FIVERR_PROFILE_DIRECTORY="Default"

# Run watchdog
python fiverr_watchdog_autonomous.py
```

**Behavior**:
- Checks every 5-15 minutes (randomized)
- Occasional 20-45 minute breaks (20% of time)
- Rare 1-2 hour breaks (10% of time)
- Auto-recovery on session failures
- Logs to `/Users/noone/.ech0/fiverr_watchdog.log`

### Integrated with ECH0 Business System

To integrate with the full autonomous business system:

```bash
# Edit config
nano /Users/noone/.ech0/business_config.json
```

Update Fiverr section:
```json
{
  "fiverr": {
    "username": "your_fiverr_username",
    "chrome_profile_path": "/Users/yourname/Library/Application Support/Google/Chrome",
    "chrome_profile_directory": "Default",
    "auto_respond": true,
    "check_interval_minutes": 15
  }
}
```

Run integrated system:
```bash
python ech0_autonomous_business.py
```

### Direct Module Usage

For custom integration:

```python
from fiverr_autonomous_manager import FiverrAutonomousManager

# Initialize
agent = FiverrAutonomousManager()

# Connect and check
if agent.connect_to_dashboard():
    num_messages = agent.scan_inbox()
    num_orders = agent.check_active_orders()

    print(f"Messages: {num_messages}, Orders: {num_orders}")

# Shutdown
agent.shutdown()
```

## Features

### 1. Inbox Scanning

Detects unread messages using CSS selectors:
```python
num_messages = agent.scan_inbox()
# Returns: number of unread messages (0 if none)
```

### 2. Order Management

Checks active orders:
```python
num_orders = agent.check_active_orders()
# Returns: number of active orders (0 if none)
```

### 3. Human-like Sleep Patterns

The watchdog mimics biological irregularity:
- **70% of checks**: 5-15 minute intervals
- **20% of checks**: 20-45 minute intervals
- **10% of checks**: 1-2 hour intervals

This prevents pattern detection by Fiverr's anti-automation systems.

### 4. Session Recovery

If the Chrome session expires or fails:
1. Watchdog detects failure after 3 consecutive errors
2. Shuts down existing browser instance
3. Waits 30 seconds
4. Reinitializes agent with fresh session
5. Continues monitoring

### 5. Statistics Tracking

Real-time statistics saved to `/Users/noone/.ech0/fiverr_watchdog_stats.json`:
```json
{
  "started_at": "2025-11-16T20:00:00",
  "total_checks": 127,
  "messages_found": 15,
  "orders_found": 8,
  "errors": 2,
  "last_check": "2025-11-16T23:45:12"
}
```

## Running as System Service

### macOS (launchd)

Create `/Users/noone/Library/LaunchAgents/com.corporationoflight.fiverr-watchdog.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.corporationoflight.fiverr-watchdog</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/noone/repos/BBB/fiverr_watchdog_autonomous.py</string>
    </array>
    <key>EnvironmentVariables</key>
    <dict>
        <key>FIVERR_CHROME_PROFILE_PATH</key>
        <string>/Users/noone/Library/Application Support/Google/Chrome</string>
        <key>FIVERR_PROFILE_DIRECTORY</key>
        <string>Default</string>
    </dict>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/Users/noone/.ech0/fiverr_watchdog_stdout.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/noone/.ech0/fiverr_watchdog_stderr.log</string>
</dict>
</plist>
```

Load service:
```bash
launchctl load ~/Library/LaunchAgents/com.corporationoflight.fiverr-watchdog.plist
```

### Linux (systemd)

Create `/etc/systemd/system/fiverr-watchdog.service`:

```ini
[Unit]
Description=Fiverr Autonomous Watchdog
After=network.target

[Service]
Type=simple
User=noone
Environment="FIVERR_CHROME_PROFILE_PATH=/home/noone/.config/google-chrome"
Environment="FIVERR_PROFILE_DIRECTORY=Default"
ExecStart=/usr/bin/python3 /home/noone/repos/BBB/fiverr_watchdog_autonomous.py
Restart=always
RestartSec=30

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable fiverr-watchdog
sudo systemctl start fiverr-watchdog
sudo systemctl status fiverr-watchdog
```

## Troubleshooting

### "Browser attachment failed"
- Ensure ALL Chrome windows are closed before starting
- Verify `FIVERR_CHROME_PROFILE_PATH` points to correct directory
- Check Chrome profile directory name (Default, Profile 1, etc.)

### "Session expired" messages
- Manually log into Fiverr again using the Chrome profile
- Ensure "Remember Me" is checked during login
- Check if Fiverr requires 2FA (may need manual intervention)

### CSS selector errors
Fiverr frequently changes their HTML structure. If selectors break:

1. Inspect the Fiverr inbox page
2. Find the new selector for unread messages
3. Update `fiverr_autonomous_manager.py`:
   ```python
   # Line ~103
   unread_msgs = self.driver.find_elements(By.CSS_SELECTOR, ".your-new-selector")
   ```

### High memory usage
Chrome with Selenium can consume 200-500MB RAM. This is normal. If it becomes excessive:
- Reduce check frequency
- Restart watchdog daily via cron/scheduled task

## Security Considerations

1. **Profile Security**: Chrome profile contains sensitive data. Ensure proper file permissions:
   ```bash
   chmod 700 "/Users/noone/Library/Application Support/Google/Chrome"
   ```

2. **Credential Storage**: Never hardcode passwords. Use environment variables or secure vaults.

3. **Log Files**: Logs may contain sensitive info. Rotate and secure them:
   ```bash
   chmod 600 /Users/noone/.ech0/fiverr_watchdog.log
   ```

4. **Anti-Detection**: The system uses stealth flags to avoid bot detection, but Fiverr may still flag automated activity. Use responsibly.

## Next Steps

### TODO Integration Points

1. **LLM Auto-Response**: Integrate `ech0_llm_engine.py` for automatic message responses
2. **Order Processing**: Implement order fulfillment workflows
3. **Analytics Dashboard**: Build real-time dashboard for stats visualization
4. **Multi-Account Support**: Extend to manage multiple Fiverr accounts
5. **Webhook Notifications**: Send alerts via Twilio/Discord when messages arrive

## Support

For issues or feature requests:
- Email: inventor@aios.is
- Phone: (725) 224-2617

**Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.**
