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


import serial
import threading

import sys
sys.path.append("..")
from FisnarCommands import FisnarCommands

def getSinglePrecisionBits(number):
    # given a floating point number, return a bit string representing how
    # the number would be stored as a single precision floating point number
    # in accordance with IEEE 754

    def floatToBinary(num, places):
        # helper function for turning a float into its equivalent binary representation

        whole, dec = str(num).split(".")  # splitting into whole number and fraction
        ret_str = bin(int(whole))[2:] + "."  # first part of return string is the whole number in 'traditional' binary

        # getting decimal part
        dec = float("." + dec)
        for i in range(1, places + 1):
            if dec >= 2**(-i):  # 'i'th digit is a 1
                ret_str += "1"
                dec = dec - 2**(-i)
            else:  # 'i'th digit is a 0
                ret_str += "0"

        return ret_str

    # getting sign of number
    sign_bit = 0
    if number < 0:
        sign_bit = 1
        number *= -1
    sign_bit = str(sign_bit)  # for returning binary string later

    # turning decimal number to binary number (with 30 binary 'decimal' places (30 digits after the '.'))
    bin_str = floatToBinary(number, 30)

    # getting indices of the first '1' and the '.' in the binary representation
    first_one_ind = bin_str.find("1")
    dot_ind = bin_str.find(".")

    # preparing the 'to-be' mantissa binary string by removing '.'
    if first_one_ind < dot_ind:
        bin_str = bin_str.replace(".", "")
        dot_ind -= 1
    else:
        bin_str = bin_str.replace(".", "")
        dot_ind -= 1
        first_one_ind -= 1

    # calculating stored exponent and converting to binary
    real_exp = dot_ind - first_one_ind
    stored_exp = real_exp + 127
    exp_bits = bin(stored_exp)[2:].zfill(8)

    # getting stored mantissa from number's binary representation
    mantissa_bits = bin_str[first_one_ind + 1:][:23].ljust(23, "0")
    print(mantissa_bits, len(mantissa_bits))

    # putting it all together
    ret_bits = sign_bit + exp_bits + mantissa_bits
    return(ret_bits)


if __name__ == "__main__":
    serial_port = serial.Serial("COM7", 115200, timeout=3)

    # for i in range(20):
    #     serial_port.write(FisnarCommands.VA(i, 0, 0))
    #     print(f"sent: {FisnarCommands.VA(i, 0, 0)}")
    #     for j in range(2):
    #         print(serial_port.readline())
    #
    # serial_port.write(FisnarCommands.ID())

    serial_port.write(FisnarCommands.finalizer())

    serial_port.close()
