import os
import os.path
import time

from cura.CuraApplication import CuraApplication
from cura.PrinterOutput.PrinterOutputDevice import PrinterOutputDevice, ConnectionType, ConnectionState
from io import StringIO
from PyQt6.QtCore import pyqtProperty, pyqtSignal, pyqtSlot, QTimer
from queue import Queue
from serial import Serial, SerialException, SerialTimeoutException
from threading import Event, Thread
from UM.Resources import Resources
from UM.Logger import Logger
from UM.Message import Message
from .Converter import Converter
from .FisnarCommands import FisnarCommands
from .FisnarCSVWriter import FisnarCSVWriter
from .FisnarRobotExtension import FisnarRobotExtension
from .PickAndPlaceGenerator import PickAndPlaceGenerator
from .UltimusV import PressureUnits, UltimusV

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

class FisnarOutputDevice(PrinterOutputDevice):
    # class for printing with the Fisnar over RS232 port

    def __init__(self):
        super().__init__("fisnar_f5200n", ConnectionType.UsbConnection)

        # OutputDevice plugin UI stuff
        self.setName("Fisnar F5200N")
        self.setShortDescription("Print Over RS232")
        self.setDescription("Print Over RS232")
        self.setIconName("print")

        # Fisnar command storage/tracking during printing
        self._fisnar_commands = []  # type: list[bytes]
        self._current_index = 0

        # Fisnar/dispenser command storage tracking for pick and place
        self._pick_place_commands = []  # type: list[tuple(str, bytes)]
        self._pick_place_index = 0

        # for tracking printing state
        self._is_printing = False
        self._is_paused = False
        self._pick_place_in_progress = False

        # for segmenting
        self._va_register_count = 0
        self._output_1_on = False
        self._output_2_on = False
        self._output_3_on = False
        self._output_4_on = False

        self._command_queue = Queue()  # queue to hold commands to be sent
        self._command_received = Event()  # event that is set when the Fisnar sends 'ok!' and cleared when waiting for an 'ok!' confirm from the Fisnar

        self._init_connect_send_time = None  # type: float

        # for connecting to serial port
        self._serial = None  # type: serial.Serial
        self._serial_port_name = None  # type: str or None
        self._timeout = 3
        self._baud_rate = 115200

        # for updating position when not printing
        self._most_recent_position = [0.0, 0.0, 0.0]
        self._button_move_confirm_received = Event()
        self._button_move_confirms_received = 0
        self._x_feedback_received = Event()
        self._y_feedback_received = Event()
        self._z_feedback_received = Event()

        # for connecting to dispenser
        self.dispenser = UltimusV()

        # for showing monitor while printing
        self._plugin_path = os.path.join(Resources.getStoragePath(Resources.Resources, "plugins", "FisnarRobotPlugin", "FisnarRobotPlugin"))
        self._monitor_view_qml_path = os.path.join(self._plugin_path, "resources", "qml", "MonitorItem.qml")

        # update thread for printing
        self._update_thread = Thread(target=self._update, daemon=True, name="FisnarRobotPlugin RS232 Control")

        self._fre_instance = FisnarRobotExtension.getInstance()

        # for checking if Fisnar is printing while trying to exit app
        CuraApplication.getInstance().getOnExitCallbackManager().addCallback(self._checkActivePritingOnAppExit)

    def _checkActivePritingOnAppExit(self):
        # called when user tries to exit app - checks if Fisnar is trying to print
        application = CuraApplication.getInstance()
        if not self._is_printing:  # not printing, so lose serial port and continue with exit checks
            if self._connection_state == ConnectionState.Connected:
                self.stopPrintingAndFinalize()  # print is already stopped but doesn't matter
            self.close()
            self.dispenser.close()
            application.triggerNextExitCheck()
            return

        application.setConfirmExitDialogCallback(self._onConfirmExitDialogResult)
        application.showConfirmExitDialog.emit(catalog.i18nc("@label", "Fisnar print is in progress - closing Cura will stop this print. Are you sure?"))

    def _onConfirmExitDialogResult(self, result):
        # triggers when user clicks cancel or confirm on the confirm exit dialog
        if result:
            self.stopPrintingAndFinalize()
            self.close()  # ensuring fisnar is finalized and port is closed when exiting app
            self.dispenser.close()
            CuraApplication.getInstance().triggerNextExitCheck()

    def requestWrite(self, nodes, file_name=None, limit_mimetypes=False, file_handler=None, filter_by_machine=False, **kwargs):
        # called when 'Print Over RS232' button is pressed - all parameters are ignored.
        # generates fisnar commands and gives csv string to _printFisnarCommands()

        if self._is_printing:  # show message if the fisnar is already printing
            printing_msg = Message(text = catalog.i18nc("@message", "The Fisnar is currently printing. Another print cannot begin until the current one completes."),
                                   title = catalog.i18nc("@message", "Print in Progress"))
            printing_msg.show()
            return

        self.writeStarted.emit(self)  # not sure about this - taken from USBPrinterOutputDevice
        CuraApplication.getInstance().getController().setActiveStage("MonitorStage")  # show 'monitor' screen

        fisnar_csv_writer = FisnarCSVWriter.getInstance()
        fisnar_command_csv_io = StringIO()
        success = fisnar_csv_writer.write(fisnar_command_csv_io, None)  # writing scene to fisnar_command_csv_io
        if not success:  # conversion failed - log error and show user error message
            Logger.log("e", f"FisnarCSVWriter failed in requestWrite(): {str(fisnar_csv_writer.getInformation())}")
            err_msg = Message(text = catalog.i18nc("@message", f"An error occured while preparing print: {str(fisnar_csv_writer.getInformation())}"),
                              title = catalog.i18nc("@message", "Error Preparing Print"))
            err_msg.show()
            return

        if self._connection_state == ConnectionState.Connected:  # if successfully connected
            # Logger.log("d", "Serial port created, _printFisnarCommands() called")
            self._printFisnarCommands(fisnar_command_csv_io.getvalue())  # starting print
        else:  # not connected
            printing_msg = Message(text = catalog.i18nc("@message", "The Fisnar is not yet connected. Ensure the proper serial port name has been entered under Fisnar Actions -> Define Setup"),
                                   title = catalog.i18nc("@message", "Fisnar Not Connected"))
            printing_msg.show()
            return

    def _printFisnarCommands(self, fisnar_command_csv):
        # start a print based on a fisnar command csv

        # updating fisnar command bytes from fisnar_command_csv
        commands = Converter.readFisnarCommandsFromCSV(fisnar_command_csv)
        self._fisnar_commands.clear()

        for command in commands:
            if command[0] == "Dummy Point":
                self._fisnar_commands.append(FisnarCommands.VA(command[1], command[2], command[3]))
                self._fisnar_commands.append(FisnarCommands.ID())
            elif command[0] == "Output":
                self._fisnar_commands.append(FisnarCommands.OU(command[1], command[2]))
            elif command[0] == "Line Speed":
                self._fisnar_commands.append(FisnarCommands.SP(command[1]))
            elif command[0] == "End Program":
                pass
            else:
                Logger.log("w", "Unrecognized command found when uploading over Serial port: " + str(command[0]))

        self._current_index = 0  # resetting command index

        # print status stuff
        self.setPrintingState(True)
        self._is_paused = False

        for i in range(2):
            self._sendNextFisnarLine()  # push the first command to start the ok loop

        # Logger.log("d", "end of _printFisnarCommands")  # test

    def stopPrintingAndFinalize(self):
        # stop printing and finalize the Fisnar
        self.setPrintingState(False)  # ensure not printing

        self._sendCommand(FisnarCommands.HM())
        self.sendCommand(FisnarCommands.finalizer())

        while not self._command_queue.empty():
            time.sleep(1)

    def connect(self, serial_name):
        # try to establish serial connection and store Serial object. called whenever a print is started
        Logger.log("i", "Attempting to connect to Fisnar...")
        self._serial_port_name = serial_name

        if self._serial is None:
            try:
                self._serial = Serial(self._serial_port_name, self._baud_rate, timeout=self._timeout, writeTimeout=self._timeout)
                Logger.log("i", f"Serial port {self._serial_port_name} is open. Testing if fisnar is on...")
            except SerialException:  # exception thrown - probably not plugged in
                Logger.log("w", "Exception occured when trying to create serial connection")
                printing_msg = Message(text = catalog.i18nc("@message", "Unable to connect to Fisnar serial port. Ensure proper port is selected."),
                                       title = catalog.i18nc("@message", "Serial Port Error"))
                printing_msg.show()
                return
            except OSError as e:  # idk when this happens
                Logger.log("w", f"The serial device is suddenly unavailable while trying to connect: {str(e)}")
                printing_msg = Message(text = catalog.i18nc("@message", "Unable to connect to Fisnar serial port. Ensure proper port is selected."),
                                       title = catalog.i18nc("@message", "Serial Port Error"))
                printing_msg.show()
                return

        # if not returned, the serial port is connected to the fisnar, but it may not be on yet.
        self.setConnectionState(ConnectionState.Connecting)
        self._sendCommand(FisnarCommands.initializer())
        self._init_connect_send_time = time.time()
        while time.time() - self._init_connect_send_time < 5.0:  # 5 sec timeout to get initialization response
            try:
                curr_line = self._serial.readline()
            except:
                continue

            if curr_line == FisnarCommands.expectedReturn(FisnarCommands.initializer()):  # succesfully connected
                self._command_received.set()  # not expecting a command anymore
                Logger.log("i", "Fisnar connection successful.")
                self.setConnectionState(ConnectionState.Connected)
                self._update_thread.start()
                return

        self.close()  # escaped the while loop, so failed to initialize
        Logger.log("w", "Fisnar failed to initialize...")

    def close(self):
        # closes the serial port and resets _serial member variable to None
        # MAKE SURE FISNAR IS FINALIZED BEFORE CLOSING
        # Logger.log("d", f"serial port was {str(self._serial)}, now closing")

        super().close()  # sets _connection_state to ConnectionState.Closed
        if self._serial is not None:
            self._serial.close()
        self._serial = None

        self._update_thread = Thread(target=self._update, daemon=True, name="FisnarRobotPlugin RS232 Control")

    def _update(self):
        # this continually runs while connected to device, reading lines and
        # sending fisnar commands if necessary
        while self._connection_state == ConnectionState.Connected and self._serial is not None:
            try:
                curr_line = self._serial.readline()
            except:
                continue  # nothing to read

            Logger.log("d", "command received: " + str(curr_line))

            if curr_line.startswith(b"ok!"):  # confirmation received
                self._command_received.set()
            elif FisnarCommands.isFeedback(curr_line):  # check if value was received
                # Logger.log("d", str(curr_line))
                if not self._x_feedback_received.is_set():  # value is x position
                    self._most_recent_position[0] = float(curr_line[:-2]) if float(curr_line[:-2]) > 0.0 else 0.0  # this is to fix slightly negative reporting bug
                    # Logger.log("d", "fisnar x updated: " + str(self._most_recent_position[0]))
                    self._x_feedback_received.set()
                    self.xPosUpdated.emit()
                    self._y_feedback_received.clear()
                    self.sendCommand(FisnarCommands.PY())
                elif not self._y_feedback_received.is_set():  # value is y position
                    self._most_recent_position[1] = float(curr_line[:-2]) if float(curr_line[:-2]) > 0.0 else 0.0
                    # Logger.log("d", "fisnar y updated: " + str(self._most_recent_position[1]))
                    self._y_feedback_received.set()
                    self.yPosUpdated.emit()
                    self._z_feedback_received.clear()
                    self.sendCommand(FisnarCommands.PZ())
                elif not self._z_feedback_received.is_set():  # value is z position
                    self._most_recent_position[2] = float(curr_line[:-2]) if float(curr_line[:-2]) > 0.0 else 0.0
                    # Logger.log("d", "fisnar z updated: " + str(self._most_recent_position[2]))
                    self._z_feedback_received.set()
                    self.zPosUpdated.emit()

            # can send next command
            if curr_line.startswith(b"ok!"):
                if not self._button_move_confirm_received.is_set():  # need to update position
                    self._button_move_confirms_received += 1
                    if self._button_move_confirms_received == 2:
                        self._button_move_confirms_received = 0
                        self._button_move_confirm_received.set()
                        self._x_feedback_received.clear()  # this will trigger the PX->PY->PZ 'cascade'
                        self.sendCommand(FisnarCommands.PX())
                if not self._command_queue.empty():
                    self._sendCommand(self._command_queue.get())
                elif self._is_printing:  # still printing but queue is empty
                    if not self._is_paused:
                        self._sendNextFisnarLine()
                elif self._pick_place_in_progress:
                    self._sendNextPickPlaceCommand()

        if self._is_printing:  # connection broken
            self.terminatePrint()

    def sendCommand(self, command):
        # command: fisnar command as bytes
        # send a fisar command (or put into command queue if waiting for Fisnar command confirmation)
        if not self._command_received.is_set():  # if waiting for confirmation (ok! hasn't been received yet)
            self._command_queue.put(command)
        else:
            self._sendCommand(command)

    def _sendCommand(self, command):
        # given a fisnar command as a byte array, send it to the fisnar.
        # this function doesn't check for anything besides Serial Exceptions.
        # this functio also clears the command recieved event, so this should
        # only be called if there are no expected confirmation responses

        if self._serial is None or self._connection_state not in (ConnectionState.Connected, ConnectionState.Connecting):  # both connecting and connected mean the port is open
            return

        Logger.log("d", "command sent: " + str(command))

        # actually sending bytes
        try:
            if command != FisnarCommands.finalizer():  # finalizer has no response, so don't set flag to wait for one
                self._command_received.clear()
            self._serial.write(command)
            # Logger.log("d", f"bytes written: {command}")
        except SerialTimeoutException:
            self._command_received.set()
            Logger.log("w", "Fisnar serial connection timed out when sending bytes: " + str(command))
        except SerialException:
            self.setConnectionState(ConnectionState.Error)
            Logger.log("w", "Unexpected serial error occured when trying to send bytes: " + str(command))

    def _sendNextFisnarLine(self):
        try:
            command_bytes = self._fisnar_commands[self._current_index]
        except IndexError:  # done printing!
            Logger.log("i", "Fisnar done with print.")

            # stop printing
            self.setPrintingState(False)
            self._is_paused = False

            # clean things up
            for i in range(1, 5):
                self.sendCommand(FisnarCommands.OU(i, 0))
            self.sendCommand(FisnarCommands.HM())

            # reset to prep for another print
            self._resetPrintingInternalState()
            return

        # the below 'if' block is a fix for the delay that occurs when many VA commands are sent sequentially. this effectively registers all consecutive
        # extruding movement commands at once, and then sends an execute command afterwards so they all execute immediately, instead of registering and
        # executing each movement individually, which causes significant delays and a lot of overextrusion
        if command_bytes.startswith(bytes("OU", "ascii")) and command_bytes[-2] == ord("1"):  # if command is output on
            current_output = int(chr(command_bytes[3]))
            if not (self._output_1_on or self._output_2_on or self._output_3_on or self._output_4_on):  # all outputs currently off
                self._current_index += 1

                while not (self._fisnar_commands[self._current_index].startswith(bytes("OU", "ascii")) and self._fisnar_commands[self._current_index][-2] == ord("0")):  # while not an output off command
                    Logger.log("d", str(self._current_index) + ", " + str(self._fisnar_commands[self._current_index]))
                    if self._va_register_count >= 100:  # if fully registered, purge
                        self.sendCommand(FisnarCommands.OU(current_output, 1))
                        self.sendCommand(FisnarCommands.ID())
                        self._va_register_count = 0
                        self.sendCommand(FisnarCommands.OU(current_output, 0))
                        self.printProgressUpdated.emit()  # after every visual 'chunk', update progress

                    if self._fisnar_commands[self._current_index].startswith(bytes("VA", "ascii")):
                        self.sendCommand(self._fisnar_commands[self._current_index])
                        self._va_register_count += 1
                        self._current_index += 1
                    elif self._fisnar_commands[self._current_index].startswith(bytes("OU", "ascii")):  # this would be an output on command - should never happen, but check just in case
                        Logger.log("w", "multiple output on's received with no output off's")
                    elif self._fisnar_commands[self._current_index].startswith(bytes("ID", "ascii")):
                        self._current_index += 1  # just ignore ID() commands for now
                    elif self._fisnar_commands[self._current_index].startswith(bytes("SP", "ascii")):  # also purge if speed changes.
                        self.sendCommand(FisnarCommands.OU(current_output, 1))
                        self.sendCommand(FisnarCommands.ID())  # execute movements with old speed
                        self._va_register_count = 0
                        self.sendCommand(FisnarCommands.OU(current_output, 0))
                        self.sendCommand(self._fisnar_commands[self._current_index])  # update speed afterwards
                        self._current_index += 1
                        self.printProgressUpdated.emit()
                    else:  # nothing should make it here
                        Logger.log("w", "unexpected command: " + str(self._fisnar_commands[self._current_index]))
                        self.sendCommand(self._fisnar_commands[self._current_index])
                        self._current_index += 1
                        self.printProgressUpdated.emit()

                # send output off and ID, and reset register count
                self.sendCommand(FisnarCommands.OU(current_output, 1))
                self.sendCommand(FisnarCommands.ID())
                self._va_register_count = 0
                self.sendCommand(FisnarCommands.OU(current_output, 0))
                self.printProgressUpdated.emit()
        else:  # just send command like normal
            self._sendCommand(command_bytes)  # send bytes

            self._current_index += 1  # update current index
            self.printProgressUpdated.emit()  # recalculate progress and update QML

    def _sendNextPickPlaceCommand(self):
        # similar to _sendNextFisnarLine, but is only used for pick and place
        # procedures. note that most of the status setting is done
        # manually here. eventually, these might want to be moved to a function
        try:
            next_command = self._pick_place_commands[self._pick_place_index]
        except IndexError:
            Logger.log("i", "done with pick and place")
            self.setPickPlaceStatus(False)
            self._resetPickAndPlaceInternalState()
            return

        while next_command[0] in ("d", "sleep"):  # synchronously send dispenser commands / time delays
            if next_command[0] == "d":
                success = self.dispenser.sendCommand(next_command[1])
                if not success:
                    self.setPickPlaceStatus(False)
                    self._resetPickAndPlaceInternalState()
                    return
            else:
                time.sleep(float(next_command[1]))

            self._pick_place_index += 1  # ensure there is a next command to send
            try:
                next_command = self._pick_place_commands[self._pick_place_index]
            except IndexError:
                Logger.log("i", "done with pick and place")
                self.setPickPlaceStatus(False)
                self._resetPickAndPlaceInternalState()
                return

        self._sendCommand(next_command[1])  # is necessarily a fisnar command at this point
        self._pick_place_index += 1

    def setPrintingState(self, printing_state):
        if printing_state != self._is_printing:
            self._is_printing = not self._is_printing
            self.printingStatusUpdated.emit()

    def setPickPlaceStatus(self, pick_place_status):
        if self._pick_place_in_progress != pick_place_status:
            self._pick_place_in_progress = pick_place_status
            self.pickPlaceStatusUpdated.emit()

    def _resetPrintingInternalState(self):
        # resets internal printing state - called after user terminates print
        # or after print is finished. Assumes self._is_printing has already
        # been set to false
        self._fisnar_commands.clear()
        self._current_index = 0
        self.printProgressUpdated.emit()  # reset UI

    def _resetPickAndPlaceInternalState(self):
        # reset the internal pick and place parameters - assumes pick and place
        # status has already been updated
        self._pick_place_commands.clear()
        self._pick_place_index = 0

    def _getPrintingProgress(self):
        try:
            return self._current_index / len(self._fisnar_commands)
        except ZeroDivisionError:
            return None  # print hasn't started yet

    @pyqtSlot(str)
    def sendRawCommand(self, command_str):
        # TODO: this should validate the string before sending
        command_bytes = bytes(command_str + "\r", "ascii")
        self.sendCommand(command_bytes)

    @pyqtSlot()
    def executePickPlace(self):
        # start pick and place procedure

        # TODO: ensure parameters and connections are such that pick and place can be done
        if not self.dispenser.isConnected():  # if dispenser not connected
            Logger.log("w", "Pick and place dispenser is not open, pick and place execution terminated.")  # TODO: this should show error to user
            return

        if not self._connection_state == ConnectionState.Connected:
            Logger.log("w", "Fisnar is not connected, pick and place execution terminated")
            return

        pick_point = self._fre_instance.pick_location
        place_point = self._fre_instance.place_location
        xy_speed = self._fre_instance.xy_speed
        z_speed = self._fre_instance.z_speed
        pick_dwell = self._fre_instance.pick_dwell
        place_dwell = self._fre_instance.place_dwell
        vacuum_pressure = self._fre_instance.vacuum_pressure
        vacuum_units = self._fre_instance.vacuum_units
        reps = self._fre_instance.reps

        # TODO: call external function for generating pick and place commands from parameters
        self._pick_place_commands = PickAndPlaceGenerator.getCommands(
            pick_point,
            place_point,
            xy_speed,
            z_speed,
            pick_dwell,
            place_dwell,
            vacuum_pressure,
            vacuum_units,
            reps
        )

        # start process (push first command to start ok loop)
        self.setPickPlaceStatus(True)
        self._sendNextPickPlaceCommand()

    @pyqtSlot(float, float, float)
    def moveHead(self, dx, dy, dz):
        if not (0.0 <= self._most_recent_position[0] + dx <= 200.0):  # checking if move is valid
            return
        if not (0.0 <= self._most_recent_position[1] + dy <= 200.0):
            return
        if not (0.0 <= self._most_recent_position[2] + dz <= 150.0):
            return

        self._button_move_confirm_received.clear()
        self._button_move_confirms_received = 0
        # Logger.log("d", f"dx: {dx}, {type(dx)}; dy: {dy}, {type(dy)}, dz: {dz}, {type(dz)}")
        valid_movement_distances = (-10.0, -1.0, -0.1, -0.01, -0.001, 0.001, 0.01, 0.1, 1.0, 10.0)

        if dx in valid_movement_distances:
            self._sendCommand(FisnarCommands.MXR(dx))
            self._sendCommand(FisnarCommands.ID())
        if dy in valid_movement_distances:
            self._sendCommand(FisnarCommands.MYR(dy))
            self._sendCommand(FisnarCommands.ID())
        if dz in valid_movement_distances:
            self._sendCommand(FisnarCommands.MZR(dz))
            self._sendCommand(FisnarCommands.ID())

    @pyqtSlot()
    def home(self):
        self._button_move_confirm_received.clear()
        self._button_move_confirms_received = 1  # kind of hacky but it works - this makes the _update loop only need to look for one more ok! confirm before sending coord feedback commands
        self._sendCommand(FisnarCommands.HM())

    ################################
    # QML Stuff
    ################################

    @pyqtSlot()
    def pauseOrResumePrint(self):
        Logger.log("i", "Fisnar serial print has been " + ("resumed" if self._is_paused else "paused"))
        self._is_paused = not self._is_paused  # flips whether print is paused or not
        if not self._is_paused:  # if being resumed, send the next command to restart the ok! loop
            self._sendNextFisnarLine()

    @pyqtSlot()
    def terminatePrint(self):
        # called when the user presses the 'Terminate' button. this stops
        # sending commands and homes the Fisnar
        Logger.log("i", "Fisnar serial print has been terminated.")

        # this combination of states signals that no print has started or a print has been terminated
        self.setPrintingState(False)
        self._is_paused = False

        # ensure all outputs are off, then home
        for i in range(1, 5):
            self.sendCommand(FisnarCommands.OU(i, 0))
        self.sendCommand(FisnarCommands.HM())

        self._resetPrintingInternalState()  # resets fisnar commands, current command index

    @pyqtSlot()
    def terminatePickPlace(self):
        # terminate the pick and place procedure
        Logger.log("i", "Fisnar pick and place terminated")

        self.setPickPlaceStatus(False)
        self._resetPickAndPlaceInternalState()

        self.sendCommand(FisnarCommands.HM())
        self.dispenser.sendCommand(UltimusV.setVacuum(0, PressureUnits.V_KPA))

# ----------------- pick location property setup -----------------------------
    pickXUpdated = pyqtSignal()
    @pyqtProperty(str, notify=pickXUpdated)
    def pick_x(self):
        return str(self._fre_instance.pick_location[0])

    pickYUpdated = pyqtSignal()
    @pyqtProperty(str, notify=pickYUpdated)
    def pick_y(self):
        return str(self._fre_instance.pick_location[1])

    pickZUpdated = pyqtSignal()
    @pyqtProperty(str, notify=pickZUpdated)
    def pick_z(self):
        return str(self._fre_instance.pick_location[2])

    @pyqtSlot(str, str, str)
    def setPickLocation(self, x, y, z):
        new_val = (float(x), float(y), float(z))
        self._fre_instance.pick_location = new_val
        self._fre_instance.updatePreferencedValues()

# -------------------- place location property setup ------------------------
    placeXUpdated = pyqtSignal()
    @pyqtProperty(str, notify=placeXUpdated)
    def place_x(self):
        return str(self._fre_instance.place_location[0])

    placeYUpdated = pyqtSignal()
    @pyqtProperty(str, notify=placeYUpdated)
    def place_y(self):
        return str(self._fre_instance.place_location[1])

    placeZUpdated = pyqtSignal()
    @pyqtProperty(str, notify=placeZUpdated)
    def place_z(self):
        return str(self._fre_instance.place_location[2])

    @pyqtSlot(str, str, str)
    def setPlaceLocation(self, x, y, z):
        new_val = (float(x), float(y), float(z))
        self._fre_instance.place_location = new_val
        self._fre_instance.updatePreferencedValues()

# -------------------- vacuum pressure property setup -----------------------
    vacuumPressureUpdated = pyqtSignal()
    @pyqtProperty(str, notify=vacuumPressureUpdated)
    def vacuum_pressure(self):
        return str(self._fre_instance.vacuum_pressure)

    @pyqtSlot(str)
    def setVacuumPressure(self, pressure):
        self._fre_instance.vacuum_pressure = float(pressure)
        self._fre_instance.updatePreferencedValues()

# ------------------ vacuum units property setup ----------------------------
    # 'int' represents enumeration in UltimusV.PressureUnits (vacuum units section)
    vacuumUnitsUpdated = pyqtSignal()
    @pyqtProperty(int, notify=vacuumUnitsUpdated)
    def vacuum_units(self):
        return int(self._fre_instance.vacuum_units)

    @pyqtSlot(int)
    def setVacuumUnits(self, units):
        self._fre_instance.vacuum_units = int(units)
        self._fre_instance.updatePreferencedValues()

# --------------------- x/y speed property setup ----------------------------
    xySpeedUpdated = pyqtSignal()
    @pyqtProperty(str, notify=xySpeedUpdated)
    def xy_speed(self):
        return str(self._fre_instance.xy_speed)

    @pyqtSlot(str)
    def setXYSpeed(self, speed):
        self._fre_instance.xy_speed = float(speed)
        self._fre_instance.updatePreferencedValues()

# ---------------------- z speed property setup -----------------------------
    zSpeedUpdated = pyqtSignal()
    @pyqtProperty(str, notify=zSpeedUpdated)
    def z_speed(self):
        return str(self._fre_instance.z_speed)

    @pyqtSlot(str)
    def setZSpeed(self, speed):
        self._fre_instance.z_speed = float(speed)
        self._fre_instance.updatePreferencedValues()

# ------------------ pick dwell time -----------------------------------
    pickDwellUpdated = pyqtSignal()
    @pyqtProperty(str, notify=pickDwellUpdated)
    def pick_dwell(self):
        return str(self._fre_instance.pick_dwell)

    @pyqtSlot(str)
    def setPickDwell(self, dwell_time):
        self._fre_instance.pick_dwell = float(dwell_time)
        self._fre_instance.updatePreferencedValues()

# ----------------- place dwell time ----------------------------------
    placeDwellUpdated = pyqtSignal()
    @pyqtProperty(str, notify=placeDwellUpdated)
    def place_dwell(self):
        return str(self._fre_instance.place_dwell)

    @pyqtSlot(str)
    def setPlaceDwell(self, dwell_time):
        self._fre_instance.place_dwell = float(dwell_time)
        self._fre_instance.updatePreferencedValues()

# ---------------- repititions -------------------------------------
    repsUpdated = pyqtSignal()
    @pyqtProperty(str, notify=repsUpdated)
    def reps(self):
        return str(self._fre_instance.reps)

    @pyqtSlot(str)
    def setReps(self, reps):
        self._fre_instance.reps = int(reps)
        self._fre_instance.updatePreferencedValues()

# ----------------------------------------------------------------------

    xPosUpdated = pyqtSignal()
    @pyqtProperty(str, notify=xPosUpdated)
    def x_pos(self):
        return str(round(self._most_recent_position[0], 3))

    yPosUpdated = pyqtSignal()
    @pyqtProperty(str, notify=yPosUpdated)
    def y_pos(self):
        return str(round(self._most_recent_position[1], 3))

    zPosUpdated = pyqtSignal()
    @pyqtProperty(str, notify=zPosUpdated)
    def z_pos(self):
        return str(round(self._most_recent_position[2], 3))

    fisnarPortNameUpdated = pyqtSignal()
    @pyqtProperty(str, notify=fisnarPortNameUpdated)
    def fisnar_serial_port(self):
        if not self._connection_state == ConnectionState.Connected:
            return "Not connected..."
        else:
            return str(self._fre_instance.com_port)

    pickPlaceStatusUpdated = pyqtSignal()
    @pyqtProperty(bool, notify=pickPlaceStatusUpdated)
    def pick_place_status(self):
        return self._pick_place_in_progress

    dispenserStatusUpdated = pyqtSignal()
    @pyqtProperty(bool, notify=dispenserStatusUpdated)
    def dispenser_connected(self):
        return self.dispenser.isConnected()

    printingStatusUpdated = pyqtSignal()
    @pyqtProperty(bool, notify=printingStatusUpdated)
    def printing_status(self):
        return self._is_printing

    printProgressUpdated = pyqtSignal()  # signal to update printing progress
    @pyqtProperty(str, notify=printProgressUpdated)
    def print_progress(self):
        printing_prog = self._getPrintingProgress()
        if printing_prog is None:
            return "n/a"
        else:
            return str(round(printing_prog * 100, 2))
