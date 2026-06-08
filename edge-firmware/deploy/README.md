# Deployment Scripts

This directory contains deployment scripts for the Smart Glove Edge Firmware.

## Files

- `smart_glove.service` - Systemd service unit file
- `install.sh` - Initial installation script
- `upgrade.sh` - Upgrade script for updating firmware

## Installation

### Prerequisites

- Raspberry Pi OS (Bullseye or Bookworm)
- Python 3.10+
- Root access
- Camera module connected

### Initial Installation

1. Copy the entire `edge-firmware` directory to the Raspberry Pi
2. Navigate to the `edge-firmware` directory
3. Run the installation script:

```bash
sudo bash deploy/install.sh
```

4. Edit the configuration file:

```bash
sudo nano /etc/smart_glove/.env
```

Add your credentials:
```
OWNER_ID=your_owner_id_here
GLOVE_API_KEY=your_glove_api_key_here
```

5. Start the service:

```bash
sudo systemctl start smart_glove
```

6. Check the status:

```bash
sudo systemctl status smart_glove
```

## Upgrade

To upgrade to a new version:

1. Copy the new firmware files to the Raspberry Pi
2. Navigate to the `edge-firmware` directory
3. Run the upgrade script:

```bash
sudo bash deploy/upgrade.sh
```

The upgrade script will:
- Stop the service
- Backup the current installation
- Update the firmware files
- Upgrade dependencies
- Restart the service

If the upgrade fails, you can restore from the backup directory shown in the output.

## Service Management

### Start service
```bash
sudo systemctl start smart_glove
```

### Stop service
```bash
sudo systemctl stop smart_glove
```

### Restart service
```bash
sudo systemctl restart smart_glove
```

### Enable service (start on boot)
```bash
sudo systemctl enable smart_glove
```

### Disable service
```bash
sudo systemctl disable smart_glove
```

### View service status
```bash
sudo systemctl status smart_glove
```

### View logs
```bash
sudo journalctl -u smart_glove -f
```

### View last 100 log lines
```bash
sudo journalctl -u smart_glove -n 100
```

## Troubleshooting

### Service won't start

Check the logs for errors:
```bash
sudo journalctl -u smart_glove -n 50
```

Common issues:
- Missing configuration in `/etc/smart_glove/.env`
- Camera not enabled
- Incorrect permissions on cache directory

### Camera not detected

Enable the camera:
```bash
sudo raspi-config
# Navigate to Interface Options -> Camera -> Enable
```

### Permission errors

Ensure the service user has correct permissions:
```bash
sudo usermod -a -G video smartglove
sudo usermod -a -G gpio smartglove
```

### Configuration changes

After editing `/etc/smart_glove/.env`, restart the service:
```bash
sudo systemctl restart smart_glove
```

## Manual Installation

If you prefer manual installation instead of using the scripts:

1. Create user:
```bash
sudo useradd --system --create-home --shell /bin/bash smartglove
```

2. Create directories:
```bash
sudo mkdir -p /opt/smart_glove
sudo mkdir -p /etc/smart_glove
sudo mkdir -p /var/lib/smart_glove/queue
```

3. Copy files:
```bash
sudo cp -r edge_firmware /opt/smart_glove/
sudo cp requirements.txt /opt/smart_glove/
sudo cp .env.example /etc/smart_glove/.env
```

4. Set permissions:
```bash
sudo chown -R smartglove:smartglove /opt/smart_glove
sudo chown -R smartglove:smartglove /etc/smart_glove
sudo chown -R smartglove:smartglove /var/lib/smart_glove
sudo chmod 750 /etc/smart_glove
sudo chmod 750 /var/lib/smart_glove
```

5. Create virtual environment:
```bash
sudo -u smartglove python3 -m venv /opt/smart_glove/venv
sudo -u smartglove /opt/smart_glove/venv/bin/pip install -r /opt/smart_glove/requirements.txt
```

6. Install service:
```bash
sudo cp deploy/smart_glove.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable smart_glove
```

7. Configure and start:
```bash
sudo nano /etc/smart_glove/.env
sudo systemctl start smart_glove
```
