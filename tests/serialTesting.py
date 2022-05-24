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


# # 5/24 tests (trying to interface with Nordson pressure controller from Python)
import serial

pressureController = serial.Serial("COM7", timeout=10)  # 10 indicates a read timeout of 10 seconds

str_to_write = f"{chr(5)}{chr(2)}03DI F0{chr(3)}{chr(4)}"  # ascii characters: ENQ, STX, ETX, EOT
bytes_to_write = bytes(str_to_write, "ascii")

write_ret_val = pressureController.write(bytes_to_write)
print(write_ret_val)
print(pressureController.in_waiting)
confirm_line = pressureController.readline()

print(confirm_line)


























# space saver
