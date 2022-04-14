import copy
import numpy
import os.path
import sys
from typing import Optional, Union, List

from cura.BuildVolume import BuildVolume
from cura.CuraApplication import CuraApplication

from PyQt5.QtCore import QObject, QUrl, pyqtSlot, pyqtProperty
from PyQt5.QtQml import QQmlComponent, QQmlContext

from UM.Application import Application
from UM.Extension import Extension
from UM.Logger import Logger
from UM.Math.Polygon import Polygon
from UM.PluginRegistry import PluginRegistry
from UM.Scene.Iterator.BreadthFirstIterator import BreadthFirstIterator

from .AutoUploader import AutoUploader

# needed for all 'manual' imports
import importlib
plugin_folder_path = os.path.dirname(__file__)

# importing pyperclip
pyperclip_path = os.path.join(plugin_folder_path, "pyperclip", "src", "pyperclip", "__init__.py")
spec_2 = importlib.util.spec_from_file_location("pyperclip", pyperclip_path)
pyperclip_module = importlib.util.module_from_spec(spec_2)
sys.modules["pyperclip"] = pyperclip_module
spec_2.loader.exec_module(pyperclip_module)
import pyperclip


class FisnarCSVParameterExtension(QObject, Extension):


    # for factory methods. This will be set to the instance of this class once initialized.
    # this class is only instantiated once, when Cura first opens.
    _instance = None


    def __init__(self, parent=None):
        # calling necessary super methods.
        QObject.__init__(self, parent)
        Extension.__init__(self)

        # factory object creation
        if FisnarCSVParameterExtension._instance is not None:  # if object has already been instantiated
            Logger.log("e", "****** FisnarCSVParameterExtension instantiated more than once")
        else:  # first time instantiating object
            # Logger.log("i", "****** FisnarCSVParameterExtension instantiated for the first time")  # test
            FisnarCSVParameterExtension._instance = self

        # signal to update disallowed areas whenever build plate activity is changed
        # this is called a shit load. It works for now, but maybe look for a cleaner solution in the future
        CuraApplication.getInstance().activityChanged.connect(self.resetDisallowedAreas)

        # print area parameters
        self.fisnar_x_min = 0.0
        self.fisnar_x_max = 200.0
        self.fisnar_y_min = 0.0
        self.fisnar_y_max = 200.0
        self.fisnar_z_max = 100.0

        # output correlations
        self.num_extruders = None
        self.extruder_1_output = None
        self.extruder_2_output = None
        self.extruder_3_output = None
        self.extruder_4_output = None

        # setting up menus
        self.setMenuName("Fisnar Parameter Entry")
        self.addMenuItem("Define Print Surface", self.showParameterEntryWindow)
        self.addMenuItem("Correlate Outputs with Extruders", self.showOutputEntryWindow)
        self.addMenuItem("Start Auto-Upload Process", self.showAutoUploadWindow)
        self.addMenuItem("Test", self.test)

        # 'lazy loading' windows, so can be called later.
        self.parameter_entry_window = None
        self.output_entry_window = None
        self.auto_upload_window = None

        # auto upload dialog text
        self.auto_upload_dialog_text = "When the autoupload process starts, it will take control of the mouse and keyboard. At any time, you can press escape to terminate the process. Once terminated, you cannot resume progress. Press Ok to start the auto upload process, or Cancel to go back."

        # for passing to auto uploader object
        self.most_recent_fisnar_commands = None

        # writes to logger when something happens (TODO figure out when this is called, although it doesn't really matter).
        # ya pretty sure this is totally irrelevant but I'm gonna leave it
        Application.getInstance().mainWindowChanged.connect(self.logMessage)


    def test(self):
        auto_uploader = AutoUploader()
        auto_uploader.test()


    @classmethod
    def getInstance(cls):
        return cls._instance


    def resetDisallowedAreas(self):
        # turning fisnar coords to gcode coords (fisnar coords are inverted in each direction)
        # the following inversion is based on a (200, 200, 100) fisnar print area. Note: the printer in cura needs to be set up as such to look the best
        # also, the min and max nomenclatures are flipped (because the directions are inverted)
        # NOTE: for some reason, the build volume class takes the origin of the build plate to be at the center
        # NOTE: this code assumes a build volume x-y dimension of (200, 200). Any integers seen in this code are based off of this assumption

        # adding disallowed areas to each BuildVolume object
        scene = Application.getInstance().getController().getScene()
        for node in BreadthFirstIterator(scene.getRoot()):
            if isinstance(node, BuildVolume):
                # getting build volume dimensions and original disallowed areas, for documentation
                orig_disallowed_areas = node.getDisallowedAreas()
                x_dim = node.getWidth()  # NOTE: I think width corresponds to x, not sure
                y_dim = node.getDepth()  # NOTE: same as above comment. I think this is right

                # converting coord system from fisnar to build volume coord system
                bv_x_min = 100 - self.fisnar_x_max
                bv_x_max = 100 - self.fisnar_x_min
                bv_y_min = self.fisnar_y_min - 100
                bv_y_max = self.fisnar_y_max - 100
                new_z_dim = self.fisnar_z_max

                # establishing new dissalowed areas (list of Polygon objects)
                new_disallowed_areas = []
                new_disallowed_areas.append(self.handledPolygon([[-100, -100], [-100, 100], [bv_x_min, bv_y_max], [bv_x_min, bv_y_min]]))
                new_disallowed_areas.append(self.handledPolygon([[-100, 100], [100, 100], [bv_x_max, bv_y_max], [bv_x_min, bv_y_max]]))
                new_disallowed_areas.append(self.handledPolygon([[100, 100], [100, -100], [bv_x_max, bv_y_min], [bv_x_max, bv_y_max]]))
                new_disallowed_areas.append(self.handledPolygon([[100, -100], [-100, -100], [bv_x_min, bv_y_min], [bv_x_max, bv_y_min]]))

                # getting rid of old polygons in old list
                iter = 0
                while iter < len(orig_disallowed_areas):
                    if isinstance(orig_disallowed_areas[iter], self.handledPolygon):
                        orig_disallowed_areas.pop(iter)
                    else:
                        iter += 1

                # updating original list with new list
                for poly in new_disallowed_areas:
                    orig_disallowed_areas.append(poly)

                # setting new disallowed areas and rebuilding (not sure if the rebuild is necessary)
                node.setDisallowedAreas(orig_disallowed_areas)
                node.setHeight(new_z_dim)
                node.rebuild()

                # logging updated disallowed areas, tests
                # Logger.log("i", "****** build volume disallowed areas have been reset")
                # Logger.log("i", "****** original disallowed areas: " + str(orig_disallowed_areas))
                # Logger.log("i", "****** new disallowed areas: " + str(new_disallowed_areas))


    def logMessage(self):
        # logging message when one of the windows is opened
        Logger.log("i", "Fisnar parameter or output entry window opened")


    @pyqtProperty(str)
    def getXMin(self):
        return str(self.fisnar_x_min)


    @pyqtProperty(str)
    def getXMax(self):
        return str(self.fisnar_x_max)


    @pyqtProperty(str)
    def getYMin(self):
        return str(self.fisnar_y_min)


    @pyqtProperty(str)
    def getYMax(self):
        return str(self.fisnar_y_max)


    @pyqtProperty(str)
    def getZMax(self):
        return str(self.fisnar_z_max)


    @pyqtSlot(str, str)
    def setCoord(self, attribute, coord_val):
        setattr(self, attribute, float(coord_val))  # validation occurs in the qml file
        # Logger.log("i", "***** " + str(attribute) + " set to " + str(getattr(self, attribute)) + " *****")  # test
        self.resetDisallowedAreas()  # updating disallowed areas on the build plate


    @pyqtProperty(int)
    def getNumExtruders(self):
        self.num_extruders = len(Application.getInstance().getExtrudersModel()._active_machine_extruders)
        # Logger.log("i", "***** number of extruders: " + str(self.num_extruders))  # test
        return self.num_extruders


    @pyqtProperty(str)
    def getExtruder1Output(self):
        return str(self.extruder_1_output)


    @pyqtProperty(str)
    def getExtruder2Output(self):
        return str(self.extruder_2_output)


    @pyqtProperty(str)
    def getExtruder3Output(self):
        return str(self.extruder_3_output)


    @pyqtProperty(str)
    def getExtruder4Output(self):
        return str(self.extruder_4_output)


    @pyqtSlot(str, str)
    def setExtruderOutput(self, attribute, output_val):
        setattr(self, attribute, int(output_val))
        # Logger.log("i", "***** attribute '" + str(attribute) + "' set to " + str(output_val))  # test


    @pyqtProperty(str)
    def getAutoUploadDialogText(self):
        # this is called by qml
        return self.auto_upload_dialog_text


    @pyqtSlot()
    def startAutoUpload(self):
        pass


    @pyqtSlot()
    def cancelAutoUpload(self):
        # this is done before anything auto upload related is started,
        # so this doesn't really need to exist. But it's here, just in case it might have a use in the future.
        # Logger.log("i", "auto upload process cancelled")  # test

        Logger.log("i", "cancelAutoUpload() called (autoupload.qml canceled)")  # TEST


    def showParameterEntryWindow(self):
        # Logger.log("i", "parameter entry window called")  # test
        if not self.parameter_entry_window:  # ensure a window isn't already created
            self.parameter_entry_window = self._createDialogue("parameter_entry.qml")
        self.parameter_entry_window.show()


    def showOutputEntryWindow(self):
        # Logger.log("i", "Output Entry Window Called")  # test
        if not self.output_entry_window:
            self.output_entry_window = self._createDialogue("output_entry.qml")
        self.output_entry_window.show()


    def showAutoUploadWindow(self):
        # Logger.log("i", "auto upload window called")  # test
        if not self.auto_upload_window:
            self.auto_upload_window = self._createDialogue("autoupload.qml")
        self.auto_upload_window.show()


    def _createDialogue(self, qml_file_name):
        # Logger.log("i", "***** Fisnar CSV Writer dialogue created")  # test
        qml_file_path = os.path.join(PluginRegistry.getInstance().getPluginPath(self.getPluginId()), "resources", "qml", qml_file_name)
        component = Application.getInstance().createQmlComponent(qml_file_path, {"main": self})
        return component


    class handledPolygon(Polygon):
        # class that extends Polygon object so a polygon can be checked if it has been set in this extension or by something else
        # to see if a 'Polygon' object is handledPolygon, just check it's instance
        def __init__(self, points: Optional[Union[numpy.ndarray, List]] = None):
            super().__init__(points)
