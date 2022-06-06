from .FisnarCSVParameterExtension import FisnarCSVParameterExtension
from .Converter import Converter
from .AutoUploader import AutoUploader

from UM.Mesh.MeshWriter import MeshWriter
from UM.Application import Application
from UM.Logger import Logger

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")


class FisnarCSVWriter(MeshWriter):
    def __init__(self):
        super().__init__(add_to_recent_files = False)  # don't want the spreadsheets to appear in recent files
        self._application = Application.getInstance()  # I dont need this. might be needed internally, so gonna leave it.

        self.converter = Converter()


    def getEnteredParameters(self):
        # get the user entered parameters in the Extension part of this plugin
        # and update the Converter object

        #  getting extension instance
        ext = FisnarCSVParameterExtension.getInstance()

        # updating conversion mode
        self.converter.conversion_mode = ext.conversion_mode

        # updating fisnar coords
        self.converter.setPrintSurface(ext.fisnar_x_min,
                                       ext.fisnar_x_max,
                                       ext.fisnar_y_min,
                                       ext.fisnar_y_max,
                                       ext.fisnar_z_max)
        Logger.log("i", "Build area updated in FisnarCSVWriter. New print surface: " + str(self.converter.getPrintSurface()))  # test

        # updating extruder correlations
        self.converter.setExtruderOutputs(ext.extruder_1_output,
                                          ext.extruder_2_output,
                                          ext.extruder_3_output,
                                          ext.extruder_4_output)
        Logger.log("i", "Extruder outputs passed to FisnarCSVWriter. New outputs: " + str(self.converter.getExtruderOutputs()))  # test


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

            # setting converter gcode and attempting to convert
            self.converter.setGcode("".join([str(chunk) for chunk in gcode_list]))
            fisnar_commands = self.converter.getFisnarCommands()

            if fisnar_commands is False:  # error was caught in conversion, get error info from converter object
                self.setInformation(catalog.i18nc("@warning:status", self.converter.getInformation()))
                return False  # error

            csv_string = AutoUploader.fisnarCommandsToCSVString(fisnar_commands)
            stream.write(csv_string)  # writing to file
            FisnarCSVParameterExtension.getInstance().most_recent_fisnar_commands = fisnar_commands  # updating in extension class

            return True  # successful conversion
        else:  # gcode list not found, log error
            self.setInformation(catalog.i18nc("@warning:status", "Gcode must be prepared before exporting Fisnar CSV"))
            return False  # error
