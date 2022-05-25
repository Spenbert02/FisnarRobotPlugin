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

"""
Fisnar RS 232 Protocol Settings (from fisnar f5200n.1 manual, 'remote command' section)

baud rate: 115200
# of bits: 8
parity: none
stop bits: 1
"""


# # 5/24 tests (trying to interface with Nordson pressure controller from Python)
# import serial
#
# # creating serial port object
# pressureController = serial.Serial("COM7", timeout=10)  # 10 indicates a read timeout of 10 seconds
#
# # preparing string and converting string to ascii bytes
# str_to_write = f"{chr(5)}{chr(2)}03DI F0{chr(3)}{chr(4)}"  # ascii characters: ENQ, STX, ETX, EOT
# bytes_to_write = bytes(str_to_write, "ascii")
#
# # writing command to dispenser and reading returned line
# write_ret_val = pressureController.write(bytes_to_write)
# confirm_line = pressureController.read_until(expected=bytes(chr(3), "ascii"))  # reading input buffer until 0x03 (ETX) character is read
#
# # printing returned line
# print(confirm_line)


# 5/25 tests - trying to figure out the command format the fisnar takes
import serial

# creating port object
fisnar = serial.Serial("COM7", 115200, serial.EIGHTBITS, serial.PARITY_NONE, serial.STOPBITS_ONE, timeout=10)  # assuming the default communication settings? Not sure where to find this info, wouldn't be surprised if its some weird settings

command_1 = bytes.fromhex("f0 f0")
command_2 = bytes.fromhex("e8")

fisnar.write(bytes_to_write)

confirm_line = fisnar.read()

print(confirm_line)





















# space saver
