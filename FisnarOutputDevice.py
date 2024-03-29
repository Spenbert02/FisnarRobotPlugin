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


class FisnarOutputTracker:
    # class for tracking output states - this is an independent class because
    # in the future there may need to be a signal system for when outputs are
    # turned on or off

    def __init__(self):
        self._outputs = [False, False, False, False]
        self._most_recent_output = None

    def logOutputs(self):
        log_str = "\n active output: " + str(self._most_recent_output)
        for i in range(4):
            log_str += "\n output " + str(i + 1) + ": " + str(self._outputs[i])
        Logger.log("d", log_str)

    def setOutput(self, output, state):
        self._outputs[output - 1] = state
        self._most_recent_output = output

    def getOutput(self, output):
        return self._outputs[output - 1]

    def getActiveOutput(self):
        return self._most_recent_output

    def allOff(self):
        for output in self._outputs:
            if output:
                return False
        return True

    def allOn(self):
        for output in self._outputs:
            if not output:
                return False
        return True


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
        self._printing_commands = []  # type: list[list[str, bytes]] (fisnar/dispenser mixed command format)
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
        self._outputs = FisnarOutputTracker()

        self._command_queue = Queue()  # queue to hold commands to be sent
        self._command_received = Event()  # event that is set when the Fisnar sends 'ok!' and cleared when waiting for an 'ok!' confirm from the Fisnar

        self._empty_byte_count = 0
        self._connect_confirm_received = Event()  # for tracking whether the fisnar is still connected
        self._connect_confirm_received.set()  # needs to be initially set
        self._connect_confirm_send_time = None

        self._init_connect_send_time = None  # type: float

        # for connecting to serial port
        self._serial = None  # type: serial.Serial
        self._fisnar_serial_port_name = None  # type: str or None
        self._timeout = 3
        self._baud_rate = 115200

        # for updating position when not printing
        self._most_recent_position = [0.0, 0.0, 0.0]
        self._button_move_confirm_received = Event()
        self._button_move_confirms_received = 0
        self._x_feedback_received = Event()
        self._y_feedback_received = Event()
        self._z_feedback_received = Event()

        # for showing monitor while printing
        self._plugin_path = os.path.join(Resources.getStoragePath(Resources.Resources, "plugins", "FisnarRobotPlugin", "FisnarRobotPlugin"))
        self._monitor_view_qml_path = os.path.join(self._plugin_path, "resources", "qml", "MonitorItem.qml")

        # update thread for printing
        self._update_thread = Thread(target=self._update, daemon=True, name="FisnarRobotPlugin RS232 Control")

        # fre instance
        self._fre_instance = FisnarRobotExtension.getInstance()
        self._dispenser_manager = self._fre_instance.getDispenserManager()
        self._dispenser_command_sent = Event()

        # for checking if Fisnar is printing while trying to exit app
        CuraApplication.getInstance().getOnExitCallbackManager().addCallback(self._checkActivePritingOnAppExit)

    def _checkActivePritingOnAppExit(self):
        # called when user tries to exit app - checks if Fisnar is trying to print
        application = CuraApplication.getInstance()
        if not (self._is_printing or self._pick_place_in_progress):  # not printing, so lose serial port and continue with exit checks
            if self._connection_state == ConnectionState.Connected:
                self.stopPrintingAndFinalize()  # print is already stopped but doesn't matter
            self.close()
            self._dispenser_manager.closeAll()
            application.triggerNextExitCheck()
            return

        application.setConfirmExitDialogCallback(self._onConfirmExitDialogResult)
        application.showConfirmExitDialog.emit(catalog.i18nc("@label", "Fisnar " + ("print" if self._is_printing else "pick and place") + " is in progress - closing Cura will stop this print. Are you sure?"))

    def _onConfirmExitDialogResult(self, result):
        # triggers when user clicks cancel or confirm on the confirm exit dialog
        if result:
            self.stopPrintingAndFinalize()
            self.close()  # ensuring fisnar is finalized and port is closed when exiting app
            self._dispenser_manager.closeAll()
            CuraApplication.getInstance().triggerNextExitCheck()

    def setConnectionState(self, connection_state):
        # method to set the connection state - needs to override the base method in PrinterOutputDevice so that
        # the state can also be updated in FisnarRobotExtension

        if self.connectionState != connection_state:
            self._connection_state = connection_state
            self._fre_instance.setFisnarConnectionState(self._connection_state == ConnectionState.Connected)
            application = CuraApplication.getInstance()
            if application is not None:  # Might happen during the closing of Cura or in a test.
                global_stack = application.getGlobalContainerStack()
                if global_stack is not None:
                    global_stack.setMetaDataEntry("is_online", self.isConnected())
            self.connectionStateChanged.emit(self._id)

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
            necessary_outputs = Converter.getOutputsInFisnarCommands(Converter.readFisnarCommandsFromCSV(fisnar_command_csv_io.getvalue()))
            for i in range(4):  # ensure necessray dispensers are connected
                if necessary_outputs[i]:
                    if not self._dispenser_manager.getDispenser("dispenser_" + str(i + 1)).isConnected():
                        printing_msg = Message(text = catalog.i18nc("@message", f"Dispenser {i + 1} is not yet connected. Ensure the proper serial port name has been entered under 'Fisnar Actions' -> 'Define Setup' and that the dispenser is on."),
                                               title = catalog.i18nc("@message", "Dispenser Not Connected"))
                        printing_msg.show()
                        return

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
        self._printing_commands.clear()
        self._printing_commands = Converter.fisnarCommandsToBytes(commands, self._fre_instance.continuous_extrusion)

        self._current_index = 0  # resetting command index

        # print status stuff
        self.setPrintingState(True)
        self._is_paused = False

        for i in range(2):
            self._sendNextFisnarLine()  # push the first command to start the ok loop

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
        self._fisnar_serial_port_name = serial_name

        if self._serial is None:
            try:
                self._serial = Serial(self._fisnar_serial_port_name, self._baud_rate, timeout=self._timeout, writeTimeout=self._timeout)
                Logger.log("i", f"Serial port {self._fisnar_serial_port_name} is open. Testing if fisnar is on...")
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
                self.home()
                return

        self._sendCommand(FisnarCommands.finalizer())  # in case couldn't connect because already initialized
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
            if not self._dispenser_command_sent.is_set():
                try:
                    curr_line = self._serial.readline()
                except:
                    continue
            else:
                curr_line = b""

            if self._dispenser_command_sent.is_set() or curr_line.startswith(b"ok!"):

                if self._dispenser_command_sent.is_set():
                    self._dispenser_command_sent.clear()
                elif curr_line.startswith(b"ok!"):
                    self._empty_byte_count = 0
                    self._command_received.set()

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

            elif curr_line == bytes():
                if self._connect_confirm_received.is_set():  # not already confirming
                    self._empty_byte_count += 1
                    if self._empty_byte_count >= 5:  # send connect confirmation command and wait for return bytes
                        Logger.log("i", "fisnar may be unresponsive, will attempt to confirm connection status")
                        self.sendCommand(FisnarCommands.PX())
                        self._connect_confirm_send_time = time.time()
                        self._connect_confirm_received.clear()
                        self._empty_byte_count = 0
                else:  # trying to confirm
                    if time.time() - self._connect_confirm_send_time > 5.0:  # 10 sec since sending confirm command
                        Logger.log("w", "fisnar unresponsive, will disconnect and attempt to reconnect")
                        self._connect_confirm_received.set()  # reset in case it reconnects and begins checking again
                        msg = Message(text = catalog.i18nc("@message", "Fisnar F5200N is unresponsive, will attempt to regain connection..."),
                                      title = catalog.i18nc("@message", "Unresponsive Peripheral"))
                        msg.show()
                        self.close()
            elif FisnarCommands.isFeedback(curr_line):  # check if value was received
                self._empty_byte_count = 0
                # Logger.log("d", str(curr_line))
                if not self._connect_confirm_received.is_set():  # PX() sent to confirm connection status
                    Logger.log("i", "Fisnar connection status confirmed")
                    self._connect_confirm_received.set()  # connection status confirmed
                elif not self._x_feedback_received.is_set():  # value is x position
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
        if len(command) > 2 and command[:2] == bytes("OU", "ascii"):  # is an output command - assumes format 'OU n, s'
            if self._outputs.getOutput(int(chr(command[3]))) != (int(chr(command[6])) == 1):  # if change in output state
                self._outputs.setOutput(int(chr(command[3])), int(chr(command[6])) == 1)
                dispenser_name = "dispenser_" + str(chr(command[3]))
                self._dispenser_manager.busy = True
                self._dispenser_manager.getDispenser(dispenser_name).sendCommand(UltimusV.dispenseToggle())  # TODO: handle potential errors here
            self._dispenser_command_sent.set()
            return

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
            command_bytes = self._printing_commands[self._current_index]
        except IndexError:  # done printing!
            Logger.log("i", "Fisnar done with print.")

            # stop printing
            self.setPrintingState(False)
            self._is_paused = False

            # clean things up
            self._sendCommand(FisnarCommands.OU(1, 0))
            self._sendCommand(FisnarCommands.OU(2, 0))
            self._sendCommand(FisnarCommands.HM())

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
                success = self._dispenser_manager.getPickPlaceDispenser().sendCommand(next_command[1])
                if not success:  # TODO: show error to the user here
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
            self._is_printing = printing_state

            if self._is_printing:  # update business state of dispensers while printing
                for dispenser in self._dispenser_manager.getDispensers():
                    dispenser.busy = True
            else:
                for dispenser in self._dispenser_manager.getDispensers():
                    dispenser.busy = False

            self.printingStatusUpdated.emit()

    def setPickPlaceStatus(self, pick_place_status):
        if self._pick_place_in_progress != pick_place_status:
            self._pick_place_in_progress = pick_place_status

            if self._pick_place_in_progress:  # update 'busy' state of pick and place dispenser
                self._dispenser_manager.getPickPlaceDispenser().busy = True
            else:
                self._dispenser_manager.getPickPlaceDispenser().busy = False

            self.pickPlaceStatusUpdated.emit()

    def _resetPrintingInternalState(self):
        # resets internal printing state - called after user terminates print
        # or after print is finished. Assumes self._is_printing has already
        # been set to false
        self._printing_commands.clear()
        self._current_index = 0
        self.printProgressUpdated.emit()  # reset UI

    def _resetPickAndPlaceInternalState(self):
        # reset the internal pick and place parameters - assumes pick and place
        # status has already been updated
        self._pick_place_commands.clear()
        self._pick_place_index = 0

    def _getPrintingProgress(self):
        try:
            return self._current_index / len(self._printing_commands)
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
        if not self._dispenser_manager.getPickPlaceDispenser().isConnected():  # if dispenser not connected
            Logger.log("w", "Pick and place dispenser is not open, pick and place execution terminated.")
            msg = Message(text = catalog.i18nc("@message", f"UltimusV dispenser '{self._dispenser_manager.getPickPlaceDispenser().display_name}' at {self._dispenser_manager.getPickPlaceDispenser().getComPort()} is not connected. Ensure the proper serial port is selected and the dispenser is on"),
                          title = catalog.i18nc("@message", "Unable to Execute Pick and Place"))
            msg.show()
            return

        if not self._connection_state == ConnectionState.Connected:  # this should never happen, because the fisnar has to be connected for the execute pick and place button to appear
            Logger.log("w", "Fisnar is not connected, pick and place execution terminated")
            return

        pick_point = self._fre_instance.pick_location
        place_point = self._fre_instance.place_location
        xy_speed = self._fre_instance.xy_speed
        pick_z_speed = self._fre_instance.pick_z_speed
        place_z_speed = self._fre_instance.place_z_speed
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
            pick_z_speed,
            place_z_speed,
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

        # # ensure outputs are off, then home
        self.sendCommand(FisnarCommands.OU(1, 0))
        self.sendCommand(FisnarCommands.OU(2, 0))
        self.sendCommand(FisnarCommands.HM())

        self._resetPrintingInternalState()  # resets fisnar commands, current command index

    @pyqtSlot()
    def terminatePickPlace(self):
        # terminate the pick and place procedure
        Logger.log("i", "Fisnar pick and place terminated")

        self.setPickPlaceStatus(False)
        self._resetPickAndPlaceInternalState()

        self.sendCommand(FisnarCommands.HM())
        self._dispenser_manager.getPickPlaceDispenser().sendCommand(UltimusV.setVacuum(0, PressureUnits.V_KPA))

    @pyqtSlot(str, result=str)
    def getTooltip(self, id):
        return self._fre_instance.getTooltip(id)

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
        if x != "-1":
            self._fre_instance.pick_location[0] = float(x)
        if y != "-1":
            self._fre_instance.pick_location[1] = float(y)
        if z != "-1":
            self._fre_instance.pick_location[2] = float(z)

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
        if x != "-1":
            self._fre_instance.place_location[0] = float(x)
        if y != "-1":
            self._fre_instance.place_location[1] = float(y)
        if z != "-1":
            self._fre_instance.place_location[2] = float(z)

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

# ------------------ pick z speed property setup -----------------------------
    pickZSpeedUpdated = pyqtSignal()
    @pyqtProperty(str, notify=pickZSpeedUpdated)
    def pick_z_speed(self):
        return str(self._fre_instance.pick_z_speed)

    @pyqtSlot(str)
    def setPickZSpeed(self, speed):
        self._fre_instance.pick_z_speed = float(speed)
        self._fre_instance.updatePreferencedValues()

# --------------- place z speed prop setup ----------------------
    placeZSpeedUpdated = pyqtSignal()
    @pyqtProperty(str, notify=placeZSpeedUpdated)
    def place_z_speed(self):
        return str(self._fre_instance.place_z_speed)

    @pyqtSlot(str)
    def setPlaceZSpeed(self, speed):
        self._fre_instance.place_z_speed = float(speed)
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

# -------------- dispenser for pick and place ------------------------
    pickPlaceDispenserUpdated = pyqtSignal()
    @pyqtProperty(int, notify=pickPlaceDispenserUpdated)
    def pick_place_dispenser_index(self):
        if self._dispenser_manager.getPickPlaceDispenserName() == "dispenser_1":
            return 0
        elif self._dispenser_manager.getPickPlaceDispenserName() == "dispenser_2":
            return 1
        else:
            Logger.log("w", "pick and place dispenser not set dispenser manager: " + str(self._dispenser_manager.getPickPlaceDispenserName()))
            return 0  # default to dispenser 1

    @pyqtSlot(str)
    def setPickPlaceDispenser(self, id):
        self._dispenser_manager.setPickPlaceDispenser(id)
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
