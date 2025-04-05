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
    mainLogFile = None
    io_thread = None

    def __init__(self, mainLogFile):
        """
        Initialize the Radiacode 10X to log to disk.
        """
        self.mainLogFile = mainLogFile

        device = rcCore.RadiaCode()
        a0, a1, a2 = device.energy_calib()
        start = datetime.now()
        cwd = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

        base_directory = f'{cwd}/logs'
        os.makedirs(base_directory, exist_ok=True)
        logFileName = f'{base_directory}/rc-{start}.log'
        self.log(f'Logging to {logFileName}')

        with open(logFileName, 'w') as logFile:
            logFile.write(f'### Beginning at {start}.\n')
            logFile.write(f'### Serial number: {device.serial_number()}.\n')
            logFile.write(f'### Firmware: {device.fw_version()}\n')
            logFile.write(f'### Energy Calibration constants: {a0}, {a1}, {a2}.\n')

        self.log("Resetting dose and spectrum")
        device.dose_reset()
        device.spectrum_reset()
        
        self.io_thread = threading.Thread(target=self.__io_thread, args=[device, logFileName, start], daemon=True)
        self.io_thread.start()
        self.log("Done with init")


    def isThreadAlive(self):
        """
        Used by main.py to see if the background thread crashed.
        """
        return self.io_thread.is_alive()


    def __io_thread(self, device, logFileName, start):
        """
        Do not invoke directly, this method never returns.
        """
        self.log("Radiacode i/o thread running")
        logFile = open(logFileName, 'a')
        while True:
            self.log("Logging buffer")
            for data in device.data_buf():
                msg = data.dt.isoformat() + " " + repr(data) + "\n"
                logFile.write(msg)
                logFile.flush()
            
            self.log("Logging spectrum")
            spectrum = device.spectrum()
            newTime = start + spectrum.duration
            
            msg = newTime.isoformat() + " " + repr(spectrum) + "\n"
            logFile.write(msg)
            logFile.flush()

            self.log("Sleeping")
            time.sleep(5)

    def log(self, message):
        self.mainLogFile.write(f'[{datetime.now()}]: RC: {message}\n')
        self.mainLogFile.flush()
    
if __name__ == "__main__":
    with open(f'main-rc-{datetime.now()}.log', 'w') as logFile:
        print("RC: Starting Radiacode...")
        rc = Rc(logFile)
        input("RC: Running. Press Enter to exit.")
