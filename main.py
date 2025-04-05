#!/usr/bin/env python3
""" Main tracker loop """

import time
import os
from datetime import datetime
import gps as gpsLib
import rc as rcLib

def main():
    """ Main tracker loop. Never exits. """
    cwd = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    start = datetime.now()

    base_directory = f'{cwd}/logs'
    os.makedirs(base_directory, exist_ok=True)
    logFileName = f'{base_directory}/main-{start}.log'

    with open(logFileName, 'w') as logFile:
        logFile.write(f'[{datetime.now()}]: Starting up main tracker loop...\n')

        ### This would be a good place to start blinking an LED
 
        gps = gpsLib.Gps(logFile)
        rc = rcLib.Rc(logFile)

        ### This would be a good place to stop blinking an LED

        while True:
            if not gps.isThreadAlive():
                logFile.write(f'[{datetime.now()}]: Restarting GPS...\n')
                gps = gpsLib.Gps(logFile)
            if not rc.isThreadAlive():
                logFile.write(f'[{datetime.now()}]: Restarting RC...\n')
                rc = rcLib.Rc(logFile)

            logFile.write(f'[{datetime.now()}]: Loop running...\n')
            time.sleep(30)

if __name__ == "__main__":
    main()
