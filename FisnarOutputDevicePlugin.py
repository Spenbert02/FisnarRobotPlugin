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
    # this class manages the FisnarOutputDevice instance which is used to control
    # the fisnar via RS232 printing and manual control (and pick and place). As
    # the FisnarOutputDevice class also holds an UltimusV instance for dispenser
    # control, this class also manages the UltimusV instance
    #
    # The UltimusV does not have it's own output device manager class because
    # by its own, it can't do anything with slicer output - it is merely a peripheral
    # used by the Fisnar. In order to execute pick and place manuevers, however, it must
    # be controled independently over RS232, so this class also manages that connection

    def __init__(self):
        super().__init__()

        if FisnarOutputDevicePlugin._instance is not None:
            Logger.log("e", "FisnarOutputDevicePlugin instantiated more than once")
        FisnarOutputDevicePlugin._instance = self

        self._check_updates = True  # for controlling while loop in _updateThread

        self._update_thread = threading.Thread(target=self._updateThread, name="FisnarRobotPlugin Serial Finder")
        self._update_thread.daemon = True  # constantly checks for serial connections until shutdown

        self._fisnar_port_name = None  # type: str, the name of the serial port from FisnarRobotExtension

        self._application = CuraApplication.getInstance()
        self._fre_instance = FisnarRobotExtension.getInstance()
        self._dispenser_manager = self._fre_instance.getDispenserManager()

    def start(self):
        # start checking for serial port updates
        Logger.log("i", "FisnarOutputDevicePlugin instance starting...")

        # creating FisnarOutputDevice
        self.getOutputDeviceManager().addOutputDevice(FisnarOutputDevice())

        # initializing com port name
        self._fisnar_port_name = self._fre_instance.com_port

        # start update thread to find open serial ports
        self._check_updates = True
        self._update_thread.start()

    def stop(self):
        # stop checking for serial port updates
        Logger.log("i", "FisnarOutputDevicePlugin instance stopping...")
        self._check_updates = False  # stops while loop in _updateThread
        self.getOutputDeviceManager().getOutputDevice("fisnar_f5200n").close()
        self.getOutputDeviceManager().removeOutputDevice("fisnar_f5200n")
        self._dispenser_manager.closeAll()

    def _updateThread(self):
        # try to connect to fisnar and dispenser serial port every 10 seconds if they aren't already connected
        while self._check_updates:
            time.sleep(10)
            self._fisnar_port_name = self._fre_instance.com_port
            self.getOutputDeviceManager().getOutputDevice("fisnar_f5200n").fisnarPortNameUpdated.emit()
            # TODO: put dispenser ports in manual control ui and emit signal here - basically the above line but for the dispensers

            if not self.getOutputDeviceManager().getOutputDevice("fisnar_f5200n").isConnected():  # if fisnar port not connected, try to.
                if self._fisnar_port_name not in (None, "None"):
                    self.getOutputDeviceManager().getOutputDevice("fisnar_f5200n").connect(self._fisnar_port_name)
                    if self.getOutputDeviceManager().getOutputDevice("fisnar_f5200n").isConnected():
                        fis_msg = Message(text = catalog.i18nc("@message", "Fisnar F5200N successfully connected via: " + str(self._fisnar_port_name)),
                                          title = catalog.i18nc("@message", "Connection Status Update"))
                        fis_msg.show()

            for dispenser in self._dispenser_manager.getDispensers():
                if not dispenser.isConnected():
                    if dispenser.getComPort() not in (None, "None"):
                        dispenser.connect()
                        if dispenser.isConnected():
                            disp_msg = Message(text = catalog.i18nc("@message", f"UltimusV dispenser '{dispenser.name}' successfully connected via: {dispenser.getComPort()}"),
                                               title = catalog.i18nc("@message", "Connection Status Update"))
                            disp_msg.show()

    _instance = None

    @classmethod
    def getInstance(cls):
        return cls._instance
