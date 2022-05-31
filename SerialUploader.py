import serial


class SerialUploader:
    # a class that can be used similarly to the AutoUploader class, but
    # instead of uploading using mouse/keyboard predetermined commands
    # with the Smart Robot Edit software, it uploads the commands directly
    # over the RS 232 port.


    COM_PORT = "COM7"  # COM port to write commands to
    START_COMMANDS = 2  # symbol for starting commands
    END_COMMANDS = 3  # symbol for ending commands
    LAST_COMMAND = 4  # symbol for last command to send - the empty command with '4000' as a parameter


    def __init__(self):
        self.fisnar_commands = None  # fisnar commands that can be externally set
        self.information = None  # error information that can be retrieved externally

        # creating serial port object
        self.serial_port = serial.Serial(SerialUploader.COM_PORT, 115200, serial.EIGHTBITS, serial.PARITY_NONE, serial.STOPBITS_ONE, timeout=10)


    def getInformation(self):
        # get the error information attribute - if an error occured during the most
        # recent conversion process, this attribute will contain useful information that
        # should be shown to the user. If no errors were detected, this attribute
        # is just None

        if self.information is None:
            return "<No Error Info Found>"
        else:
            return self.information


    def setInformation(self, information):
        # set error information. This is just a function for code readability
        # purposes
        self.information = information


    def setCommands(self, fisnar_commands):
        # set the fisnar command list to be uploaded during the serial upload process=
        self.fisnar_commands = fisnar_commands


    def uploadCommands(self):
        # upload the previously set commands to the fisnar. the last command that
        # is given here should always be an 'end program' command.

        if self.fisnar_commands is None:
            self.setInformation("slicer output must be saved as CSV file before uploading")
            return

        for i in range(len(self.fisnar_commands)):
            pass  # tODO


    def sendCommand(self, command, command_num):
        # write a given command to the fisnar through the serial port - returning
        # false if an error occurs and returning true if no error occurs. 'command'
        # parameter can be either a fisnar command of type 'Dummy Point', 'Line Speed',
        # or 'Output', or it can be None to signal an empty command, or it can
        # be START_COMMANDS to send f0 starting sequence, or it can be END_COMMANDS
        # to send f1 ending sequence

        if self.serial_port is None:  # ensuring the port exists
            self.setInformation("serial port not initialized")
            return False

        if command is SerialUploader.START_COMMANDS:  # send starting command
            self.serial_port.write(bytes.fromhex("f0 f0"))
            confirmation = self.serial_port.read_until(bytes.fromhex("f0"))
            if confirmation == bytes.fromhex("f0"):  # f0 confirmation recieved
                return True
            else:  # timeout, f0 confirmation not recieved
                self.setInformation("unsuccessful command upload initialization")
                return False
        elif command is SerialUploader.END_COMMANDS:  # send ending commands
            self.serial_port.write(bytes.fromhex("f1 f1"))
            confirmation = self.serial_port.read_until(bytes.fromhex("f1"))
            if confirmation == bytes.fromhex("f1"):  # f1 confirmation recieved
                return True
            else:  # no confirmation recieved
                self.setInformation("unsuccessful command upload finalization")
                return False
        elif command is None:  # send empty command
            # getting command number in byte form. command number must be under 65536
            command_num = command_num % 65536  # just in case. should probably throw an error here. this works for now
            command_num_bytes = command_num.to_bytes(2, byteorder="little")

            # getting checksum byte for empty command (dependent only on command number, all other bytes are constant)
            checksum_byte = SerialUploader.getCheckSum(command_num_bytes + bytes.fromhex("13"))

            # putting together into single byte array
            command_bytes = bytes.fromhex("aa") + command_num_bytes + bytes.fromhex("00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 13") + checksum_byte + bytes.fromhex("00")

            self.serial_port.write(command_bytes)
            confirmation = self.serial_port.read_until(checksum_byte)
            if confirmation == checksum_byte:
                return True
            else:
                self.setInformation("'Empty' command failed to send.")
                return False
        else:  # actual command to send
            pass  # TODO


    @staticmethod
    def getCommandBytes(command, command_num):
        # given a list of fisnar commands, get a list of sequential commands
        # as a list of byte arrays

        ret_bytes = bytes.fromhex("aa")  # current bytes to be generated

        # accounting for command number
        if command_num <= 65535:
            ret_bytes += command_num.to_bytes(2, byteorder="little")
        else:  # this is an error - undoable with the current command understanding
            pass

        # forking decision-making by fisnar command here until checksum
        if command[0] == "Dummy Point":
            for i in range(1, 4):  # appending parameters 1, 2, and 3
                ret_bytes += SerialUploader.flipByteArray(SerialUploader.getByteArrayFromBitstring(SerialUploader.getSinglePrecisionBits(float(command[i]))))

            ret_bytes += bytes.fromhex("00 00 00 1f")

        elif command[0] == "Line Speed":
            ret_bytes += SerialUploader.flipByteArray(SerialUploader.getByteArrayFromBitstring(SerialUploader.getSinglePrecisionBits(float(command[1]))))
            ret_bytes += bytes.fromhex("00 00 00 00 00 00 00 00")  # params 2 and 3
            ret_bytes += bytes.fromhex("00 00 00 01")  # command bytes

        elif command[0] == "Output":
            for i in range(1, 3):
                ret_bytes += SerialUploader.flipByteArray(SerialUploader.getByteArrayFromBitstring(SerialUploader.getSinglePrecisionBits(float(command[i]))))
            ret_bytes += bytes.fromhex("00 00 00 00")  # param 3
            ret_bytes += bytes.fromhex("d7 a3 42 42")  # command bytes

        elif command[0] == "End Program":
            ret_bytes += bytes.fromhex("00 00 00 00 00 00 00 00 00 00 00 00")  # all param bytes are x00
            ret_bytes += bytes.fromhex("00 00 00 0b")  # command byte

        else:  # error, not one of the above acceptable commands
            pass

        # adding checksum and final x00 byte
        ret_bytes += SerialUploader.getCheckSum(ret_bytes[1:])
        ret_bytes += bytes.fromhex("00")

        return ret_bytes



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

        # special case checking (because the below code gets messed up if there's no ones in the returned binary string)
        if abs(number) < 0.00001:  # number is basically zero, for the purposes of this plugin.
            return "00000000000000000000000000000000"  # kind of hacky but it works

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
    ["Dummy Point", 10, 10, 1]
    ]


    # testing for how to end commands (writing 4000 empty commands first)
    port = serial.Serial(SerialUploader.COM_PORT, 115200, serial.EIGHTBITS, serial.PARITY_NONE, serial.STOPBITS_ONE, timeout=10)

    port.write(bytes.fromhex("f0 f0"))
    confirm = port.read_until(bytes.fromhex("f0"))
    print(confirm)

    port.write(bytes.fromhex("e8"))
    port.write(SerialUploader.getCommandBytes(["Dummy Point", 10, 10, 10], 1))
    confirm = port.read_until(bytes.fromhex("43"))
    print(confirm)

    for i in range(2, 4001):
        command_num = i + 1
        curr_bytes = bytes.fromhex("aa")
        curr_bytes += command_num.to_bytes(2, byteorder="little")
        curr_bytes += bytes.fromhex("00 00 00 00 00 00 00 00 00 00 00 00")
        curr_bytes += bytes.fromhex("00 00 00 13")
        checksum_byte = SerialUploader.getCheckSum(curr_bytes[1:])
        curr_bytes += checksum_byte
        curr_bytes += bytes.fromhex("00")

        port.write(bytes.fromhex("e8"))
        port.write(curr_bytes)
        confirm = port.read_until(checksum_byte)
        print(confirm)

    port.write(bytes.fromhex("e8"))
    port.write(SerialUploader.getCommandBytes(["Dummy Point", 20, 20, 0], 4001))
    confirm = port.read_until(bytes.fromhex("91"))
    print(confirm)


    # # test for how to end commands
    # line_speed_bytes_1 = SerialUploader.getCommandBytes(["Line Speed", 20.1], 1)
    # dummy_point_bytes = SerialUploader.getCommandBytes(["Dummy Point", 10, 10, 10], 2)  # checksum is x44
    # last_command = bytes.fromhex("aa 03 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 13 16 00")
    # line_speed_bytes_2 = SerialUploader.getCommandBytes(["Line Speed", 20.1], 4)
    #
    #
    # port = serial.Serial(SerialUploader.COM_PORT, 115200, serial.EIGHTBITS, serial.PARITY_NONE, serial.STOPBITS_ONE, timeout=10)
    #
    # port.write(bytes.fromhex("f0 f0"))
    # confirm = port.read_until(bytes.fromhex("f0"))
    # print(confirm)
    #
    # port.write(bytes.fromhex("e8"))
    # port.write(line_speed_bytes_1)
    # confirm = port.read_until(bytes.fromhex("7b"))
    # print(confirm)
    #
    # port.write(bytes.fromhex("e8"))
    # port.write(dummy_point_bytes)
    # confirm = port.read_until(bytes.fromhex("44"))
    # print(confirm)
    #
    # port.write(bytes.fromhex("e8"))
    # port.write(last_command)
    # confirm = port.read_until(bytes.fromhex("16"))
    # print(confirm)
    #
    # # port.write(bytes.fromhex("e8"))
    # # port.write(line_speed_bytes_2)
    # # confirm = port.read_until(bytes.fromhex("7f"))
    # # print(confirm)
    #
    # port.write(bytes.fromhex("f1 f1"))
    # confirm = port.read_until(bytes.fromhex("f1"))
    # print(confirm)


    # byte_array = SerialUploader.getByteArrayFromBitstring(SerialUploader.getSinglePrecisionBits(123.123))
