import sys
import time
import keyboard

from Fisnar import Fisnar
from UltimusV import UltimusV
from UM.Logger import Logger


class PickAndPlaceGenerator:
    # static class for getting pick and place commands from ui parameters

    def __init__(self):  # should never be called
        Logger.log("w", "instance created of static class 'PickAndPlaceGenerator'")

    @staticmethod
    def execute(p1, p2, xy_speed, z_speed, pick_dwell, place_dwell, vacuum_pressure, vacuum_units):
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
            ["f", Fisnar.SP(z_speed)],
            ["f", Fisnar.HZ()],
            ["f", Fisnar.SP(xy_speed)],
            ["f", Fisnar.HX()],
            ["f", Fisnar.HY()],
            ["f", Fisnar.VA(p1[0], p1[1], 0)],
            ["f", Fisnar.ID()],
            ["f", Fisnar.SP(z_speed)],
            ["f", Fisnar.VA(p1[0], p1[1], p1[2])],
            ["f", Fisnar.ID()],
            ["d", UltimusV.setVacuumPressure(vacuum_pressure, vacuum_units)],
            ["sleep", pick_dwell],  # signals to wait for 'pick dwell' seconds
            ["f", Fisnar.VA(p1[0], p1[1], 0)],
            ["f", Fisnar.ID()],
            ["f", Fisnar.SP(xy_speed)],
            ["f", Fisnar.VA(p2[0], p2[1], 0)],
            ["f", Fisnar.ID()],
            ["f", Fisnar.SP(z_speed)],
            ["f", Fisnar.VA(p2[0], p2[1], p2[2])],
            ["f", Fisnar.ID()],
            ["d", UltimusV.setVacuum(0, vacuum_units)],
            ["sleep", place_dwell],
            ["f", Fisnar.VA(p2[0], p2[1], 0)],
            ["f", Fisnar.ID()],
            ["f", Fisnar.SP(z_speed)],
            ["f", Fisnar.HZ()],
            ["f", Fisnar.SP(xy_speed)],
            ["f", Fisnar.HX()],
            ["f", Fisnar.HY()]
        ]

        return commands
