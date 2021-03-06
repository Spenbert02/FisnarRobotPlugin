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


# 5/24 tests (trying to interface with Nordson pressure controller from Python)
import serial

# creating serial port object
pressureController = serial.Serial("COM4", timeout=10)  # 10 indicates a read timeout of 10 seconds

# preparing string and converting string to ascii bytes
str_to_write = f"{chr(5)}{chr(2)}03DI F0{chr(3)}{chr(4)}"  # ascii characters: ENQ, STX, ETX, EOT
bytes_to_write = bytes(str_to_write, "ascii")

# writing command to dispenser and reading returned line
write_ret_val = pressureController.write(bytes_to_write)
confirm_line = pressureController.read_until(expected=bytes(chr(3), "ascii"))  # reading input buffer until 0x03 (ETX) character is read

# printing returned line
print(confirm_line)


# # function to get check byte from a string of hex bytes
# def getCheckSumByte(bytes_to_sum):
#     tally = 0
#     for b in bytes_to_sum:
#         tally += b
#
#     return bytes.fromhex(hex(tally % 256)[2:])
#
#
# sample = bytes.fromhex("01 00 00 00 20 41 00 00 20 41 00 00 20 41 00 00 00 1f")
# print(getCheckSumByte(sample))
#
# print(sample + )


# # 5/25 tests - trying to figure out the command format the fisnar takes
# import serial
#
# # creating port object
# fisnar = serial.Serial("COM7", 115200, serial.EIGHTBITS, serial.PARITY_NONE, serial.STOPBITS_ONE, timeout=10)  # assuming the default communication settings? Not sure where to find this info, wouldn't be surprised if its some weird settings
#
# command_1 = bytes.fromhex("f0 f0")  # wait until f0 recieved afterwards
# command_2 = bytes.fromhex("e8")  # 'pre-command' command
# # command_3 = bytes.fromhex("aa 01 00 00 00 20 41 00 00 20 41 00 00 20 41 00 00 00 1f 43 00")  # actual command
# command_3 = bytes.fromhex("aa 01 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 01 00")  # test empty
# command_4 = bytes.fromhex("f1 f1")  # wait until f1 recieved afterwards
#
# # writing command so fisnar knows to listen
# fisnar.write(command_1)
# print("command 1 (" + str(command_1) + ") sent")
# command_1_ret = fisnar.read_until(expected=bytes.fromhex("f0"))
# if command_1_ret == bytes.fromhex("f0"):
#     print("f0 recieved. proceeding...")
#
#     # writing actual command (and xe8 pre command)
#     fisnar.write(command_2)
#     print("command 2 (" + str(command_2) + ") sent")
#     fisnar.write(command_3)
#     print("command 3 (" + str(command_3) + ") sent")
#     command_3_ret = fisnar.read_until(expected=bytes.fromhex("01"))
#     if command_3_ret == bytes.fromhex("01"):
#         print("checksum recieved, proceeding...")
#
#         # writing 'end' command
#         fisnar.write(command_4)
#         print("command 4 (" + str(command_4) + ") sent")
#         command_4_ret = fisnar.read_until(expected="f1")
#         if command_4_ret == bytes.fromhex("f1"):
#             print("f1 recieved. all done")



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



# if __name__ == "__main__":
#     testFloat = 15.123
#     print(testFloat, getSinglePrecisionBits(testFloat))





















# space saver
