import os
import os.path
import time

from cura.CuraApplication import CuraApplication
from cura.PrinterOutput.PrinterOutputDevice import PrinterOutputDevice, ConnectionType, ConnectionState
from io import StringIO
from PyQt6.QtCore import pyqtProperty, pyqtSignal, pyqtSlot
from queue import Queue
from serial import Serial, SerialException, SerialTimeoutException
from threading import Event, Thread
from UM.Resources import Resources
from UM.Logger import Logger
from UM.Message import Message
from .Converter import Converter
from .Fisnar import Fisnar
from .FisnarCSVWriter import FisnarCSVWriter
from .FisnarRobotExtension import FisnarRobotExtension

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

class FisnarOutputDevice(PrinterOutputDevice):

    def __init__(self):
        super().__init__("fisnar_f5200n", ConnectionType.UsbConnection)

        # OutputDevice plugin UI stuff
        self.setName("Fisnar F5200N")
        self.setShortDescription("Print Over RS232")
        self.setDescription("Print Over RS232")
        self.setIconName("print")

        # Fisnar command storage/tracking
        self._fisnar_commands = []  # type: list[bytes]
        self._current_index = 0

        # for tracking printing state
        self._is_printing = False
        self._is_paused = False

        self._command_queue = Queue()  # queue to hold commands to be sent
        self._command_received = Event()  # event that is set when the Fisnar sends 'ok!' and cleared when waiting for an 'ok!' confirm from the Fisnar

        self._fisnar_initialized = Event()  # event for tracking state of printer - set when initialized, and cleared when finalized

        # for connecting to serial port
        self._serial = None
        self._serial_port_name = None
        self._timeout = 10
        self._baud_rate = 115200

        # for showing monitor while printing
        self._plugin_path = os.path.join(Resources.getStoragePath(Resources.Resources, "plugins", "FisnarRobotPlugin", "FisnarRobotPlugin"))
        self._monitor_view_qml_path = os.path.join(self._plugin_path, "resources", "qml", "MonitorItem.qml")

        # update thread for printing
        self._update_thread = Thread(target=self._update, daemon=True, name="FisnarRobotPlugin RS232 Control")

        # fisnar robot extension instance
        self._fre_instance = FisnarRobotExtension.getInstance()

        # for checking if Fisnar is printing while trying to exit app
        CuraApplication.getInstance().getOnExitCallbackManager().addCallback(self._checkActivePritingOnAppExit)

    def _checkActivePritingOnAppExit(self):
        # called when user tries to exit app - checks if Fisnar is trying to print
        application = CuraApplication.getInstance()
        if not self._is_printing:  # not printing, so lose serial port and continue with exit checks
            time.sleep(5)
            self.close()
            application.triggerNextExitCheck()
            return

        application.setConfirmExitDialogCallback(self._onConfirmExitDialogResult)
        application.showConfirmExitDialog.emit(catalog.i18nc("@label", "Fisnar print is in progress - closing Cura will stop this print. Are you sure?"))

    def _onConfirmExitDialogResult(self, result):
        # triggers when user clicks cancel or confirm on the confirm exit dialog
        if result:
            self._is_printing = False
            self.sendCommand(Fisnar.HM())
            while not self._command_queue.empty():
                Logger.log("d", "not empty")
                self._command_received.wait(5)  # wait until commands are done being sent
            self.close()  # ensuring fisnar is finalized and port is closed when exiting app
            CuraApplication.getInstance().triggerNextExitCheck()

    def close(self):
        Logger.log("d", f"serial port was {str(self._serial)}, now closing")

        # ensuring the fisnar is not still initialized
        Logger.log("d", f"serial : {str(self._serial)}, connection : {self._connection_state}")
        if self._serial is not None and self._connection_state == ConnectionState.Connected:
            Logger.log("i", "sending finalizer ********")
            self._sendCommand(Fisnar.finalizer())

        super().close()  # sets _connection_state to ConnectionState.Closed
        if self._serial is not None:
            self._serial.close()
        self._serial = None

        # recreate thread so it can be started again? not sure why this is necessary
        self._update_thread = Thread(target=self._update, daemon=True, name="FisnarRobotPlugin RS232 Control")

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
            Logger.log("d", "Serial port created, _printFisnarCommands() called")
            self._printFisnarCommands(fisnar_command_csv_io.getvalue())  # starting print

    # IN PROG
    def _printFisnarCommands(self, fisnar_command_csv):
        # start a print based on a fisnar command csv

        # updating fisnar command bytes from fisnar_command_csv
        commands = Converter.readFisnarCommandsFromCSV(fisnar_command_csv)
        self._fisnar_commands.clear()
        self._fisnar_commands.append(Fisnar.initializer())  # initial command
        for command in commands:
            if command[0] == "Dummy Point":
                self._fisnar_commands.append(Fisnar.VA(command[1], command[2], command[3]))
                self._fisnar_commands.append(Fisnar.ID())
            elif command[0] == "Output":
                self._fisnar_commands.append(Fisnar.OU(command[1], command[2]))
            elif command[0] == "Line Speed":
                self._fisnar_commands.append(Fisnar.SP(command[1]))
            elif command[0] == "End Program":
                pass
            else:
                Logger.log("w", "Unrecognized command found when uploading over Serial port: " + str(command[0]))

        self._current_index = 0  # resetting command index

        # print status stuff
        self._is_printing = True
        self._is_paused = False

        self._sendNextFisnarLine()  # push the first command to start the 'ok!' loop

        Logger.log("d", "end of _printFisnarCommands")  # test

    def isConnected(self):
        # Logger.log("d", f"serial port: {self._serial}")
        return self._serial is not None

    def connect(self):
        # try to establish serial connection and store Serial object. called whenever a print is started
        Logger.log("i", "Attempting to connect to Fisnar...")

        if self._serial is None:
            self._serial_port_name = str(self._fre_instance.getComPortName())
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

    # IN PROG
    def _update(self):
        # this continually runs while connected to device, reading lines and
        # sending fisnar commands if necessary
        while self._connection_state == ConnectionState.Connected and self._serial is not None:
            Logger.log("d", "groovy*****")
            try:
                curr_line = self._serial.readline()
            except:
                continue  # nothing to read

            # need to check for feedback response commands here (PX, PY, PZ response values)
            # will probably have to indicate in a member Event() what value is currently expected

            # check if fisnar has been initialized and update internal state (finalization check occurs in _sendCommand())
            if curr_line.startswith(Fisnar.expectedReturn(Fisnar.initializer())):
                Logger.log("i", "Fisnar successfully initialized")
                self._fisnar_initialized.set()

            if curr_line.startswith(b"ok!"):  # confirmation received
                self._command_received.set()

            # can send next command
            if curr_line.startswith(b"ok!") or curr_line.startswith(Fisnar.expectedReturn(Fisnar.initializer())):
                if not self._command_queue.empty():
                    self._sendCommand(self._command_queue.get())
                elif self._is_printing:  # still printing but queue is empty
                    if not self._is_paused:
                        self._sendNextFisnarLine()

    def sendCommand(self, command):
        # command: fisnar command as bytes
        # send a fisar command (or put into command queue if waiting for Fisnar command confirmation)
        if not self._command_received.is_set():  # if waiting for confirmation
            self._command_queue.put(command)
        else:
            self._sendCommand(command)

    def _sendCommand(self, command):
        # given a fisnar command as a byte array, send it to the fisnar.
        # this function doesn't check for anything besides Serial Exceptions.
        # this functio also clears the command recieved event, so this should
        # only be called if there are no expected confirmation responses
        if self._serial is None or self._connection_state != ConnectionState.Connected:
            return

        if command.startswith(Fisnar.finalizer()):  # updating state representation if being finalized
            self._fisnar_initialized.clear()
            Logger.log("i", "Fisnar has been finalized.")

        if command.startswith(Fisnar.initializer()):
            if self._fisnar_initialized.is_set():  # don't initialize if already initialized
                Logger.log("i", "Fisnar already initialized")
                return

        # actually sending bytes
        try:
            self._command_received.clear()
            self._serial.write(command)
            Logger.log("d", f"bytes written: {command}")
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
            self._is_printing = False
            return

        self._sendCommand(command_bytes)  # send bytes

        self._current_index += 1  # update current index
        self.printProgressUpdated.emit()  # recalculate progress and update QML


    def _getPrintingProgress(self):
        try:
            return self._current_index / len(self._fisnar_commands)
        except ZeroDivisionError:
            return None  # signals print hasn't started yet

    ################################
    # QML Stuff
    ################################

    @pyqtSlot()
    def pauseOrResumePrint(self):
        Logger.log("i", "Fisnar serial print has been " + ("resumed" if self._is_paused else "paused") + ".")
        self._is_paused = not self._is_paused  # flips whether print is paused or not
        if not self._is_paused:
            self._sendNextFisnarLine()

    @pyqtSlot()
    def terminatePrint(self):
        # called when the user presses the 'Terminate' button. this finalizes
        # the fisnar and resets all internal states
        Logger.log("i", "Fisnar serial print has been terminated.")

        # resetting fisnar commands
        self._fisnar_commands.clear()
        self._current_index = 0

        # this combination of states signals that no print has started or a print has been terminated
        self._is_printing = False
        self._is_paused = False

        # homing fisnar
        self._sendCommand(Fisnar.HM())

    printProgressUpdated = pyqtSignal()  # signal to update printing progress

    @pyqtProperty(str, notify=printProgressUpdated)
    def print_progress(self):
        printing_prog = self._getPrintingProgress()
        if printing_prog is None:
            return "n/a"
        else:
            return str(round(printing_prog * 100, 2))
