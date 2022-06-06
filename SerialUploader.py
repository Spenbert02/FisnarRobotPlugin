import serial
from UM.Logger import Logger


class SerialUploader:
    # a class that can be used similarly to the AutoUploader class, but
    # instead of uploading using mouse/keyboard predetermined commands
    # with the Smart Robot Edit software, it uploads the commands directly
    # over the RS 232 port.

    # enumeration representing starting (0xf0) and ending (0xf1) commands
    START_COMMANDS = 2  # starting command
    END_COMMANDS = 3  # ending command

    # constants - properties of the fisnar's (potentially changeable) settings
    # and the physical setup of the system (namely port #'s)
    COM_PORT = "COM7"  # COM port to write commands to
    MAX_COMMANDS = 32767  # max number of commands that can be sent


    # map correlating commands to their command bytes
    COMMAND_BYTES = {
        "Dummy Point" : bytes.fromhex("00 00 00 1f"),
        "Line Speed" : bytes.fromhex("00 00 00 01"),
        "End Program" : bytes.fromhex("00 00 00 0b"),
        "Output" : bytes.fromhex("d7 a3 42 42"),
        "Empty" : bytes.fromhex("00 00 00 13")
    }


    def __init__(self):
        self.fisnar_commands = None  # fisnar commands that can be externally set
        self.information = None  # error information that can be retrieved externally

        # creating serial port object - should be UNCOMMENTED for actual use
        self.serial_port = serial.Serial(SerialUploader.COM_PORT, 115200, serial.EIGHTBITS, serial.PARITY_NONE, serial.STOPBITS_ONE, timeout=10)


    def writeBytes(self, byte_array):
        # send a byte array through a COM port. This is a separate function to make
        # debugging easier - during debugging, this function can just print bytes.
        # during deployment, this should actually upload to the COM port, obviously.

        self.serial_port.write(byte_array)  # actually upload

        # # this is for debugging: only use this for really short test command sequences
        # Logger.log("d", "sent bytes: " + str(byte_array))

        # # this is for debugging to not log any commands
        # pass


    def readUntil(self, byte):
        # read from the serial port until a certain byte is found. As the above
        # function, this just exists because it makes debugging easier. All this
        # does is call the Serial objects read_until() function.

        return(self.serial_port.read_until(byte))  # actually read

        # return(byte)  # for debugging


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


    def uploadCommands(self):  # STILL NEEDS TO BE TESTED
        # upload the previously set commands to the fisnar. the last command that
        # is given here should always be an 'end program' command. Eventually,
        # this function should be able to handle uploading fisnar command lists
        # with more than the max # (ie, it should be able to recursively segment
        # and upload commands). Also, all error reporting occurs in sendCommand(),
        # and all command checking should occur before sending commands here.
        # Essentially, this function serves as a portal to dump a list of commands
        # commands into the fisnar, and getting a return value indicating whether
        # or not it was successful.

        # the only error checking that happens here - commands need to exist to upload
        if self.fisnar_commands is None:
            self.setInformation("slicer output must be saved as CSV file before uploading")
            return False

        # ensuring that "End Program" is the last command
        if self.fisnar_commands[-1][0] != "End Program":
            Logger.log("d", "'End Program' was not the last fisnar command")
            self.fisnar_commands.append(["End Program"])

        # sending initialization command
        init_confirm = self.sendCommand(SerialUploader.START_COMMANDS, None)
        if not init_confirm:
            return False

        # sending actual commands
        for i in range(len(self.fisnar_commands)):
            command_num = i + 1
            curr_comm_confirm = self.sendCommand(self.fisnar_commands[i], command_num)
            if not curr_comm_confirm:
                return False  # error information will already be set in sendCommand()

        # sending finalization command
        final_confirm = self.sendCommand(SerialUploader.END_COMMANDS, None)
        if not final_confirm:
            return False

        # if the function hasn't returned by this line of code, everything went ok
        return True


    def sendCommand(self, command, command_num):
        # write a given command to the fisnar through the serial port - returning
        # false if an error occurs and returning true if no error occurs. 'command'
        # parameter can be either a fisnar command of type 'Dummy Point', 'Line Speed',
        # or 'Output', or it can be None to signal an empty command, or it can
        # be START_COMMANDS to send f0 starting sequence, or it can be END_COMMANDS
        # to send f1 ending sequence

        # #  UNCOMMENT this for actual use
        if self.serial_port is None:  # ensuring the port exists
            self.setInformation("serial port not initialized")
            return False

        if command is SerialUploader.START_COMMANDS:  # send initialization command
            self.writeBytes(bytes.fromhex("f0 f0"))
            confirmation = self.readUntil(bytes.fromhex("f0"))
            if confirmation == bytes.fromhex("f0"):  # f0 confirmation recieved
                return True
            else:  # timeout, f0 confirmation not recieved
                self.setInformation("unsuccessful command upload initialization")
                return False

        elif command is SerialUploader.END_COMMANDS:  # send finalization commands
            self.writeBytes(bytes.fromhex("f1 f1"))
            confirmation = self.readUntil(bytes.fromhex("f1"))
            if confirmation == bytes.fromhex("f1"):  # f1 confirmation recieved
                return True
            else:  # no confirmation recieved
                self.setInformation("unsuccessful command upload finalization")
                return False

        elif command is None:  # send empty command
            # getting command number in byte form
            command_num_bytes = command_num.to_bytes(2, byteorder="little")

            # getting checksum byte for empty command (dependent only on command number, all other bytes are constant)
            checksum_byte = SerialUploader.getCheckSum(command_num_bytes + bytes.fromhex("13"))

            # putting together into single byte array
            command_bytes = bytes.fromhex("aa") + command_num_bytes + bytes.fromhex("00 00 00 00 00 00 00 00 00 00 00 00 00 00 00 13") + checksum_byte + bytes.fromhex("00")

            self.writeBytes(command_bytes)
            confirmation = self.readUntil(checksum_byte)
            if confirmation == checksum_byte:
                return True
            else:
                self.setInformation("'Empty' command failed to send.")
                return False

        else:  # actual Fisnar command to send
            # getting command bytes from getCommandBytes function and error checking
            command_bytes = SerialUploader.getCommandBytes(command, command_num)
            if command_bytes is False:
                return False  # error information will already be set in getCommandBytes()

            checksum_byte = command_bytes[-2].to_bytes(1, byteorder="big")

            # sending command bytes over and getting checksum confirmation
            self.writeBytes(bytes.fromhex("e8"))
            self.writeBytes(command_bytes)
            confirmation = self.readUntil(checksum_byte)
            if confirmation == checksum_byte:
                return True
            else:
                self.setInformation("Unable to write ''" + command[0] + "' command at index " + str(command_num))
                return False


    @staticmethod
    def getCommandBytes(command, command_num):
        # given a list of fisnar commands, get a list of sequential commands
        # as a list of byte arrays

        ret_bytes = bytes.fromhex("aa")  # current bytes to be generated

        # accounting for command number, this is the only time this function will throw an error
        if command_num <= SerialUploader.MAX_COMMANDS:
            ret_bytes += command_num.to_bytes(2, byteorder="little")
        else:  # this is an error - undoable with the current command understanding
            self.setInformation("out of range command number (" + str(command_num) + " > " + str(SerialUploader.MAX_COMMANDS) + str(")"))
            return False

        # determining parameter representation based on the command type
        if command[0] == "Dummy Point":
            for i in range(1, 4):  # appending parameters 1, 2, and 3
                ret_bytes += SerialUploader.flipByteArray(SerialUploader.getByteArrayFromBitstring(SerialUploader.getSinglePrecisionBits(float(command[i]))))

        elif command[0] == "Line Speed":
            ret_bytes += SerialUploader.flipByteArray(SerialUploader.getByteArrayFromBitstring(SerialUploader.getSinglePrecisionBits(float(command[1]))))
            ret_bytes += bytes.fromhex("00 00 00 00 00 00 00 00")  # params 2 and 3

        elif command[0] == "Output":
            for i in range(1, 3):
                ret_bytes += SerialUploader.flipByteArray(SerialUploader.getByteArrayFromBitstring(SerialUploader.getSinglePrecisionBits(float(command[i]))))
            ret_bytes += bytes.fromhex("d7 a3 42 42")  # param 3

        elif command[0] == "End Program":
            ret_bytes += bytes.fromhex("00 00 00 00 00 00 00 00 00 00 00 00")  # all param bytes are x00

        else:  # error, not one of the above acceptable commands
            self.setInformation("unrecognized command type passed: " + str(command[0]))
            return False

        # adding the command bytes
        ret_bytes += SerialUploader.COMMAND_BYTES[command[0]]

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

    # testing out sending commands
    sample_commands = [
    ["Dummy Point", 10, 10, 1]
    ]

    test_uploader = SerialUploader()

    init_confirm = test_uploader.sendCommand(SerialUploader.START_COMMANDS, None)
    print("f0 successfully sent: ", init_confirm)

    for i in range(32000, 32768):
        if i == 1:
            curr_confirm = test_uploader.sendCommand(["Dummy Point", 0, 0, 0], i)
        elif i == 32767:
            curr_confirm = test_uploader.sendCommand(["End Program"], i)
        elif i == 32766:
            curr_confirm = test_uploader.sendCommand(["Dummy Point", 30, 30, 30], i)
        else:
            curr_confirm = test_uploader.sendCommand(["Line Speed", i % 10], i)


        print("commmand", i, ":", curr_confirm)

    final_confirm = test_uploader.sendCommand(SerialUploader.END_COMMANDS, None)
    print("f1 successfully sent: ", final_confirm)
