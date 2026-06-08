#!/bin/bash
# Smart Glove Edge Firmware Installation Script
# Run as root on Raspberry Pi

set -e

echo "=========================================="
echo "Smart Glove Edge Firmware Installation"
echo "=========================================="

# Configuration
INSTALL_DIR="/opt/smart_glove"
SERVICE_USER="smartglove"
CONFIG_DIR="/etc/smart_glove"
CACHE_DIR="/var/lib/smart_glove"

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root"
    exit 1
fi

# Create system user
echo "Creating system user..."
if ! id "$SERVICE_USER" &>/dev/null; then
    useradd --system --create-home --shell /bin/bash "$SERVICE_USER"
    echo "User $SERVICE_USER created"
else
    echo "User $SERVICE_USER already exists"
fi

# Create directories
echo "Creating directories..."
mkdir -p "$INSTALL_DIR"
mkdir -p "$CONFIG_DIR"
mkdir -p "$CACHE_DIR"
mkdir -p "$CACHE_DIR/queue"

# Copy firmware files
echo "Copying firmware files..."
cp -r edge_firmware "$INSTALL_DIR/"
cp requirements.txt "$INSTALL_DIR/"
cp .env.example "$CONFIG_DIR/.env"

# Set permissions
echo "Setting permissions..."
chown -R "$SERVICE_USER:$SERVICE_USER" "$INSTALL_DIR"
chown -R "$SERVICE_USER:$SERVICE_USER" "$CONFIG_DIR"
chown -R "$SERVICE_USER:$SERVICE_USER" "$CACHE_DIR"
chmod 750 "$CONFIG_DIR"
chmod 750 "$CACHE_DIR"

# Create virtual environment
echo "Creating virtual environment..."
sudo -u "$SERVICE_USER" python3 -m venv "$INSTALL_DIR/venv"

# Install dependencies
echo "Installing dependencies..."
sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install --upgrade pip
sudo -u "$SERVICE_USER" "$INSTALL_DIR/venv/bin/pip" install -r "$INSTALL_DIR/requirements.txt"

# Install systemd service
echo "Installing systemd service..."
cp deploy/smart_glove.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable smart_glove.service

# Configure camera
echo "Enabling camera..."
raspi-config nonint do_camera 0

# Configure GPIO permissions
echo "Configuring GPIO permissions..."
usermod -a -G gpio "$SERVICE_USER"
usermod -a -G video "$SERVICE_USER"

echo "=========================================="
echo "Installation complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Edit configuration: sudo nano $CONFIG_DIR/.env"
echo "2. Add your OWNER_ID and GLOVE_API_KEY"
echo "3. Start service: sudo systemctl start smart_glove"
echo "4. Check status: sudo systemctl status smart_glove"
echo "5. View logs: sudo journalctl -u smart_glove -f"
echo ""
