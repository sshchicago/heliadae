#!/usr/bin/env bash

cd $(dirname $(realpath $0))

echo "Updating packages..."
sudo apt-get update
sudo apt-get upgrade

echo "Installing python dependencies..."
sudo apt-get install python3-pip libglib2.0-dev
pip install radiacode pynmea2 --break-system-packages

echo "Setting up Radiacode udev rules..."
echo 'SUBSYSTEMS=="usb", ATTRS{idVendor}=="0483", ATTRS{idProduct}=="f123" GROUP="users", MODE="0666"' > /dev/shm/50-myusb.rules
sudo cp /dev/shm/50-myusb.rules /etc/udev/rules.d/50-myusb.rules
sudo udevadm control --reload-rules && sudo udevadm trigger

echo "Moving README to accessible location if someone plugs in the SD card..."
sudo cp -pv README_ABOUT_THIS_SCIENCE_EXPERIMENT.txt /boot/firmware/

echo "Making service scripts executable..."
sudo chmod +x gps.py
sudo chmod +x rc.py

echo "Setting up heliadae systemd services..."
sudo cp -pv heliadae-gps.service /etc/systemd/system/
sudo cp -pv heliadae-rc.service /etc/systemd/system/
echo "Reloading systemd..."
sudo systemctl daemon-reload
echo "Enabling systemd service..."
sudo systemctl enable heliadae-gps
sudo systemctl enable heliadae-rc
sudo systemctl start heliadae-gps
sudo systemctl start heliadae-rc