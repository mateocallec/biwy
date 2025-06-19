#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "Updating package lists..."
sudo apt update

echo "Installing Python 3 and pip..."
sudo apt install -y python3 python3-pip

echo "Upgrading pip to latest version..."
python3 -m pip install --upgrade pip

echo "Installing required Python packages..."
sudo apt install -y python3-requests python3-numpy python3-statsmodels

echo "Setup complete."
