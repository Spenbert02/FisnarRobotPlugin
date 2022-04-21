# relies on libraries in VirtEnv, should only be run from a terminal (not
# a part of the cura application)


"""
port settings - from the device manager tab, and taken by manually getting
values using pySerial.

-- from device manager tab --
port: COM7
bits per second: 9600
data bits: 8
parity: None
flow control: None

-- from pySerial --
device: 'COM7'  (str)
name: 'COM7'  (str)
description: 'Prolific USB-toSerial Comm Port'  (str)
hwid: 'USB VID:PID=067B:2303 SER= LOCATION=1-10'  (str)
vid: 1659  (int)
    -> vendor ID
pid: 8963  (int)
    -> product ID
serial_number: ''  (str)
    -> returned an empty string
location: '1-10'  (str)
manufacturer: 'Prolific'  (str)
product: None  (NoneType)
interface: None  (NoneType)
"""

# import serial.tools.list_ports  # for getting ports information
from serial import Serial
from serial.serialutil import SerialException

import os
os.startfile("C:\\Program Files (x86)\\SmartRotbotEdit\\Smart Robot Edit.exe")

# # tinkering around
# try:
#     port = Serial("COM7", timeout=0)
# except SerialException:
#     port = None
#
# if port is not None:
#     print(port.is_open)
