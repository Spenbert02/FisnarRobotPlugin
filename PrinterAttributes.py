from UM.Logger import Logger


class PrintSurface:
    # simple class representing the print area.

    DEFAULT_X_MIN = 0.0
    DEFAULT_X_MAX = 200.0
    DEFAULT_Y_MIN = 0.0
    DEFAULT_Y_MAX = 200.0
    DEFAULT_Z_MAX = 150.0

    def __init__(self, x_min, x_max, y_min, y_max, z_max):
        self.x_min = x_min
        self.x_max = x_max
        self.y_min = y_min
        self.y_max = y_max
        self.z_max = z_max

    def updateFromTuple(self, coords):
        self.x_min = coords[0]
        self.x_max = coords[1]
        self.y_min = coords[2]
        self.y_max = coords[3]
        self.z_max = coords[4]

    def setXMin(self, x_min):
        self.x_min = float(x_min)

    def setXMax(self, x_max):
        self.x_max = float(x_max)

    def setYMin(self, y_min):
        self.y_min = float(y_min)

    def setYMax(self, y_max):
        self.y_max = float(y_max)

    def setZMax(self, z_max):
        self.z_max = float(z_max)

    def getAsTuple(self):
        return [self.x_min, self.x_max, self.y_min, self.y_max, self.z_max]

    def getXMin(self):
        return float(self.x_min)

    def getXMax(self):
        return float(self.x_max)

    def getYMin(self):
        return float(self.y_min)

    def getYMax(self):
        return float(self.y_max)

    def getZMax(self):
        return float(self.z_max)

    def getDebugString(self):
        return "\nx_min: " + str(self.x_min) + ", " + str(type(self.x_min)) + "\nx_max: " + str(self.x_max) + ", " + str(type(self.x_max)) + "\ny_min: " + str(self.y_min) + ", " + str(type(self.y_min)) + "\ny_max: " + str(self.y_max) + ", " + str(type(self.y_max)) + "\nz_max: " + str(self.z_max) + ", " + str(type(self.z_max))


class ExtruderArray:
    # class representing an array of extruders (usually 4) that correlates
    # an extruder to an output

    def __init__(self, num_extruders):
        self.outputs = []
        for i in range(num_extruders):
            self.outputs.append(None)

    def updateFromTuple(self, ext_outs):
        for i in range(len(ext_outs)):
            self.setOutput(i + 1, ext_outs[i])

    def setOutput(self, extruder, output):
        if output is None or output == "None" or int(output) == 0:
            self.outputs[extruder - 1] = None
        else:
            self.outputs[extruder - 1] = int(output)

    def getAsTuple(self):
        ret_tuple = []
        for output in self.outputs:
            if output is None:
                ret_tuple.append(None)
            else:
                ret_tuple.append(int(output))
        return ret_tuple

    def getOutput(self, extruder):
        return self.outputs[extruder - 1]

    def getOutputAsInt(self, extruder):
        Logger.log("d", "in PrinterAttributes, self.outputs: " + str(self.outputs))
        ret_output = self.outputs[extruder - 1]
        if ret_output is None:
            return 0
        else:
            return ret_output

    def getDebugString(self):
        return "\nextruder 1: " + str(self.outputs[0]) + "\nextruder 2: " + str(self.outputs[1]) + "\nextruder 3: " + str(self.outputs[2]) + "\nextruder 4: " + str(self.outputs[3])


if __name__ == "__main__":
    ea = ExtruderArray(4)
    ea.updateFromTuple([2, 0, 0, 0])
    # print(ea.outputs)
    for i in range(1, 5):
        print(ea.getOutputAsInt(i))
