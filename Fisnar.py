class Fisnar:
    # class representing physical Fisnar machine, with functions representing
    # different RS232 commands

    def __init__(self):
        pass

    @staticmethod
    def initializer():
        return bytes.fromhex("f0 f0 f2")

    @staticmethod
    def finalizer():
        return bytes.fromhex("df 00")

    @staticmethod
    def okConfirmation():
        return bytes("ok!\r")

    @staticmethod
    def OU(port, status):
        return bytes("OU " + str(port) + ", " + str(status) + "\r", "ascii")

    @staticmethod
    def SP(speed):
        return bytes("SP " + str(round(float(speed), 3)) + "\r", "ascii")

    @staticmethod
    def PX():
        return bytes("PX\r", "ascii")

    @staticmethod
    def PY():
        return bytes("PY\r", "ascii")

    @staticmethod
    def PZ():
        return bytes("PZ\r", "ascii")

    @staticmethod
    def VA(x, y, z):
        return bytes("VA " + str(round(float(x), 3)) + ", " + str(round(float(y), 3)) + ", " + str(round(float(z), 3)) + "\r", "ascii")

    @staticmethod
    def VX(x):
        return bytes("VX " + str(round(float(x), 3)) + "\r", "ascii")

    @staticmethod
    def VY(y):
        return bytes("VY " + str(round(float(y), 3)) + "\r", "ascii")

    @staticmethod
    def VZ(z):
        return bytes("VZ " + str(round(float(z), 3)) + "\r", "ascii")

    @staticmethod
    def HM():
        return bytes("HM\r", "ascii")

    @staticmethod
    def HX():
        return bytes("HX\r", "ascii")

    @staticmethod
    def HY():
        return bytes("HY\r", "ascii")

    @staticmethod
    def HZ():
        return bytes("HZ\r", "ascii")

    @staticmethod
    def ID():
        return bytes("ID\r", "ascii")

    @staticmethod
    def expectedReturn(byte_array):
        return byte_array + bytes("\n", "ascii") + Fisnar.okConfirmation() + bytes("\n", "ascii")

    @staticmethod
    def feedbackCommands():
        return (self.PX(), self.PY(), self.PZ())
