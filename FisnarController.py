import copy
import serial
import time
import threading

from .Fisnar import Fisnar
from .Converter import Converter

from UM.Logger import Logger


class FisnarController:
    # class to handle controlling the fisnar via the RS-232 port. Once an
    # instance is given commands, it can upload them to the Fisnar

    # to turn on or off debugging mode
    DEBUG_MODE = False

    # for error reporting
    SERIAL_ERR_MSG = "Failed to connect to Fisnar serial port. Reconnection will be attempted when commands are next uploaded. Ensure the Fisnar is on and connected to the proper COM port, and ensure no other apps are using the COM port."

    def __init__(self):
        # error message
        self.information = None

        # fisnar machine initialization
        self.fisnar_machine = None
        self.com_port = None

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

    def setInformation(self, info):
        # set the error information
        self.information = str(info)

    def getInformation(self):
        # get error information
        if self.information is None:
            return "<no err msg set>"
        else:
            return str(self.information)

    def setComPort(self, com_port):
        # update the com port and create fisnar machine if the port
        # isn't None
        if com_port is None or com_port == "None":
            self.com_port = None
            if self.fisnar_machine is not None:  # None signals to get rid of port
                self.fisnar_machine.close()
                del self.fisnar_machine
                self.fisnar_machine = None
        else:
            self.com_port = str(com_port)
            if self.fisnar_machine is not None:  # delete com port object to free port
                self.fisnar_machine.close()
                del self.fisnar_machine
            self.fisnar_machine = Fisnar(self.com_port, 115200)

    def getComPort(self):
        return str(self.com_port)

    def setTerminateRunning(self, val):
        # set the terminate running status
        self.lock.acquire()
        self.terminate_running = val
        # Logger.log("d", "***** terminate running set to: " + str(val))
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
            confirmation = self.fisnar_machine.sendCommand(Fisnar.OU(i, 0))
            if not confirmation:
                return False
        return True

    def setCommands(self, command_list):
        # set the fisnar commands to be uploaded
        self.fisnar_commands = command_list

    def runCommands(self):
        # run the previously uploaded fisnar commands to the fisnar
        def setSuccessfulPrint(tf):
            # set whether the print was successful or not. Regardless, the print
            # is done and a finalizer should be sent
            self.successful_print = tf

            if self.fisnar_machine is not None:
                self.turnOffOutputs()
                self.fisnar_machine.sendCommand(Fisnar.finalizer())

        # beginning progress tracking
        self.setPrintProgress(0)

        # for testing
        if self.fisnar_machine is None:
            setSuccessfulPrint(False)
            self.setInformation("invalid Fisnar COM port selection.")
            return

        # ensuring serial port is/can be opened
        if not FisnarController.DEBUG_MODE and not self.fisnar_machine.isInitialized():
            self.fisnar_machine.initializeSerialPort()
            if not self.fisnar_machine.isInitialized():  # still couldn't open
                self.setInformation(self.fisnar_machine.getInformation())
                setSuccessfulPrint(False)
                return

        # making sure fisnar commands exist
        if self.fisnar_commands is None:
            self.setInformation("slicer output must be saved as CSV before uploading to fisnar")
            setSuccessfulPrint(False)
            return

        # initializing
        confirmation = self.fisnar_machine.sendCommand(Fisnar.initializer())
        if not confirmation:
            setSuccessfulPrint(False)
            return

        # homing, to start
        confirmation = self.fisnar_machine.sendCommand(Fisnar.HM())
        if not confirmation:
            setSuccessfulPrint(False)
            return

        # # test
        # Logger.log("d", "before running commands, terminate running: " + str(self.getTerminateRunning()))
        # test = [[], [], []]

        # segmenting commands, turning into new command segment list where the max dummy point length is set
        initial_segmented_commands = Converter.segmentFisnarCommands(self.fisnar_commands)
        segmented_commands = []
        max_dummy_seg_length = 50
        for i in range(len(initial_segmented_commands)):  # iterating over segmented commands from Converter
            if isinstance(initial_segmented_commands[i][0], list):  # is list of dummy command
                dummy_list = initial_segmented_commands[i][:-1]  # current dummy command list
                output_list = initial_segmented_commands[i][-1]

                new_dummy_segs = []  # list of lists of dummy commands (with output ending)
                for j in range(len(dummy_list)):
                    if j % max_dummy_seg_length == 0:
                        new_dummy_segs.append([])
                    new_dummy_segs[-1].append(dummy_list[j])

                for j in range(len(new_dummy_segs)):
                    new_dummy_segs[j].append(output_list)
                    segmented_commands.append(new_dummy_segs[j])
            else:  # Line speed, etc. - just not dummy point list
                segmented_commands.append(initial_segmented_commands[i])

        # # test
        # for element in segmented_commands:
        #     Logger.log("d", str(element))

        i = 0  # index
        output_states = [0, 0, 0, 0]
        # iterating over commands, uploading bytes without sendCommand function
        while (i < len(segmented_commands)) and (not self.getTerminateRunning()):
            # Logger.log("d", "command " + str(i) + ", terminate running: " + str(self.getTerminateRunning()))  # test
            self.setPrintProgress(i / len(segmented_commands))  # updating progress

            if isinstance(segmented_commands[i][0], str):  # not chunk of dummy points
                command = segmented_commands[i]
                if command[0] == "Line Speed":
                    confirmation = self.fisnar_machine.sendCommand(Fisnar.SP(command[1]))
                    if not confirmation:
                        setSuccessfulPrint(False)
                        return
                else:
                    Logger.log("i", "forgotten about command: '" + str(command[0]) + "'")
            else:  # chunk of dummy points
                expected_bytes = bytes()

                for j in range(len(segmented_commands[i]) - 1):  # sending VA commands
                    command = segmented_commands[i][j]
                    command_bytes = Fisnar.VA(command[1], command[2], command[3])
                    self.fisnar_machine.writeBytes(command_bytes)
                    expected_bytes += Fisnar.expectedReturn(command_bytes)

                    # test[0].append(str(command_bytes))  # test
                    # test[1].append(str(Fisnar.expectedReturn(command_bytes)))

                if segmented_commands[i][-1] != output_states:  # change in output state(s)
                    for k in range(4):
                        if segmented_commands[i][-1][k] != output_states[k]:
                            output_command = Fisnar.OU(k + 1, segmented_commands[i][-1][k])
                            self.fisnar_machine.writeBytes(output_command)
                            expected_bytes += Fisnar.expectedReturn(output_command)
                    output_states = copy.deepcopy(segmented_commands[i][-1])

                self.fisnar_machine.writeBytes(Fisnar.ID())  # ID and confirmation bytes
                expected_bytes += Fisnar.expectedReturn(Fisnar.ID())

                received_bytes = bytes()
                for j in range(expected_bytes.count(bytes("\n", "ascii"))):
                    temp = self.fisnar_machine.readLine()
                    received_bytes += temp
                    # # test
                    # if j % 2 == 0:
                    #     test[2].append(str(temp))
                    # else:
                    #     test[2][-1] += str(temp)

                # for j in range(len(test[0])):  # test
                #     Logger.log("d", "sent: " + str(test[0][j]) + "  |  expected: " + str(test[1][j]) + "  |  received: " + str(test[2][j]))

                if expected_bytes != received_bytes:  # improper confirmation bytes recieved
                    Logger.log("e", "byte mismatch:\n-- expected --\n" + str(expected_bytes) + "\n-- received --\n" + str(received_bytes))
                    Logger.log("e", "newline count: " + str(expected_bytes.count(bytes("\n", "ascii"))))
                    self.setInformation("failed to send commands over RS232 port - incorrect confirmation bytes recieved")
                    setSuccessfulPrint(False)
                    return
            i += 1

        self.turnOffOutputs()  # turning off output no matter what
        if self.getTerminateRunning():  # loop was terminated
            self.fisnar_machine.sendCommand(Fisnar.finalizer())
            return  # will return anyway, so doesn't really matter

        else:  # loop wasn't terminated
            # homing, to end
            confirmation = self.fisnar_machine.sendCommand(Fisnar.HM())
            if not confirmation:
                setSuccessfulPrint(False)
                return

            # if no errors have triggered so far, all good
            setSuccessfulPrint(True)
            return  # will return anyway, so this isn't really necessary

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
