from .FisnarCSVParameterExtension import FisnarCSVParameterExtension
from .convert import convert, getExtrudersInGcode
from .autoupload import fisnarCommandsToCSVString

from UM.Mesh.MeshWriter import MeshWriter
from UM.Application import Application
from UM.Logger import Logger

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")


class FisnarCSVWriter(MeshWriter):
    def __init__(self):
        super().__init__(add_to_recent_files = False)  # don't want the spreadsheets to appear in recent files
        self._application = Application.getInstance()  # I dont need this. might be needed internally, so gonna leave it.

        # instantiating print surface parameters, to be updated by the FisnarCSVParameterExtension extension
        # these default values need to match the default values in the FisnarCSVParameterExtension class
        self.fisnar_x_min = None
        self.fisnar_x_max = None
        self.fisnar_y_min = None
        self.fisnar_y_max = None
        self.fisnar_z_max = None

        # extruder - output correlations
        self.num_extruders = None
        self.extruder_1_output = None
        self.extruder_2_output = None
        self.extruder_3_output = None
        self.extruder_4_output = None

    def getEnteredParameters(self):
        # get the user entered parameters in the Extension part of this plugin

        #  getting extension instance
        ext = FisnarCSVParameterExtension.getInstance()

        # getting fisnar coords
        self.fisnar_x_min = ext.fisnar_x_min
        self.fisnar_x_max = ext.fisnar_x_max
        self.fisnar_y_min = ext.fisnar_y_min
        self.fisnar_y_max = ext.fisnar_y_max
        self.fisnar_z_max = ext.fisnar_z_max
        Logger.log("i", "Build area updated in FisnarCSVWriter. New fisnar surface areas: (" + str(self.fisnar_x_min) + ", " + str(self.fisnar_x_max) + "), (" + str(self.fisnar_y_min) + ", " + str(self.fisnar_y_max) + "), (" + str(self.fisnar_z_max) + ")")  # test

        # getting extruder info
        self.num_extruders = ext.num_extruders
        self.extruder_1_output = ext.extruder_1_output
        self.extruder_2_output = ext.extruder_2_output
        self.extruder_3_output = ext.extruder_3_output
        self.extruder_4_output = ext.extruder_4_output
        Logger.log("i", "Extruders passed to FisnarCSVWriter. Num extruders: " + str(self.num_extruders) + ". Ext 1: " + str(self.extruder_1_output) + ", Ext 2: " + str(self.extruder_2_output) + ", Ext 3: " + str(self.extruder_3_output) + ", Ext 4: " + str(self.extruder_4_output))  # test


    def write(self, stream, nodes, mode=MeshWriter.OutputMode.TextMode):
        # getting updated extension parameters
        self.getEnteredParameters()

        # TODO: figure out a way to get the filename of the saved file, and add it as a parameter in the extension plugin

        # making sure the mode is text output
        if mode != MeshWriter.OutputMode.TextMode:
            Logger.log("e", "FisnarCSVWriter does not support non-text mode")
            self.setInformation(catalog.i18nc("@error:not supported", "FisnarCSVWriter does not support non-text mode"))
            return False  # signals error

        # making sure gcode_dict exists before calling it
        active_build_plate = Application.getInstance().getMultiBuildPlateModel().activeBuildPlate
        scene = Application.getInstance().getController().getScene()
        if not hasattr(scene, "gcode_dict"):  # if hasn't been sliced yet
            self.setInformation(catalog.i18nc("@warning:status", "Gcode must be prepared before exporting Fisnar CSV"))
            return False  # error

        gcode_dict = getattr(scene, "gcode_dict")
        gcode_list = gcode_dict.get(active_build_plate, None)  # returns None if not found
        if gcode_list is not None:  # gcode_list was found

            fisnar_commands = self.getFisnarCommands("".join([str(chunk) for chunk in gcode_list]))
            if fisnar_commands is False:  # error was caught in conversion (information will already be set.)
                return False  # error

            csv_string = fisnarCommandsToCSVString(fisnar_commands)
            stream.write(csv_string)  # writing to file
            FisnarCSVParameterExtension.getInstance().most_recent_fisnar_commands = fisnar_commands  # updating in extension class

            return True  # successful conversion
        else:  # gcode list not found, log error
            self.setInformation(catalog.i18nc("@warning:status", "Gcode must be prepared before exporting Fisnar CSV"))
            return False  # error


    def getFisnarCommands(self, gcode_str):
        # either returns a 2d list of fisnar commands or False if an error was caught
        # this is the function where error checking goes down

        extruders = getExtrudersInGcode(gcode_str)
        # Logger.log("i", "extruders in gcode: " + str(extruders))  # test

        for i in range(len(extruders)):  # validating extruders
            # Logger.log("i", "" + str(getattr(self, "extruder_" + str(i + 1) + "_output")))  # test
            if extruders[i]:  # T'i' appears in gcode, need to have ouput for the 'i + 1'th extruder
                if getattr(self, "extruder_" + str(i + 1) + "_output") is None:
                    self.setInformation(catalog.i18nc("@error:not supported", "Output for extruder " + str(i + 1) + " must be entered."))
                    return False

        return convert(gcode_str, [self.extruder_1_output, self.extruder_2_output, self.extruder_3_output, self.extruder_4_output],
                       [self.fisnar_x_min, self.fisnar_x_max, self.fisnar_y_min, self.fisnar_y_max, self.fisnar_z_max])
