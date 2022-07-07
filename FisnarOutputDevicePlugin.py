import threading
import time

from cura.CuraApplication import CuraApplication
from UM.Logger import Logger
from UM.OutputDevice.OutputDevicePlugin import OutputDevicePlugin
from .FisnarOutputDevice import FisnarOutputDevice
from .FisnarRobotExtension import FisnarRobotExtension


class FisnarOutputDevicePlugin(OutputDevicePlugin):
    # this class only manages ONE output device - the Fisnar F5200N. It doesn't
    # check serial ports regularly (like USBPrinterOutputDevice) - rather, it
    # takes the serial port that the user has entered in FisnarRobotExtension,
    # and it continually tries to connect to it until it successfully does so.

    def __init__(self):
        super().__init__()

        if FisnarOutputDevicePlugin._instance is not None:
            Logger.log("e", "FisnarOutputDevicePlugin instantiated more than once")
        FisnarOutputDevicePlugin._instance = self

        self._check_updates = True  # for controlling while loop in _updateThread

        self._update_thread = threading.Thread(target=self._updateThread, name="FisnarRobotPlugin Serial Finder")
        self._update_thread.daemon = True  # constantly checks for serial connections until shutdown

        self._serial_port_name = None  # type: str, the name of the serial port from FisnarRobotExtension

        self._application = CuraApplication.getInstance()

    def _onUpdatedSerialPort(self):
        self._serial_port_name = str(FisnarRobotExtension.getInstance().getComPortName())
        self.getOutputDeviceManager().getOutputDevice("fisnar_f5200n").serialPortNameUpdated.emit(self._serial_port_name)

    def start(self):
        Logger.log("i", "OutputDevicePlugin.start() called")

        # creating FisnarOutputDevice
        self.getOutputDeviceManager().addOutputDevice(FisnarOutputDevice())

        # signal to update internal com_port storage
        FisnarRobotExtension.getInstance().comPortNameUpdated.connect(self._onUpdatedSerialPort)

        # start update thread to find open serial ports
        self._check_updates = True
        self._update_thread.start()

    def stop(self):
        # stop checking for serial port updates
        self._check_updates = False  # stops while loop in _updateThread

        Logger.log("i", "OutputDevicePlugin.stop() called")
        self.getOutputDeviceManager().getOutputDevice("fisnar_f5200n").close()
        self.getOutputDeviceManager().removeOutputDevice("fisnar_f5200n")

    def _updateThread(self):
        # try to connect to serial port every 5 seconds, unless port is
        # already connected to
        while self._check_updates:
            if self.getOutputDeviceManager().getOutputDevice("fisnar_f5200n").isConnected() or self._serial_port_name in (None, "None"):
                pass
            else:  # not connected, so try
                Logger.log("d", "serial_port_name: " + str(self._serial_port_name))
                self.getOutputDeviceManager().getOutputDevice("fisnar_f5200n").connect(self._serial_port_name)
            time.sleep(5)

    _instance = None

    @classmethod
    def getInstance(cls):
        return cls._instance
