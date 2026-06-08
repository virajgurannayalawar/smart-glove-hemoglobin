#!/bin/bash
# Smart Glove Edge Firmware Upgrade Script
# Run as root on Raspberry Pi

set -e

echo "=========================================="
echo "Smart Glove Edge Firmware Upgrade"
echo "=========================================="

# Configuration
INSTALL_DIR="/opt/smart_glove"
SERVICE_USER="smartglove"
SERVICE_NAME="smart_glove"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root"
    exit 1
fi

# Stop service
echo "Stopping service..."
systemctl stop "$SERVICE_NAME"

# Backup current installation
echo "Backing up current installation..."
BACKUP_DIR="/opt/smart_glove_backup_$(date +%Y%m%d_%H%M%S)"
cp -r "$INSTALL_DIR" "$BACKUP_DIR"
echo "Backup created at: $BACKUP_DIR"

# Update firmware files
echo "Updating firmware files..."
cp -r edge_firmware "$INSTALL_DIR/"
cp requirements.txt "$INSTALL_DIR/"

# Set permissions
echo "Setting permissions..."
chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"

# Upgrade dependencies
echo "Upgrading dependencies..."
sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install --upgrade pip
sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt"

# Update systemd service if changed
if [ -f "deploy/smart_glove.service" ]; then
    echo "Updating systemd service..."
    cp deploy/smart_glove.service /etc/systemd/system/
    systemctl daemon-reload
fi

# Start service
echo "Starting service..."
systemctl start "$SERVICE_NAME"

echo "=========================================="
echo "Upgrade complete!"
echo "=========================================="
echo ""
echo "Check service status: sudo systemctl status $SERVICE_NAME"
echo "View logs: sudo journalctl -u $SERVICE_NAME -f"
echo ""
echo "If there are issues, restore from backup:"
echo "  sudo systemctl stop $SERVICE_NAME"
echo "  sudo rm -rf $INSTALL_DIR"
echo "  sudo mv $BACKUP_DIR $INSTALL_DIR"
echo "  sudo systemctl start $SERVICE_NAME"
echo ""
