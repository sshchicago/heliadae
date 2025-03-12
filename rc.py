"""
Radiacode library / logger.
"""
import os
import threading
import time
from datetime import datetime

import radiacode as rcCore

class Rc():
    """
    Encapsulates the Radiacode 10X detector.
    Assumes a USB connection.
    """
    debug = False

    def __init__(self, debug=False):
        """
        Initialize the Radiacode 10X to log to disk.
        """
        self.debug = debug

        device = rcCore.RadiaCode()
        a0, a1, a2 = device.energy_calib()
        start = datetime.now()

        base_directory = "/home/pi/logs/"
        os.makedirs(base_directory, exist_ok=True)
        logFileName = f'/home/pi/logs/rc-{start}.log'
        self.dbg(f'Logging to {logFileName}')

        with open(logFileName, 'w') as logFile:
            logFile.write(f'### Beginning at {start}.\n')
            logFile.write(f'### Serial number: {device.serial_number()}.\n')
            logFile.write(f'### Firmware: ${device.fw_version()}\n')
            logFile.write(f'### Energy Calibration constants: {a0}, {a1}, {a2}.\n')

        self.dbg("Resetting dose and spectrum")
        device.dose_reset()
        device.spectrum_reset()
        
        self.io_thread = threading.Thread(target=self.__io_thread, args=[device, logFileName, start], daemon=True)
        self.io_thread.start()
        self.dbg("Done with init")
    
    def __io_thread(self, device, logFileName, start):
        """
        Do not invoke directly, this method never returns.
        """
        self.dbg("Radiacode i/o thread running")
        logFile = open(logFileName, 'a')
        while True:
            self.dbg("Logging buffer")
            for data in device.data_buf():
                msg = data.dt.isoformat() + " " + repr(data) + "\n"
                logFile.write(msg)
                logFile.flush()
            
            self.dbg("Logging spectrum")
            spectrum = device.spectrum()
            newTime = start + spectrum.duration
            msg = newTime.isoformat() + " " + repr(spectrum) + "\n"
            logFile.write(msg)
            logFile.flush()

            self.dbg("Sleeping")
            time.sleep(5)
    
    def dbg(self, msg):
        if self.debug:
            print(msg)

if __name__ == "__main__":
    print("Starting Radiacode...")
    rc = Rc(True)
    input("Running. Press Enter to exit.")
