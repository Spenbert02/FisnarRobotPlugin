from Machine import Machine

class UltimusV(Machine):
    # class representing the machine instance for the UltimusV fluid
    # dispenser

    # pressure units
    PSI = "PSI"
    BAR = "BAR"
    P_KPA = "P_KPA"

    # vacuum units  (kPa is the only unit used for both positive pressure and vacuum)
    V_KPA = "V_KPA"
    INH2O = "INH2O"
    INHG = "INHG"
    MMHG = "MMHG"
    TORR = "TORR"

    def __init__(self, port_name, *args):
        super().__init__(port_name, *args)

    def sendCommand(self, command_bytes):
        # send a command to the Ultimus V and return True if it was successful
        # or False if it was not

        number_bytes = UltimusV.intToHexBytes(len(command_bytes))
        bytes_to_send = UltimusV.ENQ + UltimusV.STX + number_bytes + command_bytes + UltimusV.checksum(number_bytes + command_bytes) + UltimusV.ETX + UltimusV.EOT
        self.writeBytes(bytes_to_send)

        ret_bytes = self.readUntil(UltimusV.ETX)  # bytes returned by the dispenser

        if len(ret_bytes) >= 6 and ret_bytes[4:6] == UltimusV.success():  # 'A0' recieved, command was success
            return True
        else:  # failure
            return False

    def sendFeedbackCommand(self, command_bytes):
        pass

    @staticmethod
    def success():
        # get the 'confirmation' byte code used by the Ultimus
        return bytes("A0", "ascii")

    @staticmethod
    def failure():
        # get the 'failure' byte code used by the Ultimus
        return bytes("A2", "ascii")

    @staticmethod
    def setPressure(pressure, units):
        # command 2.2.5 in manual
        #
        # set the pressure value of the dispenser - this DOES NOT turn the
        # dispenser on, like it does for the analogous vacuum command
        val_bytes = UltimusV.valueBytes(pressure, units)
        return bytes("PS  ", "ascii") + val_bytes

    @staticmethod
    def setVacuum(vacuum, units):
        # command 2.2.7 in manual
        #
        # set the vacuum to a certain pressure and TURN IT ON. This does not
        # just set the vacuum units, it sets the vacuum units and then turns
        # the vacuum on. To turn off the vacuum, set the vacuum value to 0
        val_bytes = UltimusV.valueBytes(vacuum, units)
        return bytes("VS  ", "ascii") + val_bytes

    @staticmethod
    def setPressureUnits(units):
        # command 2.2.12 in manual
        #
        # set the current pressure units for the dispenser
        if units == UltimusV.PSI:
            return bytes("E6  00", "ascii")
        elif units == UltimusV.BAR:
            return bytes("E6  01", "ascii")
        elif units == UltimusV.P_KPA:
            return bytes("E6  02", "ascii")

    @staticmethod
    def setVacuumUnits(units):
        # command 2.2.13 in manual
        #
        # set the vacuum units of the dispenser.
        if units == UltimusV.V_KPA:
            return bytes("E7  00", "ascii")
        elif units == UltimusV.INH2O:
            return bytes("E7  01", "ascii")
        elif units == UltimusV.INHG:
            return bytes("E7  02", "ascii")
        elif units == UltimusV.MMHG:
            return bytes("E7  03", "ascii")
        elif units == UltimusV.TORR:
            return bytes("E7  04", "ascii")

    @staticmethod
    def dispenseToggle():
        # command 2.2.27 in manual
        #
        # toggle the dispense - if the dispenser is set to 'steady mode', it will
        # begin dispensing, and another command will be needed to turn off the
        # dispenser
        return bytes("DI ", "ascii")

    @staticmethod
    def valueBytes(num, units):
        # given a pressure value and pressure units, return the bytes to be
        # sent to the ultimus to get the proper four digit byte representation.
        if units in (UltimusV.PSI, UltimusV.P_KPA, UltimusV.INH2O, UltimusV.MMHG, UltimusV.TORR):
            val_str = "000" + str(float(num)) + "0"
            return bytes(val_str[val_str.find(".") - 3:val_str.find(".")] + val_str[val_str.find(".") + 1:val_str.find(".") + 2], "ascii")
        elif units in (UltimusV.V_KPA, UltimusV.INHG):
            val_str = "00" + str(float(num)) + "00"
            return bytes(val_str[val_str.find(".") - 2:val_str.find(".")] + val_str[val_str.find(".") + 1:val_str.find(".") + 3], "ascii")
        elif units in (UltimusV.BAR):
            val_str = "0" + str(float(num)) + "000"
            return bytes(val_str[val_str.find(".") - 1:val_str.find(".")] + val_str[val_str.find(".") + 1:val_str.find(".") + 4], "ascii")
        else:
            return False

    @staticmethod
    def checksum(byte_array):
        # get the checksum (as a two byte array in forward order) from an
        # array of bytes
        antisum = 0
        for byte in byte_array:
            antisum -= byte
        antisum = antisum % 256

        return UltimusV.intToHexBytes(antisum)

    @staticmethod
    def intToHexBytes(num):
        # turn an integer into hexadecimal represented in ascii character bytes
        num = num % 256  # ensuring will fit into two hex digits
        tens_digit = num // 16
        ones_digit = num % 16
        return bytes(hex(tens_digit)[2:].upper() + hex(ones_digit)[2:].upper(), "ascii")
