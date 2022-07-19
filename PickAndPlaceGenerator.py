from .FisnarCommands import FisnarCommands
from .UltimusV import UltimusV
from UM.Logger import Logger


class PickAndPlaceGenerator:
    # static class for getting pick and place commands from ui parameters

    def __init__(self):  # should never be called
        Logger.log("w", "instance created of static class 'PickAndPlaceGenerator'")

    @staticmethod
    def getCommands(p1, p2, xy_speed, z_speed, pick_dwell, place_dwell, vacuum_pressure, vacuum_units):
        # returns a list of pick and place commands from the given parameters, or False
        # if any of the parameters are invalid

        for param in (p1, p2):
            if not isinstance(param, (list, tuple)):
                return False
        for param in (xy_speed, z_speed, pick_dwell, place_dwell, vacuum_pressure):
            if not isinstance(param, (int, float)):
                return False
        if vacuum_units not in (0, 1, 2, 3, 4):  # vacuum_units is an enumeration
            return False

        commands = [
            ["d", UltimusV.setVacuumUnits(vacuum_units)],  # set dispenser vacuum units
            ["f", FisnarCommands.SP(z_speed)],
            ["f", FisnarCommands.HZ()],
            ["f", FisnarCommands.SP(xy_speed)],
            ["f", FisnarCommands.HX()],
            ["f", FisnarCommands.HY()],
            ["f", FisnarCommands.VA(p1[0], p1[1], 0)],
            ["f", FisnarCommands.ID()],
            ["f", FisnarCommands.SP(z_speed)],
            ["f", FisnarCommands.VA(p1[0], p1[1], p1[2])],
            ["f", FisnarCommands.ID()],
            ["d", UltimusV.setVacuum(vacuum_pressure, vacuum_units)],
            ["sleep", pick_dwell],  # signals to wait for 'pick dwell' seconds
            ["f", FisnarCommands.VA(p1[0], p1[1], 0)],
            ["f", FisnarCommands.ID()],
            ["f", FisnarCommands.SP(xy_speed)],
            ["f", FisnarCommands.VA(p2[0], p2[1], 0)],
            ["f", FisnarCommands.ID()],
            ["f", FisnarCommands.SP(z_speed)],
            ["f", FisnarCommands.VA(p2[0], p2[1], p2[2])],
            ["f", FisnarCommands.ID()],
            ["d", UltimusV.setVacuum(0, vacuum_units)],
            ["sleep", place_dwell],
            ["f", FisnarCommands.VA(p2[0], p2[1], 0)],
            ["f", FisnarCommands.ID()],
            ["f", FisnarCommands.SP(z_speed)],
            ["f", FisnarCommands.HZ()],
            ["f", FisnarCommands.SP(xy_speed)],
            ["f", FisnarCommands.HX()],
            ["f", FisnarCommands.HY()]
        ]

        return commands
