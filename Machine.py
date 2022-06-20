import serial

from abc import ABC, abstractmethod

class Machine(ABC):
    # class that represents a physical machine, that deals with opening serial
    # ports and sending/recieving bytes

    STX = bytes.fromhex("02")
    ETX = bytes.fromhex("03")
    EOT = bytes.fromhex("04")
    ENQ = bytes.fromhex("05")
    ACK = bytes.fromhex("06")


    def __init__(self, port_name, *args):
        # default serial port settings
        self.port_name = port_name
        self.baud_rate = 9600
        self.num_bits = serial.EIGHTBITS
        self.parity_bits = serial.PARITY_NONE
        self.num_stop_bits = serial.STOPBITS_ONE
        self.read_timeout = 10
        self.write_timeout = 10

        # assigning any arguments given in args
        for i in range(len(args)):
            if i == 0:
                self.baud_rate = args[0]
            elif i == 1:
                self.num_bits = args[1]
            elif i == 2:
                self.parity_bits = args[2]
            elif i == 3:
                self.num_stop_bits = args[3]
            elif i == 4:
                self.read_timeout = args[4]
            elif i == 5:
                self.write_timeout = args[5]

        # information to set for error messages
        self.information = None

        # actual serial port object
        self.serial_port = None
        self.initializeSerialPort()  # try to initialize

    @abstractmethod
    def sendCommand(self, command_bytes):
        # send a command to the machine - return True if confirmation recieved,
        # or otherwise False
        pass

    @abstractmethod
    def sendFeedbackCommand(self, command_bytes):
        # send a command to the machine - return the recieved information
        # bytes if successful, or otherwise False
        pass

    def getInformation(self):
        # get information from Machine instance
        if self.information is None:
            return "<No Errors Found>"
        else:
            return str(self.information)

    def setInformation(self, info):
        # set information of Machine instance
        if info is None:
            self.information = None
        else:
            self.information = str(info)

    def initializeSerialPort(self):
        # try to initialize the serial port - return bool indicating successfulness
        try:
            self.serial_port = serial.Serial(
                self.port_name,
                self.baud_rate,
                self.num_bits,
                self.parity_bits,
                self.num_stop_bits,
                timeout=self.read_timeout,
                write_timeout=self.write_timeout
            )
        except serial.SerialException:
            self.serial_port = None
            self.setInformation("failed to initialize serial port")

    def isInitialized(self):
        # get a bool indicating whether or not the serial port has been successfully initialized
        return self.serial_port is not None

    def writeBytes(self, byte_array):
        # write bytes to serial port
        self.serial_port.write(byte_array)

    def readLine(self):
        # read line and return it
        return self.serial_port.readline()

    def read(self, num_bytes):
        # read a specified number of bytes
        return self.serial_port.read(num_bytes)

    def readUntil(self, byte_array):
        # read until a given byte (or byte_array) is found
        return self.serial_port.read_until(byte_array)

    def getDebugString(self):
        ret_str = "Debug String:\nself.port_name: " + str(self.port_name) +\
            "\nself.baud_rate: " + str(self.baud_rate) +\
            "\nself.num_bits: " + str(self.num_bits) +\
            "\nself.parity_bits: " + str(self.parity_bits) +\
            "\nself.num_stop_bits: " + str(self.num_stop_bits) +\
            "\nself.read_timeout: " + str(self.read_timeout) +\
            "\nself.write_timeout: " + str(self.write_timeout) +\
            "\nself.serial_port: " + str(self.serial_port) +\
            "\nself.information: " + str(self.information)
        return ret_str

    def updateSerialPort(self):
        # update the SerialPort object with the Machine instance's member variables
        if self.serial_port is not None:
            self.serial_port.baudrate = self.baud_rate
            self.serial_port.bytesize = self.num_bits
            self.serial_port.parity = self.parity_bits
            self.serial_port.stopbits = self.num_stop_bits
            self.serial_port.timeout = self.read_timeout
            self.serial_port.write_timeout = self.write_timeout

    def setBaudrate(self, baud_rate):
        # set baudrate for serial port (updates member attribute as well)
        self.baud_rate = baud_rate
        self.updateSerialPort()

    def setNumBits(self, num_bits):
        # set size of byte for serial port communication protocol. Always use the
        # PySerial predefined values
        self.num_bits = num_bits
        self.updateSerialPort()

    def setParityBits(self, parity_bits):
        # set the type of parity for the serial port. Always use the PySerial
        # predefined values
        self.parity_bits = parity_bits
        self.updateSerialPort()

    def setStopBits(self, stop_bits):
        # set the numnber of stop bits for the serial port. Always use the PySerial
        # predefined values
        self.num_stop_bits = stop_bits
        self.updateSerialPort()

    def setReadTimeout(self, timeout):
        # set the length of the serial port read timeout (in seconds)
        self.read_timeout = timeout
        self.updateSerialPort()

    def setWriteTimeout(self, timeout):
        # set the length of the serial port write timeout (in seconds)
        self.write_timeout = timeout
        self.updateSerialPort()


if __name__ == "__main__":
    pass
