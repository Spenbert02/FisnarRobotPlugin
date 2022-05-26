import serial


class SerialUploader:
    # a class that can be used similarly to the AutoUploader class, but
    # instead of uploading using mouse/keyboard predetermined commands
    # with the Smart Robot Edit software, it uploads the commands directly
    # over the RS 232 port.


    COM_PORT = "COM7"  # COM port to write commands to


    def __init__(self):
        self.fisnar_commands = None
        self.command_byte_arrays = None  # this doesn't really need to be a member variable, but can't hurt to have


    def setCommands(fisnar_commands):
        pass


    def clearFisnarStoredCommands():
        pass


    def uploadCommands():
        pass


    @staticmethod
    def getCommandBytes(fisnar_commands):
        # given a list of fisnar commands, get a list of sequential commands
        # as a list of byte arrays

        ret_byte_arrays  = []

        for i in range(len(fisnar_commands)):
            command = fisnar_commands[i]  # current fisnar command
            curr_bytes = bytes.fromhex("aa")  # current bytes to be generated

            # accounting for command number
            command_num = i + 1
            if command_num <= 65535:
                curr_bytes += command_num.to_bytes(2, byteorder="little")
            else:  # this is an error - undoable with the current command understanding
                pass

            # forking decision-making by fisnar command here until checksum
            if command[0] == "Dummy Point":
                for j in range(1, 4):  # appending parameters 1, 2, and 3
                    curr_bytes += SerialUploader.flipByteArray(SerialUploader.getByteArrayFromBitstring(SerialUploader.getSinglePrecisionBits(float(command[j]))))

                curr_bytes += bytes.fromhex("00 00 00 1f")

            elif command[0] == "Line Speed":
                pass
            elif command[0] == "Output":
                pass
            else:  # error, not one of the above acceptable commands
                pass

            # adding checksum and final x00 byte
            curr_bytes += SerialUploader.getCheckSum(curr_bytes[1:])
            curr_bytes += bytes.fromhex("00")

            ret_byte_arrays.append(curr_bytes)

        return ret_byte_arrays


    @staticmethod
    def getCheckSum(bytes_to_sum):
        # get the checksum of a byte array. This checksum is the sum of all byte
        # ascii values, truncated to the rightmost 8 bits (total sum mod 256)

        tally = 0
        for b in bytes_to_sum:
            tally += b

        return (tally % 256).to_bytes(1, byteorder="big")


    @staticmethod
    def getByteArrayFromBitstring(bitstring):
        # given a string object of only ones and zeros, return a byte array
        # containing the equivalent bytes, in the same order. For now, the
        # bitstring must be 32 bits long

        ret_bytes = bytes()

        for i in range(4):
            curr_bits = bitstring[i * 8:(i + 1) * 8]
            ret_bytes += int(curr_bits, 2).to_bytes(1, byteorder="big")

        return ret_bytes



    @staticmethod
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

        # putting it all together
        ret_bits = sign_bit + exp_bits + mantissa_bits
        print(ret_bits)  # test
        return(ret_bits)


    @staticmethod
    def flipByteArray(bytes_to_flip):
        # given a byte array, return the byte array in reversed order

        ret_bytes = bytes()
        for i in range(len(bytes_to_flip) - 1, -1, -1):
            ret_bytes += bytes_to_flip[i].to_bytes(1, byteorder="big")

        return ret_bytes


# testing station
if __name__ == "__main__":
    sample_commands = [
    ["Dummy Point", 0, 0, 0],
    ["Dummy Point", 1, 1, 1],
    ["Output", 1, 0],
    ["Line Speed", 12.34]
    ]

    byte_commands = SerialUploader.getCommandBytes(sample_commands)

    for command in byte_commands:
        print(command)

    # byte_array = SerialUploader.getByteArrayFromBitstring(SerialUploader.getSinglePrecisionBits(123.123))
