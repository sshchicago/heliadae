# HELIADAE

The sons of H(a)elios. Code to run on a Raspberry Pi Zero 2 W for a HAB flight. Logs GPS and Radiacode 10X.

## Setup 

Wiring:
* [PiSugar3]() connected to board
* [GPS](https://v3.airspy.us/product/upu-ublox-m8-pico/) on serial UART (physical pins 1, 8, 9, 10)
* [Radiacode 103](https://www.radiacode.com/products#!/p/602724693/) on micro USB

On a clean install of Raspbian 9:
* raspi-config:
  * Interfacing: Serial: Disable console, enable hardware (for gps)
  * Interfacing: Enable I2C (for PiSugar RTC)
* if prompted, restart
* install PiSugar battery management: `wget https://cdn.pisugar.com/release/pisugar-power-manager.sh; bash pisugar-power-manager.sh -c release`
* update PiSugar firmware: `curl https://cdn.pisugar.com/release/PiSugarUpdate.sh | sudo bash`
* enable PiSugar rtc by appending `dtoverlay=i2c-rtc,ds3231` to `/boot/firmware/config.txt`
* restart
* git clone this repo into /home/pi/heliadae `git clone https://github.com/sshchicago/heliadae.git`
* run install.sh `cd heliadae; ./install.sh`

## Notes

* Get PiSugar3 battery life: `echo "get battery" | nc -q 127.0.0.1 8423`
* Get uptime (seconds): `cat /proc/uptime`
* Check heliadae service logs: `sudo journalctl -u heliadae`
* Stop heliadae service: `sudo systemctl stop heliadae`

## Acknowledgements

* https://github.com/trickv/radio_flyer
* https://github.com/Chetic/Serenity 
* https://github.com/PiInTheSky/pits
