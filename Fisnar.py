from .Machine import Machine


class Fisnar(Machine):
    # class representing physical Fisnar machine, with functions representing
    # different RS232 commands

    def __init__(self, port_name, *args):
        super().__init__(port_name, *args)

    def sendCommand(self, command_bytes):
        if command_bytes == Fisnar.initializer():  # initializer bytes
            self.writeBytes(Fisnar.initializer())
            confirmation = self.readLine()
            if Fisnar.expectedReturn(Fisnar.initializer()) in confirmation:  # if proper confirmation bytes recieved
                return True
            else:
                self.setInformation("initializer confirmation failed. Bytes recieved: " + str(confirmation))
                return False
        elif command_bytes == Fisnar.finalizer():  # finalizer bytes, no return bytes expected so just send and return True
            self.writeBytes(Fisnar.finalizer())
            return True
        else:  # any non-feedback command besides initial and final ones
            self.writeBytes(command_bytes)
            confirmation = self.readLine() + self.readLine()  # read two lines - one for the repeat bytes, one for the 'ok!' confirmation

            if confirmation == Fisnar.expectedReturn(command_bytes):
                return True
            else:
                self.setInformation("command failed to send. Bytes sent: " + str(command_bytes) + ". Bytes recieved: " + str(confirmation))

    def sendFeedbackCommand(self, command_bytes):
        self.writeBytes(command_bytes)
        confirmation = self.readLine()  # to recieve repeat confirm

        ret_val = float(self.readLine()[:-1])  # return value w/out \'n' char

        confirmation += self.readLine()  # reading 'ok!' confirm
        if confirmation == Fisnar.expectedReturn(command_bytes):
            return ret_val
        else:
            return False

    @staticmethod
    def initializer():
        return bytes.fromhex("f0 f0 f2")

    @staticmethod
    def finalizer():
        return bytes.fromhex("df 00")

    @staticmethod
    def okConfirmation():
        return bytes("ok!\r", "ascii")

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
    def MXR(x):
        return bytes("MXR (0" + str(round(float(x), 3)) + ")\r", "ascii")

    @staticmethod
    def MYR(y):
        return bytes("MYR (0" + str(round(float(y), 3)) + ")\r", "ascii")

    @staticmethod
    def MZR(z):
        return bytes("MZR (0" + str(round(float(z), 3)) + ")\r", "ascii")

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
    def isFeedback(byte_array):
        # determine if a given byte array recieved from the fisnar is a
        # feedback command
        if len(byte_array) <= 2:
            return False

        try:
            temp = float(byte_array[:-2])
        except:
            return False

        return True

    @staticmethod
    def expectedReturn(byte_array):
        # get the expected bytes from the fisnar after sending the given bytes.
        # for feedback commands, the feedback value line is excluded
        if byte_array == Fisnar.initializer():
            return bytes.fromhex("f0") + bytes("<< BASIC BIOS 2.2 >>\r\n", "ascii")
        elif byte_array == Fisnar.finalizer():
            return bytes()
        else:
            return byte_array + bytes("\n", "ascii") + Fisnar.okConfirmation() + bytes("\n", "ascii")

    @staticmethod
    def feedbackCommands():
        return (Fisnar.PX(), Fisnar.PY(), Fisnar.PZ())
