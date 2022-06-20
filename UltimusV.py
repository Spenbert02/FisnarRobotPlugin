from .Machine import Machine

class UltimusV(Machine):
    # class representing the machine instance for the UltimusV fluid
    # dispenser

    PSI = "PSI"
    BAR = "BAR"
    KPA = "KPA"

    def __init__(self, port_name, *args):
        super().__init__(port_name, *args)

    @staticmethod
    def success():
        return bytes("A0", "ascii")

    @staticmethod
    def failure():
        return bytes("A2", "ascii")

    @staticmethod
    def dispenseToggle():
        return bytes("DI ", "ascii")

    @staticmethod
    def setPressure(pressure, units):
        val_bytes = UltimusV.valueBytes(pressure, units)
        return bytes("PS  ", "ascii") + val_bytes

    @staticmethod
    def setVacuum(vacuum, units):
        val_bytes = UltimusV.valueBytes(vacuum, units)
        return bytes("VS  ", "ascii") + val_bytes

    @staticmethod
    def valueBytes(num, units):
        if units == UltimusV.PSI:
            val_str = "00" + str(float(num)) + "00"
            return bytes(val_str[val_str.find(".") - 2:val_str.find(".")] + val_str[val_str.find(".") + 1:val_str.find(".") + 3], "ascii")

    @staticmethod
    def checksum(byte_array):
        # get the checksum (as a two byte array in forward order) from an
        # array of bytes
        antisum = 0
        for byte in byte_array:
            antisum -= byte
        antisum = antisum % 256

        tens_digit = antisum // 16
        ones_digit = antisum - (tens_digit * 16)

        return bytes(hex(tens_digit)[2:].upper() + hex(ones_digit)[2:].upper(), "ascii")


if __name__ == "__main__":
    print(UltimusV.setPressure(20, UltimusV.PSI))
