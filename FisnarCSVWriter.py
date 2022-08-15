from .FisnarRobotExtension import FisnarRobotExtension
from .Converter import Converter

from UM.Mesh.MeshWriter import MeshWriter
from UM.Application import Application
from UM.Logger import Logger

from UM.i18n import i18nCatalog
catalog = i18nCatalog("cura")


class FisnarCSVWriter(MeshWriter):

    def __init__(self):
        super().__init__(add_to_recent_files = False)  # don't want the spreadsheets to appear in recent files

        if FisnarCSVWriter._instance is not None:  # already been created - should never happen
            Logger.log("e", "FisnarCSVWriter instantiated more than once")
        else:
            FisnarCSVWriter._instance = self

        self._fre_instance = FisnarRobotExtension.getInstance()
        self.converter = Converter()

    def write(self, stream, nodes, mode=MeshWriter.OutputMode.TextMode):
        # getting updated extension parameters
        self.converter.setPrintSurface(self._fre_instance.print_surface)

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

            # # debug
            # for element in gcode_list:
            #     Logger.log("d", str(element))

            # setting converter gcode and attempting to convert
            self.converter.setGcode("".join([str(chunk) for chunk in gcode_list]))
            fisnar_commands = self.converter.getFisnarCommands()

            if fisnar_commands is False:  # error was caught in conversion, get error info from converter object
                self.setInformation(catalog.i18nc("@warning:status", self.converter.getInformation()))
                return False  # error

            csv_string = Converter.fisnarCommandsToCSVString(fisnar_commands)
            stream.write(csv_string)  # writing to file
            FisnarRobotExtension.getInstance().most_recent_fisnar_commands = fisnar_commands  # updating in extension class

            return True  # successful conversion
        else:  # gcode list not found, log error
            self.setInformation(catalog.i18nc("@warning:status", "Gcode must be prepared before exporting Fisnar CSV"))
            return False  # error

    _instance = None

    @classmethod
    def getInstance(cls):
        # get the singleton instance of the FisnarCSVWriter class
        return cls._instance
