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

        self._update_thread = threading.Thread(target=self._updateThread)
        self._update_thread.daemon = True  # constantly checks for serial connections until shutdown

        self._application = CuraApplication.getInstance()

    def start(self):
        Logger.log("i", "OutputDevicePlugin.start() called")
        self.getOutputDeviceManager().addOutputDevice(FisnarOutputDevice())

        # commenting for now, if anything this can be used to check for open serial ports and try to connect
        # self._check_updates = True
        # self._update_thread.start()

    def stop(self):
        Logger.log("i", "OutputDevicePlugin.stop() called")
        self.getOutputDeviceManager().getOutputDevice("fisnar_f5200n").close()
        self.getOutputDeviceManager().removeOutputDevice("fisnar_f5200n")

        # commenting for now, as in start()
        # self._check_updates = False  # stops while loop in _updateThread

    def _updateThread(self):
        while self._check_updates:
            container_stack = self._application.getGlobalContainerStack()
            Logger.log("d", str(container_stack))  # debugging
            if container_stack is None:
                time.sleep(5)
                continue

            # do stuff here every 5 seconds - ie, check for output devices
            # or something, eventually implement serial auto detect feature

    _instance = None

    @classmethod
    def getInstance(cls):
        return cls._instance
