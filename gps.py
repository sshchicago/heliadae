"""
GPS library / logger
"""
import os
import queue
import serial
import threading
import time
from datetime import datetime

import pynmea2
import pynmea2.types.talker

class Gps():
    """
    Encapsulates the GPS receiver.
    Contains a PySerial UART connection, and a I/O thread.
    Also includes functions to configure the GPS, and generate "UBX" messages.
    """
    debug = False
    default_timeout = 0.1 # Serial port read timeout. Should be quite low.
    port = None

    ubx_write_queue = None
    ubx_read_queue = None

    io_thread = None

    def __init__(self, debug=False):
        """
        Configure the GPS device and initialize queues, and start the I/O thread.
        """
        start = datetime.now()
        cwd = os.getcwd()

        base_directory = f'{cwd}/logs'
        os.makedirs(base_directory, exist_ok=True)
        logFileName = f'{base_directory}/gps-{start}.log'
        with open(logFileName, 'w') as logFile:
            logFile.write(f'### Beginning at {start}\n')

        self.debug=debug
        self.port = serial.Serial('/dev/ttyS0', 9600, timeout=self.default_timeout)
        self.ubx_write_queue = queue.Queue()
        self.ubx_read_queue = queue.Queue()
        self.io_thread = threading.Thread(target=self.__io_thread, args=[logFileName], daemon=True)
        self.io_thread.start()
        time.sleep(1)
        self._configure_output_messages()
        time.sleep(1)
        self._enable_flight_mode()
        print("GPS: Done with init")


    def isThreadAlive(self):
        return self.io_thread.is_alive()


    def _configure_output_messages(self):
        """
        Disables NMEA sentences with CFG-PRN: GLL, GSA, GSV, RMC, VTG (id 1 to 5)
        """
        self.dbg("GPS: Configuring NMEA sentence output")
        ubx_cfg_class = 0x06
        ubx_cfg_msg = 0x01
        for index in range(1, 6):
            payload = bytearray.fromhex("F0")
            payload += index.to_bytes(1, byteorder='little')
            payload += bytearray.fromhex("00 00 00 00 00 01")
            ack_ok = self._send_and_confirm_ubx_packet(ubx_cfg_class, ubx_cfg_msg, payload)
            if not ack_ok:
                raise Exception("Failed to configure output message id {}".format(index))
        print("GPS: NMEA sentence output configured.")


    def _enable_flight_mode(self):
        """
        Sends a CFG-NAV5 UBX message which enables "flight mode", which allows
        operation at higher altitudes than defaults.
        Should read up more on this sentence, I'm just copying this
        byte string from other tracker projects.
        See for example string:
            https://github.com/Chetic/Serenity/blob/master/Serenity.py#L10
            https://github.com/PiInTheSky/pits/blob/master/tracker/gps.c#L423
        Reference: https://content.u-blox.com/sites/default/files/products/documents/u-blox8-M8_ReceiverDescrProtSpec_UBX-13003221.pdf?utm_content=UBX-13003221
        """
        self.dbg("GPS: Enabling flight mode")
        cfg_nav5_class_id = 0x06
        cfg_nav5_message_id = 0x24
        payload = bytearray.fromhex("FF FF 06 03 00 00 00 00 10 27 00 00 05 00 FA 00 FA 00 64 00 2C 01 00 00 00 00 00 00 00 00 00 00 00 00 00 00")
        ack_ok = self._send_and_confirm_ubx_packet(cfg_nav5_class_id, cfg_nav5_message_id, payload)
        if not ack_ok:
            raise Exception("Failed to configure GPS for flight mode.")
        print("GPS: Flight mode enabled.")


    def _reboot(self):
        """
        This method REBOOTS THE GPS. Useful for testing/debugging.
        Not useful at 30000 meters!
        """
        # https://gist.github.com/tomazas/3ab51f91cdc418f5704d says to send:
        # send 0x06, 0x04, 0x04, 0x00, 0xFF, 0x87, 0x00, 0x00
        return self._send_and_confirm_ubx_packet(0x06, 0x04, bytearray.fromhex("FF 87 00 00"))


    def _ubx_checksum(self, prefix_and_payload):
        """
        Calculates a UBX binary packet checksum.
        Algorithm comes from the u-blox M8 Receiver Description manual section "UBX Checksum"
        This is an implementation of the 8-Bit Fletcher Algorithm,
            so there may be a standard library for this.
        """
        checksum_a = 0
        checksum_b = 0
        for byte in prefix_and_payload:
            checksum_a = checksum_a + byte
            checksum_b = checksum_a + checksum_b
        checksum_a %= 256
        checksum_b %= 256  
        return bytearray((checksum_a, checksum_b))


    def _ubx_assemble_packet(self, class_id, message_id, payload):
        """
        Assembles and returns a UBX packet from a class id,
        message id and payload bytearray.
        """
        # UBX protocol constants:
        ubx_packet_header = bytearray.fromhex("B5 62") # constant
        length_field_bytes = 2 # constant

        prefix = bytearray((class_id, message_id))
        length = len(payload).to_bytes(length_field_bytes, byteorder='little')
        return ubx_packet_header \
            + prefix \
            + length \
            + payload \
            + self._ubx_checksum(prefix + length + payload)


    def _send_and_confirm_ubx_packet(self, class_id, message_id, payload):
        """
        Constructs, sends, and waits for an ACK packet for a UBX "binary" packet.
        User only needs to specify the class & message IDs, and the payload as a bytearray;
            the header, length and checksum are calculated automatically.
        Then constructs the corresponding CFG-ACK packet expected, and waits for it.
        If the ACK packet is not received, returns False.
        """

        if self.ubx_read_queue.qsize() > 0:
            raise Exception("ubx_read_queue must be empty before calling this function")
        send_packet = self._ubx_assemble_packet(class_id, message_id, payload)
        self.ubx_write_queue.put(send_packet)
        print("GPS: UBX packet built: {}".format(send_packet))

        expected_ack = self._ubx_assemble_packet(0x05, 0x01, bytearray((class_id, message_id)))

        wait_length = 10 # seconds
        wait_interval = 0.1 # seconds
        for _ in range(0, int(wait_length / wait_interval)):
            time.sleep(wait_interval) # excessively large to force me to fix race conditions FIXME
            if self.ubx_read_queue.qsize() > 0:
                ack = self.ubx_read_queue.get()
                if ack == expected_ack:
                    print("GPS: UBX packet ACKd: {}".format(ack))
                    return True
                elif ack[2:3] == bytearray.fromhex("05 01"):
                    print("GPS: UBX-NAK packet! {}".format(ack))
                    return False
                else:
                    print("GPS: Unknown UBX reply: {}".format(ack))
                    print("GPS: Looking for      : {}".format(expected_ack))
                return True
        print("GPS: UBX packet sent without ACK! This is bad.")
        return False


    def __io_thread(self, logFileName):
        """
        Singleton thread which will run indefinitely, reading and
        writing between the gps serial and {read,write}_queue.

        Do not invoke directly, this method never returns.
        """
        print("GPS: I/O thread started")
        with open(logFileName, 'a') as logFile:
            while True:
                while self.ubx_write_queue.qsize() > 0:
                    to_write = self.ubx_write_queue.get()
                    to_write_type = type(to_write)
                    if to_write_type == str:
                        to_write = to_write.encode('utf-8')
                    self.dbg("GPS: write {}: {}".format(to_write_type, to_write))
                    self.port.write(to_write)
                got_some_data = self.__read(logFile)
                if not got_some_data:
                    time.sleep(0.1)


    def __read(self, logFile):
        """
        Reads a from the GPS serial port.
        Interprets between UBX and NMEA packets and places into appropriate queues.
        For NMEA packets, they are parsed by pynmea2 and corrupt packets are discarded.

        Returns False when no data is available, True when data has been read.
        """
        waiting = self.port.in_waiting
        if waiting == 0:
            return False
        first_byte = self.port.read()
        if first_byte == b'\xb5': # looks like a UBX proprietary packet
            self.port.timeout = 10
            remaining_header = self.port.read(3)
            length_bytes = self.port.read(2)
            length = int.from_bytes(length_bytes, byteorder='little')
            remaining_packet = self.port.read(length + 2) # add 2 for checksum bytes
            self.port.timeout = self.default_timeout
            ubx_packet = first_byte + remaining_header + length_bytes + remaining_packet
            self.ubx_read_queue.put(ubx_packet)
            self.dbg("GPS: UBX raw packet received: {}".format(ubx_packet))
            return True
        else:
            line = self.port.readline()
            line = first_byte + line
        try:
            ascii_line = line.decode('ascii')
        except UnicodeDecodeError as exception:
            self.dbg(exception)
            self.dbg("GPS: Reply string decode error on: {}".format(line))
            return False
        if ascii_line[0] != "$":
            self.dbg("GPS: Non-dollar line")
            return False
        # We actually have a NMEA sentence!
        self.dbg("GPS: (buf={}) raw line: {}".format(waiting, line))
        try:
            nmea_line = pynmea2.parse(ascii_line.strip(), check=True)
        except pynmea2.nmea.ParseError as exception:
            self.dbg(exception)
            return False
        if isinstance(nmea_line, pynmea2.types.talker.GGA):
            logFile.write(repr(nmea_line) + "\n")
            logFile.flush()
        else:
            print("GPS: Unhandled message type received: {}".format(nmea_line))
        return True


    def dbg(self, message):
        """ Prints a debug message to stdout if self.debug is set True """
        if self.debug:
            print(message)

if __name__ == "__main__":
    print("GPS: Starting GPS...")
    gps = Gps(True)
    input("GPS: Running. Press Enter to exit.")
