import copy
import json
import numpy
import os
import os.path
import stat
import sys
import threading
import time
import zipfile

from typing import Optional, Union, List

from cura.BuildVolume import BuildVolume
from cura.CuraApplication import CuraApplication

from PyQt6.QtCore import QObject, QUrl, QTimer, pyqtSlot, pyqtProperty, pyqtSignal
from PyQt6.QtQml import QQmlComponent, QQmlContext

from UM.i18n import i18nCatalog
from UM.Application import Application
from UM.Extension import Extension
from UM.Logger import Logger
from UM.Math.Polygon import Polygon
from UM.Message import Message
from UM.PluginRegistry import PluginRegistry
from UM.Resources import Resources
from UM.Scene.Iterator.BreadthFirstIterator import BreadthFirstIterator

# from .FisnarController import FisnarController
from .Converter import Converter
from .PrinterAttributes import PrintSurface, ExtruderArray

catalog = i18nCatalog("cura")

class FisnarRobotExtension(QObject, Extension):

    def __init__(self, parent=None):
        # calling necessary super methods.
        QObject.__init__(self, parent)
        Extension.__init__(self)

        # factory object creation
        if FisnarRobotExtension._instance is not None:  # if object has already been instantiated
            Logger.log("e", "FisnarRobotExtension instantiated more than once")
        else:  # first time instantiating object
            # Logger.log("i", "****** FisnarRobotExtension instantiated for the first time")  # test
            FisnarRobotExtension._instance = self

        # initializing applications
        self._application = Application.getInstance()
        self._cura_app = CuraApplication.getInstance()

        # signal emitted when ExtrudersModel changes
        numActiveExtrudersChanged = self._cura_app.getExtrudersModel().modelChanged

        # preferences - defining all into a single preference in the form of a dictionary
        self.preferences = self._application.getPreferences()
        default_preferences = {
            "print_surface": [0.0, 200.0, 0.0, 200.0, 150.0],
            "extruder_outputs": [None, None, None, None],
            "com_port": None,
            "dispenser_com_port": None,
            "pick_location": (0.0, 0.0, 0.0),
            "place_location": (0.0, 0.0, 0.0),
            "vacuum_pressure": 0.0,
            "vacuum_units": 0,  # uses enumeration in UltimusV.PressureUnits
            "xy_speed": 0.0,
            "z_speed": 0.0
        }
        self.preferences.addPreference("fisnar/setup", json.dumps(default_preferences))

        # internal printing preference values
        self.print_surface = PrintSurface(0.0, 200.0, 0.0, 200.0, 150.0)
        self.num_active_extruders = None
        self.extruder_outputs = ExtruderArray(4)  # array of 4 'extruders'
        self.com_port = None

        # internal pick and place preference values
        self.dispenser_com_port = None
        self.pick_location = (0.0, 0.0, 0.0)
        self.place_location = (0.0, 0.0, 0.0)
        self.vacuum_pressure = 0.0
        self.vacuum_units = 0
        self.xy_speed = 0.0
        self.z_speed = 0.0

        # setting up menus
        self.setMenuName("Fisnar Actions")
        self.addMenuItem("Define Setup", self.showDefineSetupWindow)
        # self.addMenuItem("Print", self.showFisnarControlWindow)

        # 'lazy loading' windows, so can be called later.
        self.define_setup_window = None

        # timer for resetting disallowed areas when a file is loaded
        self.reset_dis_areas_timer = QTimer()
        self.reset_dis_areas_timer.setInterval(500)
        self.reset_dis_areas_timer.setSingleShot(True)
        self.reset_dis_areas_timer.timeout.connect(self.resetDisallowedAreas)
        self._cura_app.fileCompleted.connect(self.startResetDisAreasTimer)

        # filepaths to local resources
        self.this_plugin_path = os.path.join(Resources.getStoragePath(Resources.Resources, "plugins", "FisnarRobotPlugin", "FisnarRobotPlugin"))
        self.local_meshes_path = os.path.join(Resources.getStoragePathForType(Resources.Resources), "meshes")
        self.local_printer_defs_path = os.path.join(Resources.getStoragePathForType(Resources.DefinitionContainers))

        # checking if plugin files are installed
        update_necessary = False
        if self.isInstalled():
            if self.defFilesAreUpdated():  # up-to-date
                Logger.log("i", "Up-to-date FisnarRobotPlugin extension files are already installed.")
            else:  # need to be updated
                Logger.log("i", "FisnarRobotPlugin files need to be updated.")
                update_necessary = True
        else:  # files not installed
            Logger.log("i", "One or more FisnarRobotPlugin files needs to be installed")
            update_necessary = True

        if update_necessary:
            self.installDefFiles()
            Logger.log("i", "All FisnarRobotPlugin files are installed and up-to-date")

        # setting setting values to values stored in preferences, and updating build area view
        self.startResetDisAreasTimer()
        self.updateFromPreferencedValues()

    def defFilesAreUpdated(self):
        # return True if the locally installed def files are up to date,
        # otherwise return False. Not sure the mechanism by which the version
        # can be tracked, but probably just go off the Dremel plugin example
        return False

    def isInstalled(self):
        # return True if all plugin files are already installed, and False if
        # ANY are not
        fisnar_buildplate_file = os.path.join(self.local_meshes_path, "fisnar_buildplate.3mf")
        fisnar_f5200n_def_file = os.path.join(self.local_printer_defs_path, "fisnar_f5200n.def.json")

        if not os.path.isfile(fisnar_buildplate_file):
            Logger.log("i", f"file '{fisnar_buildplate_file}' is not installed")
            return False
        if not os.path.isfile(fisnar_f5200n_def_file):
            Logger.log("i", f"file '{fisnar_f5200n_def_file}' is not installed")
            return False

        return True  # all files are installed

    def installDefFiles(self):
        # install definition files

        try:
            zipdata = os.path.join(self.this_plugin_path, "resources", "definitions.zip")
            Logger.log("i", f"found zipfile: {zipdata}")

            with zipfile.ZipFile(zipdata, "r") as zip_files:
                for info in zip_files.infolist():
                    Logger.log("i", f"found in zip file: {info.filename}")

                    folder = None
                    if info.filename == "fisnar_buildplate.3mf":
                        folder = self.local_meshes_path
                        if not os.path.exists(folder):  # making the meshes folder because cura doesn't make it for some reason
                            os.mkdir(folder)
                    elif info.filename == "fisnar_f5200n.def.json":
                        folder = self.local_printer_defs_path

                    if folder is not None:
                        extracted_path = zip_files.extract(info.filename, path=folder)
                        permissions = os.stat(extracted_path).st_mode
                        os.chmod(extracted_path, permissions | stat.S_IEXEC)  # bitwise OR?
                        Logger.log("i", f"file {info.filename} installed to {extracted_path}")
                    else:
                        Logger.log("w", f"unrecognized file in definitions.zip: {info.filename}")

            if self.isInstalled():
                Logger.log("i", "all Fisnar Robot Plugin files successfully installed")
        except:
            Logger.log("w", "An error occured while installing the Fisnar Robot Plugin files.")
            warning = Message(catalog.i18nc("@warning:status", "An error occured while installing Fisnar Robot Plugin files."))
            warning.show()

    def startResetDisAreasTimer(self):
        # start the reset disallowed areas timer
        self.reset_dis_areas_timer.start()

    def updateFromPreferencedValues(self):
        # set all setting values to the value stored in the application preferences
        # Logger.log("d", f"preferences retrieved: {self.preferences.getValue("fisnar/setup")}")
        pref_dict = json.loads(self.preferences.getValue("fisnar/setup"))

        if pref_dict.get("print_surface", None) is not None:
            self.print_surface.updateFromTuple(pref_dict["print_surface"])
        if pref_dict.get("extruder_outputs", None) is not None:
            self.extruder_outputs.updateFromTuple(pref_dict["extruder_outputs"])
        if pref_dict.get("com_port", -1) != -1:
            # self.com_port = pref_dict["com_port"]
            self.updateComPort(pref_dict["com_port"])
        if pref_dict.get("dispenser_com_port", -1) != -1:
            self.dispenser_com_port = pref_dict["dispenser_com_port"]
        if pref_dict.get("pick_location", None) is not None:
            self.pick_location = pref_dict["pick_location"]
        if pref_dict.get("place_location", None) is not None:
            self.place_location = pref_dict["place_location"]
        if pref_dict.get("vacuum_pressure", None) is not None:
            self.vacuum_pressure = pref_dict["vacuum_pressure"]
        if pref_dict.get("vacuum_units", None) is not None:
            self.vacuum_units = pref_dict["vacuum_units"]
        if pref_dict.get("xy_speed", None) is not None:
            self.xy_speed = pref_dict["xy_speed"]
        if pref_dict.get("z_speed", None) is not None:
            self.z_speed = pref_dict["z_speed"]

        Logger.log("d", "preference values retrieved: " + str(self.print_surface.getDebugString()) + str(self.extruder_outputs.getDebugString()) + f"com_port: {self.com_port}")

    def updatePreferencedValues(self):
        # update the stored preference values from the user entered values
        new_pref_dict = {
            "print_surface": self.print_surface.getAsTuple(),
            "extruder_outputs": self.extruder_outputs.getAsTuple(),
            "com_port": self.com_port,
            "dispenser_com_port": self.dispenser_com_port,
            "pick_location": self.pick_location,
            "place_location": self.place_location,
            "vacuum_pressure": self.vacuum_pressure,
            "vacuum_units": self.vacuum_units,
            "xy_speed": self.xy_speed,
            "z_speed": self.z_speed
        }
        self.preferences.setValue("fisnar/setup", json.dumps(new_pref_dict))

    def resetDisallowedAreas(self):
        # turning fisnar coords to gcode coords (fisnar coords are inverted in each direction)
        # the following inversion is based on a (200, 200, 100) fisnar print area. Note: the printer in cura needs to be set up as such to look the best
        # also, the min and max nomenclatures are flipped (because the directions are inverted)
        # NOTE: for some reason, the build volume class takes the origin of the build plate to be at the center
        # NOTE: this code assumes a build volume x-y dimension of (200, 200). Any integers seen in this code are based off of this assumption

        # test
        # Logger.log("d", "current print surface in resetDisallowedAreas: " + str(self.print_surface.getDebugString()))

        # adding disallowed areas to each BuildVolume object
        scene = self._application.getController().getScene()
        for node in BreadthFirstIterator(scene.getRoot()):
            if isinstance(node, BuildVolume):

                # getting build volume dimensions and original disallowed areas, for documentation
                orig_disallowed_areas = node.getDisallowedAreas()
                x_dim = node.getWidth()  # NOTE: I think width corresponds to x, not sure
                y_dim = node.getDepth()  # NOTE: same as above comment. I think this is right

                # converting coord system from fisnar to build volume coord system
                bv_x_min = 100 - self.print_surface.getXMax()
                bv_x_max = 100 - self.print_surface.getXMin()
                bv_y_min = self.print_surface.getYMin() - 100
                bv_y_max = self.print_surface.getYMax() - 100
                new_z_dim = self.print_surface.getZMax()

                # establishing new dissalowed areas (list of Polygon objects)
                new_disallowed_areas = []
                new_disallowed_areas.append(self.HandledPolygon([[-100, -100], [-100, 100], [bv_x_min, bv_y_max], [bv_x_min, bv_y_min]]))
                new_disallowed_areas.append(self.HandledPolygon([[-100, 100], [100, 100], [bv_x_max, bv_y_max], [bv_x_min, bv_y_max]]))
                new_disallowed_areas.append(self.HandledPolygon([[100, 100], [100, -100], [bv_x_max, bv_y_min], [bv_x_max, bv_y_max]]))
                new_disallowed_areas.append(self.HandledPolygon([[100, -100], [-100, -100], [bv_x_min, bv_y_min], [bv_x_max, bv_y_min]]))

                # removing zero area polygons from disallowed area polygon list
                i = 0
                while i < len(new_disallowed_areas):
                    if new_disallowed_areas[i].isZeroArea():
                        Logger.log("i", f"zero area polygon found in disallowed areas: {new_disallowed_areas[i]}")
                        new_disallowed_areas.pop(i)
                    else:
                        i += 1

                # setting new disallowed areas and rebuilding (not sure if the rebuild is necessary)
                node.setDisallowedAreas(new_disallowed_areas)
                node.setHeight(new_z_dim)
                node.rebuild()

                # logging updated disallowed areas, tests
                # Logger.log("i", "****** build volume disallowed areas have been reset")
                # Logger.log("i", "****** original disallowed areas: " + str(orig_disallowed_areas))
                # Logger.log("i", "****** new disallowed areas: " + str(new_disallowed_areas))

    def logMessage(self):
        # logging message when one of the windows is opened
        Logger.log("i", "Fisnar window opened")

    printSurfaceChanged = pyqtSignal() # signal to notify print surface properties

# ==================== x min property setup =================
    def setXMin(self, x_min):
        # x min setter
        self.print_surface.setXMin(float(x_min))

    def getXMin(self):
        # x min getter
        return str(self.print_surface.getXMin())

    x_min = pyqtProperty(str, fset=setXMin, fget=getXMin, notify=printSurfaceChanged)

# ======================== x max property setup ======================
    def setXMax(self, x_max):
        # x max setter
        self.print_surface.setXMax(float(x_max))

    def getXMax(self):
        # x max getter
        return str(self.print_surface.getXMax())

    x_max = pyqtProperty(str, fset=setXMax, fget=getXMax, notify=printSurfaceChanged)

# ================== y min property setup ============================
    def setYMin(self, y_min):
        # y min setter
        self.print_surface.setYMin(float(y_min))

    def getYMin(self):
        # y min getter
        return str(self.print_surface.getYMin())

    y_min = pyqtProperty(str, fset=setYMin, fget=getYMin, notify=printSurfaceChanged)

# ==================== y max property setup ===========================
    def setYMax(self, y_max):
        # y max setter
        self.print_surface.setYMax(float(y_max))

    def getYMax(self):
        # y max getter
        return str(self.print_surface.getYMax())

    y_max = pyqtProperty(str, fset=setYMax, fget=getYMax, notify=printSurfaceChanged)

# ======================== z max property setup =======================
    def setZMax(self, z_max):
        # z max setter
        Logger.log("d", f"***** z max set: {z_max}")
        self.print_surface.setZMax(float(z_max))

    def getZMax(self):
        # z max getter
        Logger.log("d", f"****** z max got: {self.print_surface.getZMax()}")
        return(str(self.print_surface.getZMax()))

    z_max = pyqtProperty(str, fset=setZMax, fget=getZMax, notify=printSurfaceChanged)
# =========================================================================

    @pyqtSlot(str, str)
    def setCoord(self, attribute, coord_val):
        # slot for qml to set the value of one of the home coordinates

        # updating coordinate value
        if attribute == "fisnar_x_min":
            self.setXMin(float(coord_val))
        elif attribute == "fisnar_x_max":
            self.setXMax(float(coord_val))
        elif attribute == "fisnar_y_min":
            self.setYMin(float(coord_val))
        elif attribute == "fisnar_y_max":
            self.setYMax(float(coord_val))
        elif attribute == "fisnar_z_max":
            self.setZMax(float(coord_val))
        else:
            Logger.log("w", "setCoord() attribute not recognized: '" + str(attribute) + "'")

        # adjusting x min/max values if they are in reverse order
        if self.print_surface.getXMax() < self.print_surface.getXMin():
            new_x_max, new_x_min = self.print_surface.getXMin(), self.print_surface.getXMax()
            self.setXMin(new_x_min)
            self.setXMax(new_x_max)
            self.printSurfaceChanged.emit()

        # adjusting y min/max values if they are in reverse order
        if self.print_surface.getYMax() < self.print_surface.getYMin():
            new_y_max, new_y_min = self.print_surface.getYMin(), self.print_surface.getYMax()
            self.setYMin(new_y_min)
            self.setYMax(new_y_max)
            self.printSurfaceChanged.emit()

        self.updatePreferencedValues()
        self.resetDisallowedAreas()  # updating disallowed areas on the build plate

    numActiveExtrudersChanged = pyqtSignal()
    @pyqtProperty(int, notify=numActiveExtrudersChanged)  # connecting to signal emitted when ExtrudersModel changes
    def num_extruders(self):
        # called by qml to get the number of active extruders in Cura
        self.num_active_extruders = len(self._application.getExtrudersModel()._active_machine_extruders)
        # Logger.log("i", "***** number of extruders: " + str(self.num_active_extruders))  # test
        return self.num_active_extruders

    # signal for updating extruder values
    extruderOutputsChanged = pyqtSignal()

# ==================== Extruder 1 setter/getter system ===================
    def setExt1Out(self, output):
        # extruder 1 output setter
        if output == "None" or output == None or output == 0:
            self.extruder_outputs.setOutput(1, None)
        else:
            self.extruder_outputs.setOutput(1, int(output))
        Logger.log("d", f"***** extruder 1 set to output: {self.extruder_outputs.getOutput(1)}")

    def getExt1OutInd(self):
        # extruder 1 output index getter
        output = self.extruder_outputs.getOutput(1)
        if output == None:
            return 0
        else:
            return output

    ext_1_output_ind = pyqtProperty(int, fset=setExt1Out, fget=getExt1OutInd, notify=extruderOutputsChanged)

# ==================== Extruder 2 setter/getter system ===================
    def setExt2Out(self, output):
        # extruder 2 output setter
        if output == None or output == "None" or output == 0:
            self.extruder_outputs.setOutput(2, None)
        else:
            self.extruder_outputs.setOutput(2, int(output))
        Logger.log("d", f"***** extruder 2 set to output: {self.extruder_outputs.getOutput(2)}")

    def getExt2OutInd(self):
        # extruder 2 output index getter
        output = self.extruder_outputs.getOutput(2)
        if output is None:
            return 0
        else:
            return output

    ext_2_output_ind = pyqtProperty(int, fset=setExt2Out, fget=getExt2OutInd, notify=extruderOutputsChanged)

# ==================== Extruder 3 setter/getter system ===================
    def setExt3Out(self, output):
        # extruder 2 output setter
        if output == None or output == "None" or output == 0:
            self.extruder_outputs.setOutput(3, None)
        else:
            self.extruder_outputs.setOutput(3, int(output))
        Logger.log("d", f"***** extruder 3 set to output: {self.extruder_outputs.getOutput(3)}")

    def getExt3OutInd(self):
        # extruder 2 output index getter
        output = self.extruder_outputs.getOutput(3)
        if output is None:
            return 0
        else:
            return output

    ext_3_output_ind = pyqtProperty(int, fset=setExt3Out, fget=getExt3OutInd, notify=extruderOutputsChanged)

# ==================== Extruder 4 setter/getter system ===================
    def setExt4Out(self, output):
        # extruder 2 output setter
        if output == None or output == "None" or output == 0:
            self.extruder_outputs.setOutput(4, None)
        else:
            self.extruder_outputs.setOutput(4, int(output))
        Logger.log("d", f"***** extruder 4 set to output: {self.extruder_outputs.getOutput(4)}")

    def getExt4OutInd(self):
        # extruder 2 output index getter
        output = self.extruder_outputs.getOutput(4)
        if output is None:
            return 0
        else:
            return output

    ext_4_output_ind = pyqtProperty(int, fset=setExt4Out, fget=getExt4OutInd, notify=extruderOutputsChanged)
# ============================================================================

    @pyqtSlot(str, str)
    def setExtruderOutput(self, extruder_num, output_val):
        # slot for qml to set the output associated with one of the extruders
        extruder_num = int(extruder_num)
        if extruder_num == 1:
            self.setExt1Out(output_val)
        elif extruder_num == 2:
            self.setExt2Out(output_val)
        elif extruder_num == 3:
            self.setExt3Out(output_val)
        elif extruder_num == 4:
            self.setExt4Out(output_val)
        else:  # throw a warning and return
            Logger.log("w", "Out of range extruder number set in setExtruderOutput(): " + str(extruder_num))
            return
        self.updatePreferencedValues()

# ==================== COM port name setter/getter system ===================
    # def setComPortName(self, name):
    #     # for updating from python via function call
    #     if name != self.com_port:
    #         self.com_port = name
    #         self.comPortNameUpdated.emit()

    comPortNameUpdated = pyqtSignal()  # signal emitted when com port name is updated
    @pyqtProperty(str, notify=comPortNameUpdated)
    def com_port_name(self):
        return str(self.com_port)

    @pyqtSlot(str)
    def updateComPort(self, com_port):
        # for qml updating (user entered new value)
        Logger.log("d", f"com port set to: '{com_port}'")
        if com_port == "None":
            self.com_port = None
        else:
            self.com_port = com_port
        self.comPortNameUpdated.emit()
        self.updatePreferencedValues()
# ===========================================================================

    def showDefineSetupWindow(self):
        # Logger.log("i", "Define setup window called")  # test
        if not self.define_setup_window:
            self.define_setup_window = self._createDialogue("define_setup_window.qml")
        self.define_setup_window.show()

    def _createDialogue(self, qml_file_name):
        # Logger.log("i", "***** Fisnar CSV Writer dialogue created")  # test
        qml_file_path = os.path.join(self.this_plugin_path, "resources", "qml", qml_file_name)
        component = self._application.createQmlComponent(qml_file_path, {"main": self})
        return component

    class HandledPolygon(Polygon):
        # class that extends Polygon object so a polygon can be checked if it has been set in this extension or by something else
        # to see if a 'Polygon' object is HandledPolygon, just check the instance's type
        def __init__(self, points: Optional[Union[numpy.ndarray, List]] = None):
            super().__init__(points)

        def isZeroArea(self):
            # determine whether a given polygon has zero area
            if len(self._points) != 4:
                return False

            # check if all x's are the same
            linearly_coincident_x_coords = True
            for i in range(1, len(self._points)):
                if numpy.absolute(self._points[0][0] - self._points[i][0]) > 0.001:
                    linearly_coincident_x_coords = False  # unequal x's, area can't be zero area

            # check if all y's are the same
            linearly_coincident_y_coords = True
            for i in range(1, len(self._points)):
                if numpy.absolute(self._points[0][1] - self._points[i][1]) > 0.0001:
                    linearly_coincident_y_coords = False  # unequal y's, so area isn't 0 area

            return (linearly_coincident_x_coords or linearly_coincident_y_coords)

    _instance = None

    @classmethod
    def getInstance(cls):
        # factory method
        return cls._instance
