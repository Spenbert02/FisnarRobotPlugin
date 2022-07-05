import os
import os.path
import threading
import time

from cura.CuraApplication import CuraApplication
from cura.PrinterOutput.PrinterOutputDevice import PrinterOutputDevice, ConnectionType, ConnectionState
from io import StringIO
from PyQt6.QtCore import pyqtProperty, pyqtSignal, pyqtSlot
from serial import Serial, SerialException, SerialTimeoutException
from UM.Resources import Resources
from UM.Logger import Logger
from UM.Message import Message
from .Converter import Converter
from .FisnarCSVWriter import FisnarCSVWriter
from .FisnarRobotExtension import FisnarRobotExtension

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")

class FisnarOutputDevice(PrinterOutputDevice):

    def __init__(self):
        super().__init__("fisnar_f5200n")

        # OutputDevice plugin UI stuff
        self.setName("Fisnar F5200N")
        self.setShortDescription("Print Over RS232")
        self.setDescription("Print Over RS232")
        self.setIconName("print")

        # Fisnar command storage/tracking
        self._fisnar_commands = []  # type: list[list[str, int, float]]
        self._current_index = 0

        # for tracking printing state
        self._is_printing = False
        self._is_paused = False
        self._is_terminated = False

        # for connecting to serial port
        self._serial = None
        self._serial_port_name = None
        self._timeout = 10
        self._baud_rate = 115200

        # for showing monitor while printing
        self._plugin_path = os.path.join(Resources.getStoragePath(Resources.Resources, "plugins", "FisnarRobotPlugin", "FisnarRobotPlugin"))
        self._monitor_view_qml_path = os.path.join(self._plugin_path, "resources", "qml", "MonitorItem.qml")

        # update thread for printing
        self._update_thread = threading.Thread(target=self._update)

        # fisnar robot extension instance
        self._fre_instance = FisnarRobotExtension.getInstance()

        # for checking if Fisnar is printing while trying to exit app
        CuraApplication.getInstance().getOnExitCallbackManager().addCallback(self._checkActivePritingOnAppExit)

    def _checkActivePritingOnAppExit(self):
        # called when user tries to exit app - checks if Fisnar is trying to print
        application = CuraApplication.getInstance()
        if not self._is_printing:  # not printing, so continue with exit checks
            application.triggerNextExitCheck()
            return

        application.setConfirmExitDialogCallback(self._onConfirmExitDialogResult)
        application.showConfirmExitDialog.emit(catalog.i18nc("@label", "Fisnar print is in progress - closing Cura will stop this print. Are you sure?"))

    def _onConfirmExitDialogResult(self, result):
        # triggers when user clicks cancel or confirm on the confirm exit dialog
        if result:
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
        if not success:
            Logger.log("e", "FisnarCSVWriter failed in requestWrite()")
            return

        self.connect()  # attempting to connect

        self._printFisnarCommands(fisnar_command_csv_io.getvalue())  # starting print

    # IN PROG
    def _printFisnarCommands(self, fisnar_command_csv):
        # start a print based on a 2d array of fisnar commands

        # updating fisnar commands / current index
        self._fisnar_commands.clear()
        self._fisnar_commands = Converter.readFisnarCommandsFromCSV(fisnar_command_csv)
        self._current_index = 0

        # print status stuff
        self._is_printing = True
        self._is_paused = False
        self._is_terminated = False

        # DO ANY MORE SETUP STUFF HERE (reference USBPrinterOutputDevice)

    def connect(self):
        # try to establish serial connection and store Serial object
        Logger.log("i", "Attempting to connect to Fisnar")

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

    def close(self):
        Logger.log("d", f"serial port was {self._serial}, now closing")
        super().close()
        if self._serial is not None:
            self._serial.close()

    def _update(self):
        while True:
            Logger.log("d", "********* _update() called")
            time.sleep(5)

    def sendCommand(self):
        pass

    def _sendCommand(self):
        pass

    def _sendNextFisnarLine(self):
        pass

    def _getPrintingProgress(self):
        try:
            return self._current_index / len(self._fisnar_commands)
        except ZeroDivisionError:
            return None  # signals print hasn't started yet

    ################################
    # QML Stuff
    ################################

    # IN PROG
    @pyqtSlot()
    def pauseOrResumePrint(self):
        Logger.log("i", "Fisnar serial print has been " + ("resumed" if self._is_paused else "paused") + ".")
        self._is_paused = not self._is_paused  # flips whether print is paused or not
        if not self._is_paused:
            pass

    # IN PROG
    @pyqtSlot()
    def terminatePrint(self):  # called when the user presses the 'Terminate' button
        Logger.log("i", "Fisnar serial print has been terminated.")
        self._is_terminated = True

    printProgressUpdated = pyqtSignal()  # signal to update printing progress

    @pyqtProperty(str, notify=printProgressUpdated)
    def print_progress(self):
        printing_prog = self._getPrintingProgress()
        if printing_prog is None:
            return "n/a"
        else:
            return str(round(printing_prog, 2))
