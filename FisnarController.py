import copy
import serial
import time
import threading


class FisnarController:
    # class to handle controlling the fisnar via the RS-232 port. Once an
    # object is given commands, it can upload them to the Fisnar


    # 'setting' variables
    COM_PORT = "COM7"

    # byte constants
    FEEDBACK_COMMANDS = (bytes("PX\r", "ascii"), bytes("PY\r", "ascii"), bytes("PZ\r", "ascii"))
    INITIALIZER = bytes.fromhex("f0 f0 f2")
    FINALIZER = bytes.fromhex("df 00")
    OK = bytes("ok!", "ascii")

    # to turn on or off debugging mode
    DEBUG_MODE = False

    # for error reporting
    SERIAL_ERR_MSG = "Failed to connect to Fisnar serial port. Reconnection will be attempted when commands are next uploaded. Ensure the Fisnar is on and connected to the proper COM port, and ensure no other apps are using the COM port."


    def __init__(self):
        # error message
        self.information = None

        # trying to initialize serial port
        self.serial_port = None
        if not FisnarController.DEBUG_MODE:
            self.serial_port = self.initializeSerialPort()  # try to get serial port object
            if self.serial_port is None:
                self.setInformation("Couldn't open serial port: " + str(FisnarController.COM_PORT))

        # fisnar commands
        self.fisnar_commands = None

        # for real-time uploading - used to terminate mid-print and report whether print was successful
        self.terminate_running = False
        self.successful_print = None

        # printing progress and requisite lock to prevent race condition
        self.print_progress = None
        self.lock = threading.Lock()

        # current position (automatically updated by Px, PY, and PZ commands)
        self.current_position = [None, None, None]


    def initializeSerialPort(self):
        # get the serial port object. If it can't be initialized, will return None
        try:
            return serial.Serial(FisnarController.COM_PORT, 115200, serial.EIGHTBITS, serial.PARITY_NONE, serial.STOPBITS_ONE, timeout=30)
        except:
            if not FisnarController.DEBUG_MODE:
                Logger.log("w", "failed to initialize FisnarController serial port")
            return None


    def initialized(self):
        # check if the serial port has been successfully opened
        return self.serial_port is not None


    def resetInternalState(self):
        # function to be called after uploading a file
        self.information = None
        self.terminate_running = False
        self.successful_print = None
        self.current_position = [None, None, None]


    def setInformation(self, info):
        # set the error information
        self.information = str(info)


    def getInformation(self):
        # get error information
        if self.information is None:
            return "<no err msg set>"
        else:
            return str(self.information)


    def setPrintProgress(self, val):
        # set the printing progress
        self.lock.acquire()
        self.print_progress = val
        self.lock.release()


    def getPrintingProgress(self, val):
        # get the printing progress
        self.lock.acquire()
        ret_val = self.print_progress
        self.lock.release()
        return ret_val


    def getCurrentPosition(self):
        # get the current position of the fisnar as it is running
        return self.current_position


    def writeBytes(self, byte_array):
        # function to write bytes over the serial port. Exists as a separate
        # function for debugging purposes

        if FisnarController.DEBUG_MODE:
            # Logger.log("d", str(byte_array))  # can be used for small prints
            pass
        else:
            self.serial_port.write(byte_array)


    def readUntil(self, last_byte):
        # function to read from the serial port until a certain byte is found

        if FisnarController.DEBUG_MODE:
            pass
        else:
            return self.serial_port.read_until(last_byte)


    def readLine(self):
        # read line from the input buffer

        if FisnarController.DEBUG_MODE:
            pass
        else:
            return self.serial_port.readline()


    def read(self, num_bytes):
        # read a given number of bytes from the input buffer

        if FisnarContrller.DEBUG_MODE:
            pass
        else:
            return self.serial_port.read(num_bytes)


    def setCommands(self, command_list):
        # set the fisnar commands to be uploaded
        self.fisnar_commands = command_list


    def runCommands(self):
        # run the previously uploaded fisnar commands to the fisnar

        def setSuccessfulPrint(tf):
            # set whether the print was successful or not. If not, then a
            # finalizer command should be sent
            self.successful_print = tf
            if not tf:
                self.sendCommand(FisnarController.FINALIZER)

        # beginning progress tracking
        self.print_progress = 0
        time.sleep(2)
        self.print_progress = .54321
        time.sleep(2)

        # ensuring serial port is/can be opened
        if self.serial_port is None:
            self.serial_port = self.initializeSerialPort()
            if self.serial_port is None:  # still couldn't open
                self.setInformation(FisnarController.SERIAL_ERR_MSG)

                # return False, effectively
                setSuccessfulPrint(False)
                return

        # making sure fisnar commands exist
        if self.fisnar_commands is None:
            self.setInformation("slicer output must be saved as CSV before uploading to fisnar")

            # 'return False'
            setSuccessfulPrint(False)
            return

        # initializing
        confirmation = self.sendCommand(FisnarController.INITIALIZER)
        if not confirmation:
            # 'return False'
            setSuccessfulPrint(False)
            return

        # homing, to start
        confirmation = self.sendCommand(self.HM())
        if not confirmation:
            # 'return False'
            setSuccessfulPrint(False)
            return

        # iterating over commands
        i = 0
        while (i < len(self.fisnar_commands)) and (not self.terminate_running):
            command = self.fisnar_commands[i]
            self.print_progress = i / len(self.fisnar_commands)  # updating progress

            if command[0] == "Dummy Point":
                x, y, z = [float(a) for a in command[1:]]  # getting command coordinates as floats

                # movement command
                confirmation = self.sendCommand(self.VA(x, y, z))
                if not confirmation:
                    # 'return False'
                    setSuccessfulPrint(False)
                    return

                # waiting until machine moves to desired position
                confirmation = self.sendCommand(self.ID())
                if not confirmation:
                    # 'return False'
                    setSuccessfulPrint(False)
                    return

            elif command[0] == "Output":
                confirmation = self.sendCommand(self.OU(int(command[1]), int(command[2])))
                if not confirmation:
                    # 'return False'
                    setSuccessfulPrint(False)
                    return

            elif command[0] == "Line Speed":
                speed = float(command[1])  # getting speed parameter as float

                confirmation = self.sendCommand(self.SP(speed))
                if not confirmation:
                    # 'return False'
                    setSuccessfulPrint(False)
                    return

            elif command[0] in ("End Program", "Z Clearance"):  # I don't think anything has to be done with this
                pass

            else:
                self.setInformation("Unrecognized command in fisnar command list: " + str(command[0]))
                # 'return False'
                setSuccessfulPrint(False)
                return

            i += 1

        if not self.terminate_running:  # loop wasn't terminated
            # homing, to start
            confirmation = self.sendCommand(self.HM())
            if not confirmation:
                # 'return False'
                setSuccessfulPrint(False)
                return

        # sending finalizer regardless of whether loop was terminated
        confirmation = self.sendCommand(FisnarController.FINALIZER)
        if not confirmation:
            # 'return False'
            setSuccessfulPrint(False)
            return

        if not self.terminate_running:  # loop wasn't terminated
            # if no errors have triggered so far, all good
            setSuccessfulPrint(True)
            return  # will return anyway, so this isn't really necessary


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


    @staticmethod
    def readFisnarCommandsFromFile(file_abspath):
        """
        this will break down if the file doesn't exist. This is for development,
        so just make sure the file exists. Returns a 2D array of fisnar commands in the expected format
        """

        # get the csv cells into a 2D array (again, no error checking)
        csv_file = open(file_abspath, "r")
        command_str = csv_file.read()
        commands = [line.split(",") for line in command_str.split("\n")]

        # converting all 2D array entries into proper types
        i = 0
        while i < len(commands):
            if commands[i][0] == "Output":
                for j in range(1, 3):
                    commands[i][j] = int(commands[i][j])
            elif commands[i][0] == "Dummy Point":
                for j in range(1, 4):
                    commands[i][j] = float(commands[i][j])
            elif commands[i][0] == "Line Speed":
                commands[i][1] = float(commands[i][1])
            elif commands[i][0] == "Z Clearance":
                commands[i][1] = int(commands[i][1])
            elif commands[i][0][:11] == "End Program":
                pass
            elif commands[i][0] in ("Line Start", "Line End", "Line Passing"):
                for j in range(1, 4):
                    commands[i][j] = float(commands[i][j])
            else:
                commands.pop(i)
                i -= 1
                print("Unexpected command: " + str(commands[i][0]))  # for debugging
            i += 1

        return copy.deepcopy(commands)


if __name__ == "__main__":
    filepath = "C:\\Users\\Lab\Desktop\\G-code Project\\single_extruder_testing\\CFFFP_5x5x5_cube.csv"
    fisnar_commands = readFisnarCommandsFromFile(filepath)

    fc = FisnarController()
    fc.setCommands(fisnar_commands)
    print(fc.runCommands(), fc.getInformation())


if not FisnarController.DEBUG_MODE:  # importing UM if not in debug mode
    from UM.Logger import Logger
