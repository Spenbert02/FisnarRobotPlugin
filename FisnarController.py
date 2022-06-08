import serial
import time
from UM.Logger import Logger


class FisnarController:
    # class to handle controlling the fisnar via the RS-232 port. Once an
    # object is given commands, it can upload them to the Fisnar


    # static member variables
    COM_PORT = "COM7"
    FEEDBACK_COMMANDS = (bytes("PX\r", "ascii"), bytes("PY\r", "ascii"), bytes("PZ\r", "ascii"))

    INITIALIZER = bytes.fromhex("f0 f0 f2")
    FINALIZER = bytes.fromhex("df 00")
    OK = bytes("ok!", "ascii")


    def __init__(self):
        # error message
        self.information = None

        # # serial port object - uncomment this for actual use
        # self.serial_port = serial.Serial(FisnarController.COM_PORT, 115200, serial.EIGHTBITS, serial.PARITY_NONE, serial.STOPBITS_ONE, timeout=30)

        # fisnar commands
        self.fisnar_commands = None

        # current position (automatically updated by Px, PY, and PZ commands)
        self.current_position = [None, None, None]

        # test for stuff
        self.test_val = 0.0


    def getCurrentProgress(self):
        # test for progress update stuff
        Logger.log("i", "current progress returned: " + str(self.test_val))
        return self.test_val


    def test(self):
        # test for progress update stuff
        for i in range(10000):
            Logger.log("i", "looping: " + str(i))
            self.test_val = i / 10000.0


    def setInformation(self, info):
        # set the error information
        self.information = str(info)


    def getInformation(self):
        # get error information
        if self.information is None:
            return "<no err msg set>"
        else:
            return str(self.information)


    def getCurrentPosition(self):
        # get the current position of the fisnar as it is running
        return self.current_position


    def writeBytes(self, byte_array):
        # function to write bytes over the serial port. Exists as a separate
        # function for debugging purposes

        # # actual use
        # self.serial_port.write(byte_array)

        # # debugging small number of commands
        # Logger.log("d", str(byte_array))

        # debugging, if too many commands to write
        pass


    def readUntil(self, last_byte):
        # function to read from the serial port until a certain byte is found

        # # actual use
        # return self.serial_port.read_until(last_byte)

        # debugging
        return last_byte


    def readLine(self):
        # read line from the input buffer

        # # actual use
        # return self.serial_port.readline()

        # debug
        pass


    def read(self, num_bytes):
        # read a given number of bytes from the input buffer

        # # actual use
        # return self.serial_port.read(num_bytes)

        # debug
        pass


    def setCommands(self, command_list):
        # set the fisnar commands to be uploaded
        self.fisnar_commands = command_list


    def runCommands(self):
        # run the previously uploaded fisnar commands to the fisnar

        # making sure fisnar commands exist
        if self.fisnar_commands is None:
            self.setInformation("slicer output must be saved as CSV before uploading to fisnar")
            return False

        # initializing
        confirmation = self.sendCommand(FisnarController.INITIALIZER)
        if not confirmation:
            return False

        # homing, to start
        confirmation = self.sendCommand(self.HM())
        if not confirmation:
            return False

        # iterating over commands
        for command in self.fisnar_commands:
            if command[0] == "Dummy Point":
                x, y, z = [float(a) for a in command[1:]]  # getting command coordinates as floats

                # movement command
                confirmation = self.sendCommand(self.VA(x, y, z))
                if not confirmation:
                    return False

                # waiting until machine moves to desired position
                confirmation = self.sendCommand(self.ID())
                if not confirmation:
                    return False

                # update current x, y, and z positions after moving
                confirmation = self.sendCommand(self.PX())
                if not confirmation:
                    return False

                confirmation = self.sendCommand(self.PY())
                if not confirmation:
                    return False

                confirmation = self.sendCommand(self.PZ())
                if not confirmation:
                    return False

            elif command[0] == "Output":
                confirmation = self.sendCommand(self.OU(int(command[1]), int(command[2])))
                if not confirmation:
                    return False

            elif command[0] == "Line Speed":
                speed = float(command[1])  # getting speed parameter as float

                confirmation = self.sendCommand(self.SP(speed))
                if not confirmation:
                    return False

            elif command[0] == "End Program":  # I don't think anything has to be done with this
                pass

            else:
                self.setInformation("Unrecognized command in fisnar command list: " + str(command[0]))
                return False

        # homing again, after all commands are done
        confirmation = self.sendCommand(FisnarController.FINALIZER)
        if not confirmation:
            return False

        return True  # if no errors have triggered so far, all good


    def sendCommand(self, command_bytes):
        # write a given command to the fisnar. return false if confirmation
        # recieved, false otherwise

        if command_bytes == FisnarController.INITIALIZER:  # initialization command
            self.writeBytes(command_bytes)
            confirmation = self.readLine()
            if confirmation == bytes.fromhex("f0") + bytes("<< BASIC BIOS 2.2 >>\r\n", "ascii"):
                return True
            else:
                self.setInformation("initializer confirmation failed. Bytes recieved: " + str(confirmation))
                return False

        elif command_bytes == FisnarController.FINALIZER:  # finalization command
            self.writeBytes(command_bytes)
            return True  # nothing is being recieved from the fisnar, so can't go wrong here

        else:  # any other command
            self.writeBytes(command_bytes)  # write bytes
            confirmation = self.read(len(command_bytes) + 1)  # read same bytes back, plus "\n" character

            if command_bytes in FisnarController.FEEDBACK_COMMANDS:
                new_coord = float(self.readLine())
                self.current_position[FisnarController.FEEDBACK_COMMANDS.index(command_bytes)] = new_coord  # updating coordinate

            if confirmation == (command_bytes + bytes("\n", "ascii")):
                ok_response = self.read(5)  # read 5 bytes - looking for "ok!\r\n" response
                if ok_response == FisnarController.OK + bytes("\r\n", "ascii"):
                    return True
                else:
                    self.setInformation("failed to recieve 'ok!' confirmation. Actual response: " + str(ok_response))
                    return False
            else:
                self.setInformation("command failed to send. Bytes sent: " + str(command_bytes) + "Bytes recieved: " + str(confirmation))
                return False


    def OU(self, port, on_off):
        return bytes("OU " + str(port) + ", " + str(on_off) + "\r", "ascii")


    def SP(self, speed):
        return bytes("SP " + str(speed) + "\r", "ascii")


    def PX(self):
        return FisnarController.FEEDBACK_COMMANDS[0]


    def PY(self):
        return FisnarController.FEEDBACK_COMMANDS[1]


    def PZ(self):
        return FisnarController.FEEDBACK_COMMANDS[2]


    def VA(self, x, y, z):
        return bytes("VA " + str(x) + ", " + str(y) + ", " + str(z) + "\r", "ascii")


    def VX(self, x):
        return bytes("VX " + str(x) + "\r", "ascii")


    def VY(self, y):
        return bytes("VY " + str(y) + "\r", "ascii")


    def VZ(self, z):
        return bytes("VZ " + str(z) + "\r", "ascii")


    def HM(self):
        return bytes("HM\r", "ascii")


    def HX(self):
        return bytes("HX\r", "ascii")


    def HY(self):
        return bytes("HY\r", "ascii")


    def HZ(self):
        return bytes("HZ\r", "ascii")


    def ID(self):
        return bytes("ID\r", "ascii")


if __name__ == "__main__":
    fc = FisnarController()
    fc.setCommands([
        ["Output", 4, 1],
        ["Line Speed", 20],
        ["Dummy Point", 50, 10, 10],
        ["Line Speed", 30],
        ["Dummy Point", 0, 0, 0],
        ["Output", 4, 0]
        ])
    print(fc.runCommands(), fc.getInformation())
