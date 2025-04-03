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
    io_thread = None

    def __init__(self, debug=False):
        """
        Initialize the Radiacode 10X to log to disk.
        """
        self.debug = debug

        device = rcCore.RadiaCode()
        a0, a1, a2 = device.energy_calib()
        start = datetime.now()
        cwd = os.getcwd()

        base_directory = f'{cwd}/logs'
        os.makedirs(base_directory, exist_ok=True)
        logFileName = f'{base_directory}/rc-{start}.log'
        self.dbg(f'RC: Logging to {logFileName}')

        with open(logFileName, 'w') as logFile:
            logFile.write(f'### Beginning at {start}.\n')
            logFile.write(f'### Serial number: {device.serial_number()}.\n')
            logFile.write(f'### Firmware: {device.fw_version()}\n')
            logFile.write(f'### Energy Calibration constants: {a0}, {a1}, {a2}.\n')

        print("RC: Resetting dose and spectrum")
        device.dose_reset()
        device.spectrum_reset()
        
        self.io_thread = threading.Thread(target=self.__io_thread, args=[device, logFileName, start], daemon=True)
        self.io_thread.start()
        print("RC: Done with init")


    def isThreadAlive(self):
        return self.io_thread.is_alive()


    def __io_thread(self, device, logFileName, start):
        """
        Do not invoke directly, this method never returns.
        """
        print("RC: Radiacode i/o thread running")
        logFile = open(logFileName, 'a')
        while True:
            self.dbg("RC: Logging buffer")
            for data in device.data_buf():
                msg = data.dt.isoformat() + " " + repr(data) + "\n"
                logFile.write(msg)
                logFile.flush()
            
            self.dbg("RC: Logging spectrum")
            spectrum = device.spectrum()
            newTime = start + spectrum.duration
            
            msg = newTime.isoformat() + " " + repr(spectrum) + "\n"
            logFile.write(msg)
            logFile.flush()

            self.dbg("RC: Sleeping")
            time.sleep(5)


    def dbg(self, msg):
        if self.debug:
            print(msg)

if __name__ == "__main__":
    print("RC: Starting Radiacode...")
    rc = Rc(True)
    input("RC: Running. Press Enter to exit.")
