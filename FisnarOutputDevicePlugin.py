import threading
import time

from cura.CuraApplication import CuraApplication
from UM.Logger import Logger
from UM.Message import Message
from UM.OutputDevice.OutputDevicePlugin import OutputDevicePlugin
from .FisnarOutputDevice import FisnarOutputDevice
from .FisnarRobotExtension import FisnarRobotExtension

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")


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

        self._fisnar_port_name = None  # type: str, the name of the serial port from FisnarRobotExtension
        self._dispenser_port_name = None

        self._application = CuraApplication.getInstance()


    def start(self):
        Logger.log("i", "OutputDevicePlugin.start() called")

        # creating FisnarOutputDevice
        self.getOutputDeviceManager().addOutputDevice(FisnarOutputDevice())

        # initializing com port name
        self._fisnar_port_name = FisnarRobotExtension.getInstance().com_port
        self._dispenser_port_name = FisnarRobotExtension.getInstance().dispenser_com_port

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
        # TEMP - right now this ignores any updates in com port after it connects. eventually, some sort of behavior should be implemented
            # actually - the current behavior might be good. after it connects, then it will stay connected
        while self._check_updates:
            time.sleep(10)
            self._fisnar_port_name = FisnarRobotExtension.getInstance().com_port
            self._dispenser_port_name = FisnarRobotExtension.getInstance().dispenser_com_port

            self.getOutputDeviceManager().getOutputDevice("fisnar_f5200n").fisnarPortNameUpdated.emit()

            # Logger.log("d", "current serial port: " + str(self._fisnar_port_name))

            if not self.getOutputDeviceManager().getOutputDevice("fisnar_f5200n").isConnected():  # if fisnar port not connected, try to.
                if self._fisnar_port_name not in (None, "None"):
                    self.getOutputDeviceManager().getOutputDevice("fisnar_f5200n").connect(self._fisnar_port_name)
                    if self.getOutputDeviceManager().getOutputDevice("fisnar_f5200n").isConnected():
                        fis_msg = Message(text = catalog.i18nc("@message", "Fisnar F5200N successfully connected via: " + str(self._fisnar_port_name)),
                                          title = catalog.i18nc("@message", "Connection Status Update"))
                        fis_msg.show()

            if not self.getOutputDeviceManager().getOutputDevice("fisnar_f5200n").dispenser.isConnected():  # if ultimus port is not connected, try to
                if self._dispenser_port_name not in (None, "None"):
                    self.getOutputDeviceManager().getOutputDevice("fisnar_f5200n").dispenser.connect(self._dispenser_port_name)
                    if self.getOutputDeviceManager().getOutputDevice("fisnar_f5200n").dispenser.isConnected():
                        disp_msg = Message(text = catalog.i18nc("@message", "UltimusV dispenser successfully connected via: " + str(self._dispenser_port_name)),
                                           title = catalog.i18nc("@message", "Connection Status Update"))
                        disp_msg.show()

    _instance = None

    @classmethod
    def getInstance(cls):
        return cls._instance
