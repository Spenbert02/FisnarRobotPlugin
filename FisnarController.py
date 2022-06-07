import serial

from UM.Logger import Logger


class FisnarController:
    # class to handle controlling the fisnar via the RS-232 port. Once an
    # object is given commands, it can upload them to the Fisnar


    # static member variables
    COM_PORT = 7


    def __init__(self):
        # error message
        self.information = None

        # serial port object
        self.serial_port = serial.Serial(FisnarController.COM_PORT, 115200, serial.EIGHTBITS, serial.PARITY_NONE, serial.STOPBITS_ONE, timeout=10)

        # fisnar commands
        self.fisnar_commands = None


    def setInformation(self, info):
        # set the error information
        self.information = str(info)


    def getInformation(self):
        # get error information
        if self.information is None:
            return "<no err msg set>"
        else:
            return str(self.information)


    def writeBytes(self, byte_array):
        # function to write bytes over the serial port. Exists as a separate
        # function for debugging purposes

        # actual use
        self.serial_port.write(byte_array)

        # # debugging small number of commands
        # Logger.log("d", str(byte_array))

        # # debugging, if too many commands to write
        # pass


    def readUntil(self, last_byte):
        # function to read from the serial port until a certain byte is found

        # actual use
        return self.serial_port.readuntil(last_byte)

        # # debugging
        # return last_byte


    def readLine(self):
        # read line from the input buffer
        return self.serial_port.readline()


    def setCommands(self, command_list):
        # set the fisnar commands to be uploaded
        self.fisnar_commands = command_list


    def runCommands(self):
        # run the previously uploaded fisnar commands to the fisnar

        # making sure fisnar commands exist
        if self.fisnar_commands is None:
            self.setInformation("slicer output must be saved as CSV before uploading to fisnar")
            return False

        for command in self.fisnar_commands:
            pass


if __name__ == "__main__":
    pass
