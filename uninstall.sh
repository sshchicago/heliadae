#!/usr/bin/env bash

for service in heliadae.service; do
    sudo systemctl stop $service
    sudo systemctl disable $service
    sudo rm /etc/systemd/system/$service
done

sudo systemctl daemon-reload
