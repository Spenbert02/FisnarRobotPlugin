import threading
import time

from cura.CuraApplication import CuraApplication
from UM.Logger import Logger
from UM.OutputDevice.OutputDevicePlugin import OutputDevicePlugin
from .FisnarOutputDevice import FisnarOutputDevice


class FisnarOutputDevicePlugin(OutputDevicePlugin):

    def __init__(self):
        super().__init__()

        if FisnarOutputDevicePlugin._instance is not None:
            Logger.log("e", "FisnarOutputDevicePlugin instantiated more than once")
        FisnarOutputDevicePlugin._instance = self

        self._check_updates = True  # for controlling while loop in _updateThread

        self._update_thread = threading.Thread(target=self._updateThread, name="FisnarRobotPlugin Serial Finder")
        self._update_thread.daemon = True  # constantly checks for serial connections until shutdown

        self._application = CuraApplication.getInstance()

    def start(self):
        Logger.log("i", "OutputDevicePlugin.start() called")
        self.getOutputDeviceManager().addOutputDevice(FisnarOutputDevice())

        # start update thread to find open serial ports
        self._check_updates = True
        self._update_thread.start()

    def stop(self):
        Logger.log("i", "OutputDevicePlugin.stop() called")
        self.getOutputDeviceManager().getOutputDevice("fisnar_f5200n").close()
        self.getOutputDeviceManager().removeOutputDevice("fisnar_f5200n")

        # stop checking for serial port updates
        self._check_updates = False  # stops while loop in _updateThread

    def _updateThread(self):
        # try to connect to serial port every 5 seconds, unless port is
        # already connected to
        while self._check_updates:
            if self.getOutputDeviceManager().getOutputDevice("fisnar_f5200n").isConnected():
                pass
            else:  # not connected, so try
                self.getOutputDeviceManager().getOutputDevice("fisnar_f5200n").connect()
            time.sleep(5)

    _instance = None

    @classmethod
    def getInstance(cls):
        return cls._instance
