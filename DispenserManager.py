import time
from cura.PrinterOutput.Peripheral import Peripheral
from PyQt6.QtCore import QTimer
from threading import Event, Thread
from UM.Logger import Logger
from UM.Message import Message
from UM.Signal import Signal
from .UltimusV import UltimusV, PressureUnits

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")


class DispenserManager:
    # a class that holds multiple UltimusV objects that has methods for
    # getting information about their status

    dispenserConnectionStatesUpdated = Signal()

    def __init__(self):
        if DispenserManager._instance is not None:
            Logger.log("e", "tried to create singleton 'DispenserManager' more than once")
        else:
            DispenserManager._instance = self

        self._dispensers = []
        self._pick_place_dispenser_name = None

        self.trigger_fisnar_loop = Event()  # set when done sending, in order to trigger ok loop in fisnar _update

        self.busy = False  # true if any dispensers are busy, false otherwise

        self._confirm_connection_thread = Thread(target=self._update, daemon=True, name="DispenserManager Connection Confirmation")

    def _update(self):
        Logger.log("i", f"DispenserManager connection confirm thread started")
        while len(self._dispensers) > 0:
            for dispenser in self._dispensers:
                if dispenser.isConnected() and dispenser.available.is_set() and not dispenser.busy:
                    still_connected = dispenser.testConnection()
                    if not still_connected:
                        Logger.log("w", str(dispenser.display_name) + " appears to be unresponsive, attempting to confirm connection status")
                        msg = Message(text = catalog.i18nc("@message", str(dispenser.display_name) + " is unresponsive, will attempt to regain connection..."),
                                      title = catalog.i18nc("@message", "Unresponsive Peripheral"))
                        msg.show()
                        dispenser.close()
                        self.dispenserConnectionStatesUpdated.emit()
            time.sleep(5)

    def _onBusyStateUpdated(self):
        # update internal busy state
        for dispenser in self._dispensers:
            if dispenser.isBusy():
                self.busy = True
                return
        self.busy = False

    def _onSuccessfulCommandSend(self):
        self.trigger_fisnar_loop.set()

    def _onDispenserConnectionStateUpdated(self):
        self.dispenserConnectionStatesUpdated.emit()

    def addDispenser(self, dispenser):
        if dispenser not in self._dispensers and isinstance(dispenser, UltimusV):
            self._dispensers.append(dispenser)
            if len(self._dispensers) == 1:
                self._confirm_connection_thread.start()
            dispenser.connectionStateUpdated.connect(self._onDispenserConnectionStateUpdated)
            dispenser.successfulCommandSend.connect(self._onSuccessfulCommandSend)
            dispenser.busyStateUpdated.connect(self._onBusyStateUpdated)

        if self._pick_place_dispenser_name is None:  # defaulting pick and place dispenser
            self._pick_place_dispenser_name = dispenser.name

    def getPortNameDict(self):
        ret_dict = {}
        for dispenser in self._dispensers:
            ret_dict[dispenser.name] = None if dispenser.getComPort() in (None, "None") else dispenser.getComPort()
        Logger.log("d", "********** " + str(ret_dict))
        return ret_dict

    def isConnected(self, dispenser_name):
        # determine if a dispenser with a given name is connected
        for dispenser in self._dispensers:
            if dispenser.name == dispenser_name:
                return dispenser.isConnected()
        Logger.log("w", "attempted to access non-existent dispenser " + dispenser_name)
        return None  # no such dispenser exists

    def connect(self, dispenser_name, com_port):
        for dispenser in self._dispensers:
            if dispenser.name == dispenser_name:
                dispenser.connect(com_port)

    def closeAll(self):
        for dispenser in self._dispensers:
            dispenser.close()

    def getDispenser(self, dispenser_name):
        # get a dispenser by name
        for i in range(len(self._dispensers)):
            if self._dispensers[i].name == dispenser_name:
                return self._dispensers[i]
        return None

    # TODO: add infrastructure for tracking active dispensers in dispensermanager and add method for getting the active dispenser

    def getPickPlaceDispenser(self):
        if self._pick_place_dispenser_name is None:
            return None
        for dispenser in self._dispensers:
            if dispenser.name == self._pick_place_dispenser_name:
                return dispenser
        Logger.log("w", "pick and place dispenser " + str(self._pick_place_dispenser_name) + " not found in list of dispensers")
        return None

    def getPickPlaceDispenserName(self):
        return self._pick_place_dispenser_name

    def setPickPlaceDispenser(self, name):
        if name == "None":
            name = None
        self._pick_place_dispenser_name = name

    def getDispensers(self):
        return self._dispensers

    def getConnectedDispensers(self):
        ret_dispensers = []
        for dispenser in self._dispensers:
            if dispenser.isConnected():
                ret_dispensers.append(dispenser)
        return ret_dispensers

    _instance = None

    @classmethod
    def getInstance(cls):
        return cls._instance
