import copy
import serial
import time
import threading

from .Fisnar import Fisnar
from .Converter import Converter


class FisnarController:
    # class to handle controlling the fisnar via the RS-232 port. Once an
    # instance is given commands, it can upload them to the Fisnar

    # 'setting' variables
    COM_PORT = "COM7"

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
        self.print_progress = None

        # lock for protecting against race conditions
        self.lock = threading.Lock()

        # current position (automatically updated by Px, PY, and PZ commands)
        self.current_position = [None, None, None]

    def initializeSerialPort(self):
        # get the serial port object. If it can't be initialized, will return None
        try:
            return serial.Serial(FisnarController.COM_PORT, 115200, serial.EIGHTBITS, serial.PARITY_NONE, serial.STOPBITS_ONE, timeout=20, write_timeout=10)
        except:
            if not FisnarController.DEBUG_MODE:
                Logger.log("w", "failed to initialize FisnarController serial port")
            return None

    def initialized(self):
        # check if the serial port has been successfully opened
        return self.serial_port is not None

    def setInformation(self, info):
        # set the error information
        self.information = str(info)

    def getInformation(self):
        # get error information
        if self.information is None:
            return "<no err msg set>"
        else:
            return str(self.information)

    def setTerminateRunning(self, val):
        # set the terminate running status
        self.lock.acquire()
        self.terminate_running = val
        Logger.log("d", "***** terminate running set to: " + str(val))
        self.lock.release()

    def getTerminateRunning(self):
        # get the terminate running status
        return self.terminate_running

    def setPrintProgress(self, val):
        # set the printing progress
        self.lock.acquire()
        self.print_progress = val
        self.lock.release()

    def getPrintingProgress(self):
        # get the printing progress
        return self.print_progress

    def getCurrentPosition(self):
        # get the current position of the fisnar as it is running
        return self.current_position

    def resetInternalState(self):
        # function to be called after uploading a file
        self.information = None
        self.setTerminateRunning(False)
        self.successful_print = None
        self.setPrintProgress(None)
        self.current_position = [None, None, None]

    def turnOffOutputs(self):
        # turn off all outputs on the fisnar
        for i in range(1, 5):
            confirmation = self.sendCommand(Fisnar.OU(i, 0))
            if not confirmation:
                return False
        return True

    def writeBytes(self, byte_array):
        # function to write bytes over the serial port. Exists as a separate
        # function for debugging purposes
        if FisnarController.DEBUG_MODE:
            # Logger.log("d", str(byte_array))  # can be used for small prints
            pass
        else:
            self.serial_port.write(byte_array)

    def readUntil(self, last_byte):
        # function to read from the serial port until a certain byte is foun
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
        if FisnarController.DEBUG_MODE:
            pass
        else:
            return self.serial_port.read(num_bytes)

    def setCommands(self, command_list):
        # set the fisnar commands to be uploaded
        self.fisnar_commands = command_list

    def runCommands(self):
        # run the previously uploaded fisnar commands to the fisnar
        def setSuccessfulPrint(tf):
            # set whether the print was successful or not. Regardless, the print
            # is done and a finalizer should be sent
            self.successful_print = tf
            self.sendCommand(Fisnar.finalizer())

        # beginning progress tracking
        self.setPrintProgress(0)

        # ensuring serial port is/can be opened
        if not FisnarController.DEBUG_MODE and self.serial_port is None:
            self.serial_port = self.initializeSerialPort()
            if self.serial_port is None:  # still couldn't open
                self.setInformation(FisnarController.SERIAL_ERR_MSG)
                setSuccessfulPrint(False)
                return

        # making sure fisnar commands exist
        if self.fisnar_commands is None:
            self.setInformation("slicer output must be saved as CSV before uploading to fisnar")
            setSuccessfulPrint(False)
            return

        # initializing
        confirmation = self.sendCommand(Fisnar.initializer())
        if not confirmation:
            setSuccessfulPrint(False)
            return

        # homing, to start
        confirmation = self.sendCommand(Fisnar.HM())
        if not confirmation:
            setSuccessfulPrint(False)
            return

        Logger.log("d", "before running commands, terminate running: " + str(self.getTerminateRunning()))  # test

        i = 0  # index
        segmented_commands = Converter.segmentFisnarCommands(self.fisnar_commands)
        output_states = [0, 0, 0, 0]
        # iterating over commands, uploading bytes without sendCommand function
        while (i < len(segmented_commands)) and (not self.getTerminateRunning()):
            Logger.log("d", "command " + str(i) + ", terminate running: " + str(self.getTerminateRunning()))  # test
            self.setPrintProgress(i / len(segmented_commands))  # updating progress

            if isinstance(segmented_commands[i][0], str):  # not chunk of dummy points
                command = segmented_commands[i]
                if command[0] == "Line Speed":
                    confirmation = self.sendCommand(Fisnar.SP(command[1]))
                    if not confirmation:
                        setSuccessfulPrint(False)
                        return
                else:
                    Logger.log("d", "forgotten about command: '" + str(command[0]) + "'")
            else:  # chunk of dummy points
                expected_bytes = bytes()

                for j in range(len(segmented_commands[i]) - 1):  # sending VA commands
                    command = segmented_commands[i][j]
                    command_bytes = Fisnar.VA(command[1], command[2], command[3])
                    self.writeBytes(command_bytes)
                    expected_bytes += Fisnar.expectedReturn(command_bytes)

                if segmented_commands[i][-1] != output_states:  # change in output state(s)
                    for k in range(4):
                        if segmented_commands[i][-1][k] != output_states[k]:
                            output_command = Fisnar.OU(k + 1, segmented_commands[i][-1][k])
                            self.writeBytes(output_command)
                            expected_bytes += Fisnar.expectedReturn(output_command)
                    output_states = copy.deepcopy(segmented_commands[i][-1])
                    Logger.log("d", str(output_states))

                self.writeBytes(Fisnar.ID())  # ID and confirmation bytes
                expected_bytes += Fisnar.expectedReturn(Fisnar.ID())

                received_bytes = bytes()  # reading as many lines as necessary
                for j in range(expected_bytes.count(bytes("\n", "ascii"))):
                    received_bytes += self.readLine()

                if expected_bytes != received_bytes:  # improper confirmation bytes recieved
                    Logger.log("e", "byte mismatch:\n-- expected --\n" + str(expected_bytes) + "\n-- received --\n" + str(received_bytes))
                    self.setInformation("failed to send commands over RS232 port - incorrect confirmation bytes recieved")
                    setSuccessfulPrint(False)
                    return
            i += 1

        if self.getTerminateRunning():  # loop was terminated
            self.sendCommand(Fisnar.finalizer())
            return  # will return anyway, so doesn't really matter

        else:  # loop wasn't terminated
            # homing, to end
            self.turnOffOutputs()
            confirmation = self.sendCommand(Fisnar.HM())
            if not confirmation:
                setSuccessfulPrint(False)
                return

            # if no errors have triggered so far, all good
            setSuccessfulPrint(True)
            return  # will return anyway, so this isn't really necessary

    def sendCommand(self, command_bytes):
        # write a given command to the fisnar. return false if confirmation
        # received, false otherwise

        if command_bytes == Fisnar.initializer():  # initialization command
            self.writeBytes(command_bytes)
            confirmation = self.readLine()
            if (bytes.fromhex("f0") + bytes("<< BASIC BIOS 2.2 >>\r\n", "ascii")) in confirmation:
                return True
            else:
                self.setInformation("initializer confirmation failed. Bytes received: " + str(confirmation))
                return False

        elif command_bytes == Fisnar.finalizer():  # finalization command
            self.writeBytes(command_bytes)
            return True  # nothing is being received from the fisnar, so can't go wrong here

        else:  # any other command
            self.writeBytes(command_bytes)  # write bytes
            confirmation = self.readLine()  # read same bytes back, plus "\n" character

            if command_bytes in (Fisnar.PX(), Fisnar.PY(), Fisnar.PZ()):
                new_coord = float(self.readLine()[:-1])

                # updating coordinate
                pos_ind = None
                if command_bytes == Fisnar.PX():
                    pos_ind = 0
                elif command_bytes == Fisnar.PY():
                    pos_ind = 1
                else:
                    pos_ind = 2
                self.current_position[pos_ind] = new_coord

            confirmation += self.readLine()  # reading 'ok!' response
            if confirmation == Fisnar.expectedReturn(command_bytes):
                return True
            else:
                self.setInformation("command failed to send. Bytes sent: " + str(command_bytes) + "Bytes received: " + str(confirmation))
                return False

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
            elif commands[i][0] == "End Program":
                pass
            elif commands[i][0] in ("Line Start", "Line End", "Line Passing"):
                for j in range(1, 4):
                    commands[i][j] = float(commands[i][j])
            else:
                print("Unexpected command: '" + str(commands[i][0]) + "'")  # for debugging
                commands.pop(i)
                i -= 1
            i += 1

        return copy.deepcopy(commands)


if __name__ == "__main__":
    # filepath = "C:\\Users\\Lab\Desktop\\G-code Project\\single_extruder_testing\\CFFFP_5x5x5_cube.csv"
    # filepath = "C:\\gcode2fisnar_tests\\cura_plugin_tests\\CFFFP_3_18_2022_three_line_test_file.csv"
    # fisnar_commands = FisnarController.readFisnarCommandsFromFile(filepath)
    #
    # for c in Converter.segmentFisnarCommands(fisnar_commands):
    #     print(c)

    fc = FisnarController()
    fc.sendCommand(Fisnar.finalizer())


if not FisnarController.DEBUG_MODE:  # importing UM if not in debug mode
    from UM.Logger import Logger
