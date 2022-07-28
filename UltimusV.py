import time
from cura.PrinterOutput.PrinterOutputDevice import ConnectionState
from cura.PrinterOutput.Peripheral import Peripheral
from queue import Queue
from serial import Serial, SerialException, SerialTimeoutException
from threading import Event, Thread
from UM.Logger import Logger
from UM.Message import Message
from UM.Signal import Signal

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")


class PressureUnits:  # enumeration class for pressure units
    # vacuum units
    V_KPA = 0
    INH2O = 1
    INHG = 2
    MMHG = 3
    TORR = 4

    # pressure units
    PSI = 5
    BAR = 6
    P_KPA = 7


class UltimusV(Peripheral):
    # class for communicating with the UltimusV dispenser unit

    STX = bytes.fromhex("02")
    ETX = bytes.fromhex("03")
    EOT = bytes.fromhex("04")
    ENQ = bytes.fromhex("05")

    connectionStateUpdated = Signal()

    def __init__(self, name, *args):
        super().__init__("dispenser", name)

        # port attributes
        self._serial = None
        self._serial_port_name = None
        self._timeout = 3
        self._baud_rate = 9600

        self._connection_state = ConnectionState.Closed

        self._command_queue = Queue()
        self._command_received = Event()

        self.command_send_complete = Event()

        # initial connecting stuff
        self._init_connect_send_time = None

        self._update_thread = Thread(target=self._update, daemon=True, name="UltimusV Control")

        self.busy = False

    def sendCommand(self, command_bytes):
        # send a command to the Ultimus V and return True if it was successful
        # or False if it was not

        if not self._command_received.is_set():
            self._command_queue.put(command_bytes)
        else:
            self._sendCommand(command_bytes)

    def _sendCommand(self, command_bytes):
        if self._serial is None or self._connection_state not in (ConnectionState.Connected, ConnectionState.Connecting):
            return

        command_bytes = UltimusV.ENQ + UltimusV.STX + UltimusV.intToHexBytes(len(command_bytes)) + command_bytes + self._checksum(UltimusV.intToHexBytes(len(command_bytes)) + command_bytes) + UltimusV.ETX + UltimusV.EOT

        try:
            self._serial.write(command_bytes)
            self._command_received.clear()
        except SerialTimeoutException:
            self._command_received.set()
            Logger.log("w", "_serial timeout when sending bytes: " + str(command_bytes))
        except SerialException:
            self.setConnectionState(ConnectionState.Error)
            Logger.log("w", "unexpected serial error occured when sending bytes:" + str(command_bytes))

    def _update(self):
        while self._connection_state == ConnectionState.Connected and self._serial is not None:
            time.sleep(1)
            try:
                curr_line == self._serial.readline()
            except:
                continue

            if len(curr_line) >= 6 and curr_line[4:6] == UltimusV.success():
                Logger.log("i", f"{self.name} received command: {curr_line}")
                self._command_received.set()
                self.command_send_complete.set()
                if not self._command_queue.empty():
                    self._sendCommand(self._command_queue.get())
            else:
                Logger.log("i", "nothing received")

    def setComPort(self, name):
        self._serial_port_name = name

    def getComPort(self):
        return self._serial_port_name

    def connect(self, port_name=None):
        if port_name is None and self._serial_port_name is None:
            return
        else:
            port_name = self._serial_port_name

        Logger.log("i", "attempting to connect to dispenser unit...")
        self._serial_port_name = port_name

        if self._serial is None:
            try:
                self._serial = Serial(self._serial_port_name, self._baud_rate, timeout=self._timeout, write_timeout=self._timeout)
                Logger.log("i", f"Serial port {self._serial_port_name} is open. Testing if the UltimusV dispenser is on...")
            except SerialException:
                Logger.log("w", "Exception occured when trying to create serial connection")
                err_msg = Message(text = catalog.i18nc("@message", f"Unable to connect to serial port for '{self.name}' at '{self._serial_port_name}'. Ensure proper port is selected"),
                                  title = catalog.i18nc("@message", "Serial Port Error"))
                err_msg.show()
                return
            except OSError as e:
                Logger.log("w", f"The serial device is suddenly unavailable when trying to connect: {str(e)}")
                err_msg = Message(text = catalog.i18nc("@message", f"Unable to connect to serial port for '{self.name}' at '{self._serial_port_name}'. Ensure proper port is selected"),
                                  title = catalog.i18nc("@message", "Serial Port Error"))
                err_msg.show()
                return

        # serial port is open, but dispenser might not be on.
        self.setConnectionState(ConnectionState.Connecting)
        self._sendCommand(UltimusV.setVacuum(0.0, PressureUnits.V_KPA))
        self._init_connect_send_time = time.time()
        while time.time() - self._init_connect_send_time < 5.0:
            try:
                curr_line = self._serial.readline()
            except:
                continue

            Logger.log("d", "curr_line: " + str(curr_line))
            if curr_line[4:6] == UltimusV.success():
                self._command_received.set()
                Logger.log("i", "dispenser '" + str(self.name) + "' successfully connected at: " + str(self._serial_port_name))
                self.setConnectionState(ConnectionState.Connected)
                self._update_thread.start()
                return

        Logger.log("w", "dispenser failed to connect...")
        self.close()

    def close(self):
        self.setConnectionState(ConnectionState.Closed)
        if self._serial is not None:
            self._serial.close()
        self._serial = None

        self._update_thread = Thread(target=self._update, daemon=True, name="UltimusV Control")

    def isConnected(self):
        return self._connection_state == ConnectionState.Connected

    def setConnectionState(self, state):
        # use PrinterOutputDevice as a template for this
        if self._connection_state != state:
            self._connection_state = state
            self.connectionStateUpdated.emit()

    def _checksum(self, byte_array):
        # get the checksum (as a two byte array in forward order) from an
        # array of bytes
        antisum = 0
        for byte in byte_array:
            antisum -= byte
        antisum = antisum % 256

        return UltimusV.intToHexBytes(antisum)

    @staticmethod
    def success():
        # get the 'confirmation' byte code used by the Ultimus
        return bytes("A0", "ascii")

    @staticmethod
    def failure():
        # get the 'failure' byte code used by the Ultimus
        return bytes("A2", "ascii")

    @staticmethod
    def setPressure(pressure, units):
        # command 2.2.5 in manual
        #
        # set the pressure value of the dispenser - this DOES NOT turn the
        # dispenser on, like it does for the analogous vacuum command
        val_bytes = UltimusV.valueBytes(pressure, units)
        return bytes("PS  ", "ascii") + val_bytes

    @staticmethod
    def setVacuum(vacuum, units):
        # command 2.2.7 in manual
        #
        # set the vacuum to a certain pressure and TURN IT ON. This does not
        # just set the vacuum units, it sets the vacuum units and then turns
        # the vacuum on. To turn off the vacuum, set the vacuum value to 0
        val_bytes = UltimusV.valueBytes(vacuum, units)
        return bytes("VS  ", "ascii") + val_bytes

    @staticmethod
    def setPressureUnits(units):
        # command 2.2.12 in manual
        #
        # set the current pressure units for the dispenser
        if units == PressureUnits.PSI:
            return bytes("E6  00", "ascii")
        elif units == PressureUnits.BAR:
            return bytes("E6  01", "ascii")
        elif units == PressureUnits.P_KPA:
            return bytes("E6  02", "ascii")

    @staticmethod
    def setVacuumUnits(units):
        # command 2.2.13 in manual
        #
        # set the vacuum units of the dispenser.
        if units == PressureUnits.V_KPA:
            return bytes("E7  00", "ascii")
        elif units == PressureUnits.INH2O:
            return bytes("E7  01", "ascii")
        elif units == PressureUnits.INHG:
            return bytes("E7  02", "ascii")
        elif units == PressureUnits.MMHG:
            return bytes("E7  03", "ascii")
        elif units == PressureUnits.TORR:
            return bytes("E7  04", "ascii")

    @staticmethod
    def dispenseToggle():
        # command 2.2.27 in manual
        #
        # toggle the dispense - if the dispenser is set to 'steady mode', it will
        # begin dispensing, and another command will be needed to turn off the
        # dispenser
        return bytes("DI ", "ascii")

    @staticmethod
    def valueBytes(num, units):
        # given a pressure value and pressure units, return the bytes to be
        # sent to the ultimus to get the proper four digit byte representation.
        if units in (PressureUnits.PSI, PressureUnits.P_KPA, PressureUnits.INH2O, PressureUnits.MMHG, PressureUnits.TORR):
            val_str = "000" + str(float(num)) + "0"
            return bytes(val_str[val_str.find(".") - 3:val_str.find(".")] + val_str[val_str.find(".") + 1:val_str.find(".") + 2], "ascii")
        elif units in (PressureUnits.V_KPA, PressureUnits.INHG):
            val_str = "00" + str(float(num)) + "00"
            return bytes(val_str[val_str.find(".") - 2:val_str.find(".")] + val_str[val_str.find(".") + 1:val_str.find(".") + 3], "ascii")
        elif units in (PressureUnits.BAR):
            val_str = "0" + str(float(num)) + "000"
            return bytes(val_str[val_str.find(".") - 1:val_str.find(".")] + val_str[val_str.find(".") + 1:val_str.find(".") + 4], "ascii")
        else:
            return False

    @staticmethod
    def intToHexBytes(num):
        # turn an integer into hexadecimal represented in ascii character bytes
        num = num % 256  # ensuring will fit into two hex digits
        tens_digit = num // 16
        ones_digit = num % 16
        return bytes(hex(tens_digit)[2:].upper() + hex(ones_digit)[2:].upper(), "ascii")
