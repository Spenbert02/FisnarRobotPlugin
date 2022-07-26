from cura.PrinterOutput.Peripheral import Peripheral
from PyQt6.QtCore import QTimer, pyqtSignal
from UM.Message import Message

from .UltimusV import UltimusV, PressureUnits


class DispenserManager:
    # a class that holds multiple UltimusV objects that has methods for
    # getting information about their status

    dispenserConnectionStatesUpdated = pyqtSignal()

    def __init__(self):
        if DispenserManager._instance is not None:
            Logger.log("e", "tried to create singleton 'DispenserManager' more than once")
        else:
            DispenserManager._instance = self

        self._dispensers = []

        self._confirm_connection_timer = QTimer()
        self._confirm_connection_timer.setInterval(5000)
        self._confirm_connection_timer.timeout.connect(self._onConfirmConnectionTimeout)

    def addDispenser(self, dispenser):
        if dispenser not in self._dispensers and isinstance(dispenser, testDispenser):
            self._dispensers.append(dispenser)

        if not self._confirm_connection_timer.isActive() and self._dispensers != []:
            self._confirm_connection_timer.start()

    def _onConfirmConnectionTimeout(self):
        for dispenser in self._dispensers:
            if dispenser.isConnected() and not dispenser.busy:
                still_connected = dispenser.sendCommand(UltimusV.setVacuum(0.0, PressureUnits.V_KPA))
                if not still_connected:
                    Logger.log("w", str(dispenser.name) + " appears to be unresponsive, attempting to confirm connection status")
                    msg = Message(text = catalog.i18nc("@message", str(dispenser.name) + " is unresponsive, will attempt to regain connection..."),
                                  title = catalog.i18nc("@message", "Unresponsive Peripheral"))
                    msg.show()
                    dispenser.close()
                    self.dispenserConnectionStatesUpdated.emit()

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

    def getDispenser(self, dispenser_name):
        # get a dispenser by name
        for i in range(len(self._dispensers)):
            if self._dispensers[i].name == dispenser_name:
                return self._dispensers[i]
        return None

    _instance = None

    @classmethod
    def getInstance(cls):
        return cls._instance
