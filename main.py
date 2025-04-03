#!/usr/bin/env python3
""" Main tracker loop """

import time
from datetime import datetime
import gps as gpsLib
import rc as rcLib

def main():
    """ Main tracker loop. Never exits. """
    print(f'[{datetime.now()}]: Starting up main tracker loop...')

    ### This would be a good place to start blinking an LED
 
    gps = gpsLib.Gps()
    rc = rcLib.Rc()

    ### This would be a good place to stop blinking an LED

    while True:
        if not gps.isThreadAlive():
            gps = gpsLib.Gps()
        if not rc.isThreadAlive():
            rc = rcLib.Rc()

        print(f'[{datetime.now()}]: Loop running...')
        time.sleep(30)

if __name__ == "__main__":
    main()
