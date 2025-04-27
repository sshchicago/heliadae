#!/usr/bin/env python3
import os
import time
from datetime import datetime

import radiacode as rcCore

def log(log_file, message):
    with open(log_file, 'a') as logger:
        logger.write(f'[{datetime.now()}]: {message}\n')

def main():
    start = datetime.now()
    home = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    log_directory = f'{home}/logs'
    os.makedirs(log_directory, exist_ok=True)
    main_log_file = f'{log_directory}/rc-main-{start.strftime("%Y-%m-%dT%H:%M:%S")}.log'
    data_log_file = main_log_file.replace("main", "data")

    log(main_log_file, "Connecting to Radiacode...")
    device = rcCore.RadiaCode()
    log(main_log_file, "Connected!")
    a0, a1, a2 = device.energy_calib()

    log(main_log_file, f'Serial number: {device.serial_number()}.')
    log(main_log_file, f'Firmware: {device.fw_version()}.')
    log(main_log_file, f'Energy Calibration constants: {a0}, {a1}, {a2}.')
    log(main_log_file, f'Logging data to {data_log_file}.')
        
    #log(main_log_file, "Resetting dose and spectrum")
    #device.dose_reset()
    #device.spectrum_reset()

    try:
        while True:
            #log(main_log_file, "Logging buffer")
            #for data in device.data_buf():
            #    msg = data.dt.isoformat() + " " + repr(data)
            #    log(data_log_file, msg)
            log(main_log_file, "Logging spectrum")
            spectrum = device.spectrum()
            log(data_log_file, repr(spectrum))
            log(main_log_file, "Sleeping")
            time.sleep(5)
    except KeyboardInterrupt:
        log(main_log_file, "Ctrl+c detected, shutting down.")

if __name__ == "__main__":
    main()