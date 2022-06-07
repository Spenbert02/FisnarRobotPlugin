import serial
from .SerialUploader import SerialUploader

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


    def setCommands(self, command_lst):
        # set the fisnar commands to be uploaded
        self.fisnar_commands = command_lst


if __name__ == "__main__":
    pass
