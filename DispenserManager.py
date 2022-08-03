from cura.PrinterOutput.Peripheral import Peripheral
from PyQt6.QtCore import QTimer
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

        self.trigger_fisnar_loop = False  # sent to true when a dispenser sends a command, in order to keep the fisnar 'ok!' loop going
        self.busy = False  # true if any dispensers are busy, false otherwise

        self._confirm_connection_timer = QTimer()
        self._confirm_connection_timer.setInterval(5000)
        self._confirm_connection_timer.timeout.connect(self._onConfirmConnectionTimeout)

    def _onBusyStateUpdated(self):
        # update internal busy state
        for dispenser in self._dispensers:
            if dispenser.isBusy():
                self.busy = True
                return
        self.busy = False

    def _onSuccessfulCommandSend(self):
        self.trigger_fisnar_loop = True

    def _onDispenserConnectionStateUpdated(self):
        self.dispenserConnectionStatesUpdated.emit()

    def _onConfirmConnectionTimeout(self):
        pass
        # for dispenser in self._dispensers:
        #     if dispenser.isConnected() and not dispenser.busy:
        #         still_connected = dispenser.sendCommand(UltimusV.setVacuum(0.0, PressureUnits.V_KPA))
        #         if not still_connected:
        #             Logger.log("w", str(dispenser.name) + " appears to be unresponsive, attempting to confirm connection status")
        #             msg = Message(text = catalog.i18nc("@message", str(dispenser.name) + " is unresponsive, will attempt to regain connection..."),
        #                           title = catalog.i18nc("@message", "Unresponsive Peripheral"))
        #             msg.show()
        #             dispenser.close()
        #             self.dispenserConnectionStatesUpdated.emit()

    def addDispenser(self, dispenser):
        if dispenser not in self._dispensers and isinstance(dispenser, UltimusV):
            self._dispensers.append(dispenser)
            dispenser.connectionStateUpdated.connect(self._onDispenserConnectionStateUpdated)
            dispenser.successfulCommandSend.connect(self._onSuccessfulCommandSend)
            dispenser.busyStateUpdated.connect(self._onBusyStateUpdated)

        if not self._confirm_connection_timer.isActive() and self._dispensers != []:  # start confirm connection timer if not going already
            self._confirm_connection_timer.start()

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
