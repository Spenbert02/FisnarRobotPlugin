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

    # # signals for sending commands to dispenser
    # sendDispenserCommand = pyqtSignal(bytes)

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

        self._command_queue = Queue()  # queue to hold commands to be sent
        self._command_received = Event()  # event that is set when the Fisnar sends 'ok!' and cleared when waiting for an 'ok!' confirm from the Fisnar

        self._fisnar_initialized = Event()  # event for tracking state of printer - set when initialized, and cleared when finalized

        # for connecting to serial port
        self._serial = None
        self._serial_port_name = None
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
        self._fre_instance.dispenserSerialPortUpdated.connect(self._onExternalDispenserSerialUpdated)

        # for checking if Fisnar is printing while trying to exit app
        CuraApplication.getInstance().getOnExitCallbackManager().addCallback(self._checkActivePritingOnAppExit)

    def _checkActivePritingOnAppExit(self):
        # called when user tries to exit app - checks if Fisnar is trying to print
        application = CuraApplication.getInstance()
        if not self._is_printing:  # not printing, so lose serial port and continue with exit checks
            if self._connection_state == ConnectionState.Connected:
                self.stopPrintingAndFinalize()  # print is already stopped but doesn't matter
            self.close()
            application.triggerNextExitCheck()
            return

        application.setConfirmExitDialogCallback(self._onConfirmExitDialogResult)
        application.showConfirmExitDialog.emit(catalog.i18nc("@label", "Fisnar print is in progress - closing Cura will stop this print. Are you sure?"))

    def _onConfirmExitDialogResult(self, result):
        # triggers when user clicks cancel or confirm on the confirm exit dialog
        if result:
            self.stopPrintingAndFinalize()
            self.close()  # ensuring fisnar is finalized and port is closed when exiting app
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

        if self._serial is not None:  # if successfully connected
            # Logger.log("d", "Serial port created, _printFisnarCommands() called")
            self._printFisnarCommands(fisnar_command_csv_io.getvalue())  # starting print

    # IN PROG
    def _printFisnarCommands(self, fisnar_command_csv):
        # start a print based on a fisnar command csv

        # updating fisnar command bytes from fisnar_command_csv
        commands = Converter.readFisnarCommandsFromCSV(fisnar_command_csv)
        self._fisnar_commands.clear()

        if not self._fisnar_initialized.is_set():  # will need to initialize if not already
            self._fisnar_commands.append(FisnarCommands.initializer())

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
        self.setPrintingState(False)  # stop iterating through gcode if it is

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
                Logger.log("i", f"Established Fisnar serial connection to {self._serial_port_name}")
            except SerialException:  # exception thrown - probably not plugged in
                Logger.log("w", "Exception occured when trying to create serial connection")
                printing_msg = Message(text = catalog.i18nc("@message", "Unable to connect to serial port. Ensure proper port is selected."),
                                       title = catalog.i18nc("@message", "Serial Port Error"))
                printing_msg.show()
                return
            except OSError as e:  # idk when this happens
                Logger.log("w", f"The serial device is suddenly unavailable while trying to connect: {str(e)}")
                printing_msg = Message(text = catalog.i18nc("@message", "Unable to connect to serial port. Ensure proper port is selected."),
                                       title = catalog.i18nc("@message", "Serial Port Error"))
                printing_msg.show()
                return

        self.setConnectionState(ConnectionState.Connected)
        self._update_thread.start()
        self._sendCommand(FisnarCommands.initializer())

    def close(self):
        # closes the serial port and resets _serial member variable to None
        # MAKE SURE FISNAR IS FINALIZED BEFORE CLOSING
        # Logger.log("d", f"serial port was {str(self._serial)}, now closing")

        super().close()  # sets _connection_state to ConnectionState.Closed
        if self._serial is not None:
            self._serial.close()
        self._serial = None

        if self.dispenser.isOpen():  # close dispenser port if not already closed
            self.dispenser.close()

        self._update_thread = Thread(target=self._update, daemon=True, name="FisnarRobotPlugin RS232 Control")

    def _update(self):
        # this continually runs while connected to device, reading lines and
        # sending fisnar commands if necessary
        while self._connection_state == ConnectionState.Connected and self._serial is not None:
            # Logger.log("d", "groovy*****")

            stage = CuraApplication.getInstance().getController().getActiveStage()
            if stage is None or stage.stageId != "MonitorStage":
                time.sleep(1)

            try:
                curr_line = self._serial.readline()
            except:
                continue  # nothing to read

            Logger.log("d", "curr_line: " + str(curr_line))

            if curr_line.startswith(FisnarCommands.expectedReturn(FisnarCommands.initializer())):  # check if fisnar has been initialized and update internal state (finalization check occurs in _sendCommand())
                Logger.log("i", "Fisnar successfully initialized")
                self._fisnar_initialized.set()
            elif curr_line.startswith(b"ok!"):  # confirmation received
                self._command_received.set()
            elif FisnarCommands.isFeedback(curr_line):  # check if value was received
                # Logger.log("d", str(curr_line))
                if not self._x_feedback_received.is_set():  # value is x position
                    self._most_recent_position[0] = float(curr_line[:-2])
                    Logger.log("d", "new x: " + str(self._most_recent_position[0]))
                    self._x_feedback_received.set()
                    self.xPosUpdated.emit()
                    self._y_feedback_received.clear()
                    self.sendCommand(FisnarCommands.PY())
                elif not self._y_feedback_received.is_set():  # value is y position
                    self._most_recent_position[1] = float(curr_line[:-2])
                    Logger.log("d", "new y: " + str(self._most_recent_position[1]))
                    self._y_feedback_received.set()
                    self.yPosUpdated.emit()
                    self._z_feedback_received.clear()
                    self.sendCommand(FisnarCommands.PZ())
                elif not self._z_feedback_received.is_set():  # value is z position
                    self._most_recent_position[2] = float(curr_line[:-2])
                    Logger.log("d", "new z: " + str(self._most_recent_position[2]))
                    self._z_feedback_received.set()
                    self.zPosUpdated.emit()

            # can send next command
            if curr_line.startswith(b"ok!") or curr_line.startswith(FisnarCommands.expectedReturn(FisnarCommands.initializer())):
                # Logger.log("d", "x feedback received set: " + str(self._x_feedback_received.is_set()) + "\ny feedback received set: " + str(self._y_feedback_received.is_set()) + "\nz feedback received set: " + str(self._z_feedback_received.is_set()))
                if not self._button_move_confirm_received.is_set():  # need to update position
                    self._button_move_confirms_received += 1
                    Logger.log("d", "confirms received: " + str(self._button_move_confirms_received))
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

        Logger.log("d", "*****command: " + str(command) + ", sent: " + str(not (self._serial is None or self._connection_state != ConnectionState.Connected)))

        if self._serial is None or self._connection_state != ConnectionState.Connected:
            return

        if command.startswith(FisnarCommands.finalizer()):  # updating state representation if being finalized
            self._fisnar_initialized.clear()
            Logger.log("i", "Fisnar has been finalized.")

        if command.startswith(FisnarCommands.initializer()):
            if self._fisnar_initialized.is_set():  # don't initialize if already initialized
                Logger.log("i", "Fisnar already initialized")
                return
            else:
                self._fisnar_initialized.set()

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

    @pyqtSlot()  # IN PROG
    def executePickPlace(self):
        # start pick and place procedure

        # TODO: ensure parameters and connections are such that pick and place can be done
        if not self.dispenser.isOpen():  # if dispenser not open
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

        for point in (pick_point[0], pick_point[1], place_point[0], place_point[1]):  # checking x/y travel coords
            if not (0.0 <= point <= 200.0):
                Logger.log("w", "pick location or place location has invalid x or y travel coordinate: " + str(point))  # TODO: show error to user
                return

        for point in (pick_point[2], place_point[2]):
            if not (0.0 <= point <= 150.0):
                Logger.log("w", "pick location or place location has invalid z travel coordinate: " + str(point))
                return

        for speed in (xy_speed, z_speed):
            if not (0.0 < speed <= 100):
                Logger.log("w", "pick and place x/y or z speed invalid: " + str(speed))
                return

        for dwell in (pick_dwell, place_dwell):
            if not (0.0 <= dwell <= 60):
                Logger.log("w", "pick and place dwell time out of valid range: " + str(dwell) + " seconds")
                return

        if not (0.0 <= vacuum_pressure <= 999.999):  # should have a different value for each unit, then error check units firsts
            Logger.log("w", "pick and place vacuum pressure invalid: " + str(vacuum_units))
            return

        if vacuum_units not in (0, 1, 2, 3, 4):
            Logger.log("w", "pick and place vacuum units are invalid: enumeration<" + str(vacuum_units) + ">")
            return

        # TODO: call external function for generating pick and place commands from parameters
        self._pick_place_commands = PickAndPlaceGenerator.getCommands(
            pick_point,
            place_point,
            xy_speed,
            z_speed,
            pick_dwell,
            place_dwell,
            vacuum_pressure,
            vacuum_units
        )

        # for command in self._pick_place_commands:
        #     Logger.log("d", "***** " + str(command[0]) + " " + str(command[1]))

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
    def homeXY(self):
        self._button_move_confirm_received.clear()
        self._button_move_confirms_received = 0  # still needs two confirms - one for each hm command
        self._sendCommand(FisnarCommands.HX())
        self.sendCommand(FisnarCommands.HY())

    @pyqtSlot()
    def homeZ(self):
        self._button_move_confirm_received.clear()
        self._button_move_confirms_received = 1  # kind of hacky but it works - this makes the _update loop only need to look for one more ok! confirm before sending coord feedback commands
        self._sendCommand(FisnarCommands.HZ())

    ################################
    # QML Stuff
    ################################

    @pyqtSlot()
    def pauseOrResumePrint(self):
        Logger.log("i", "Fisnar serial print has been " + ("resumed" if self._is_paused else "paused") + ".")
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

# ------------------- dispenser serial port property setup -------------------------
    def _onExternalDispenserSerialUpdated(self):  # very hacky. should figure a way around this.
        self.dispenserSerialPortUpdated.emit()

    dispenserSerialPortUpdated = pyqtSignal()
    @pyqtProperty(str, notify=dispenserSerialPortUpdated)
    def dispenser_serial_port(self):
        return str(self._fre_instance.dispenser_com_port)

    @pyqtSlot(str)
    def setDispenserSerialPort(self, serial_port_name):
        self._fre_instance.dispenser_com_port = str(serial_port_name)
        self._fre_instance.updatePreferencedValues()
        self._fre_instance.dispenserSerialPortUpdated.emit()

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
        return self.dispenser.isOpen()

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

    # # TEST - for testing UI under different conditions --------
    # @pyqtSlot()
    # def flipPrintingState(self):
    #     if self._is_printing:
    #         self.setPrintingState(False)
    #     else:
    #         self.setPrintingState(True)
    # @pyqtSlot()
    # def flipConnectionState(self):
    #     if self._connection_state == ConnectionState.Closed:
    #         self.setConnectionState(ConnectionState.Connected)
    #     else:
    #         self.setConnectionState(ConnectionState.Closed)
    # # ----------------------------------------------------------
