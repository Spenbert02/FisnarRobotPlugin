import copy
import json
import numpy
import os.path
import sys
import threading
import time
from typing import Optional, Union, List

from cura.BuildVolume import BuildVolume
from cura.CuraApplication import CuraApplication

from PyQt6.QtCore import QObject, QUrl, QTimer, pyqtSlot, pyqtProperty
from PyQt6.QtQml import QQmlComponent, QQmlContext

from UM.Application import Application
from UM.Extension import Extension
from UM.Logger import Logger
from UM.Math.Polygon import Polygon
from UM.PluginRegistry import PluginRegistry
from UM.Resources import Resources
from UM.Scene.Iterator.BreadthFirstIterator import BreadthFirstIterator

from .FisnarController import FisnarController
from .Converter import Converter
from .PrinterAttributes import PrintSurface, ExtruderArray


class FisnarRobotExtension(QObject, Extension):


    # for factory methods. This will be set to the instance of this class once initialized.
    # this class is only instantiated once, when Cura first opens.
    _instance = None


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

        # signal to update disallowed areas whenever build plate activity is changed
        # this is called a shit load. It works for now, but maybe look for a cleaner solution in the future
        CuraApplication.getInstance().activityChanged.connect(self.resetDisallowedAreas)

        # preferences - defining all into a single preference in the form of a dictionary
        self.preferences = Application.getInstance().getPreferences()
        default_preferences = {
            "print_surface": [0.0, 200.0, 0.0, 200.0, 150.0],
            "extruder_outputs": [None, None, None, None]
        }
        self.preferences.addPreference("fisnar/setup", json.dumps(default_preferences))

        # defining print surface
        self.print_surface = PrintSurface(0.0, 200.0, 0.0, 200.0, 150.0)

        # output correlations
        self.num_extruders = None
        self.extruder_outputs = ExtruderArray(4)  # array of 4 'extruders'

        # # setting setting values to values stored in preferences, and updating build area view
        self.updateFromPreferencedValues()
        self.resetDisallowedAreas()

        # setting up menus
        self.setMenuName("Fisnar Actions")
        self.addMenuItem("Define Setup", self.showDefineSetupWindow)
        self.addMenuItem("Print", self.showFisnarControlWindow)

        # 'lazy loading' windows, so can be called later.
        self.define_setup_window = None
        self.fisnar_control_window = None
        self.fisnar_error_window = None
        self.fisnar_progress_window = None

        # for passing to serial uploader object
        self.most_recent_fisnar_commands = None

        # initializing FisnarController
        self.fisnar_controller = FisnarController()

        # timer for updating progress
        self.progress_update_timer = QTimer()
        self.progress_update_timer.setInterval(500)

        # timer for resetting FisnarController internal state
        self.fisnar_reset_timer = QTimer()
        self.fisnar_reset_timer.setInterval(5000)
        self.fisnar_reset_timer.setSingleShot(True)  # stops after one timeout
        self.fisnar_reset_timer.timeout.connect(self.resetFisnarState)

        # # filepaths to local resources
        # self.local_meshes_path = os.path.join(Resources.getStoragePathForType(Resources.Resources), "meshes")
        # self.local_printer_defs_path = os.path.join(Resources.getStoragePathForType(Resources.DefinitionContainers))
        #
        # # checking if plugin files are installed
        # if self.isInstalled():
        #     pass
        # else:
        #     pass

        # writes to logger when something happens (TODO figure out when this is called, although it doesn't really matter).
        # ya pretty sure this is totally irrelevant but I'm gonna leave it
        Application.getInstance().mainWindowChanged.connect(self.logMessage)


    @classmethod
    def getInstance(cls):
        # factory method
        return cls._instance


    # def isInstalled(self):
    #     # return True if all plugin files are already installed, and False if
    #     # ANY are not
    #     fisnar_buildplate_file = os.path.join(self.local_meshes_path, "fisnar_buildplate.3mf")
    #     fisnar_f5200n_def_file = os.path.join(self.local_printer_defs_path, "fisnar_f5200n.def.json")
    #
    #     if not os.path.isfile(fisnar_buildplate_file):
    #         Logger.log("i", "FisnarRobotPlugin")


    def updateFromPreferencedValues(self):
        # set all setting values to the value stored in the application preferences
        Logger.log("d", self.preferences.getValue("fisnar/setup"))

        pref_dict = json.loads(self.preferences.getValue("fisnar/setup"))
        if pref_dict.get("print_surface", None) is not None:
            self.print_surface.updateFromTuple(pref_dict["print_surface"])
        if pref_dict.get("extruder_outputs", None) is not None:
            self.extruder_outputs.updateFromTuple(pref_dict["extruder_outputs"])

        Logger.log("d", "preference values retrieved: " + str(self.print_surface.getDebugString()) + str(self.extruder_outputs.getDebugString()))


    def updatePreferencedValues(self):
        # update the stored preference values from the user entered values
        new_pref_dict = {
            "print_surface": self.print_surface.getAsTuple(),
            "extruder_outputs": self.extruder_outputs.getAsTuple()
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
        scene = Application.getInstance().getController().getScene()
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

                # getting rid of old polygons in old list
                iter = 0
                while iter < len(orig_disallowed_areas):
                    if isinstance(orig_disallowed_areas[iter], self.HandledPolygon):
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


    def resetFisnarState(self):
        # reset the internal state of the FisnarController object
        self.fisnar_controller.resetInternalState()


    def logMessage(self):
        # logging message when one of the windows is opened
        Logger.log("i", "Fisnar parameter or output entry window opened")


    @pyqtProperty(str)
    def getXMin(self):
        # called by qml to get the min x coord
        return str(self.print_surface.getXMin())


    @pyqtProperty(str)
    def getXMax(self):
        # called by qml to get the max x coord
        return str(self.print_surface.getXMax())


    @pyqtProperty(str)
    def getYMin(self):
        # called by qml to get the min y coord
        return str(self.print_surface.getYMin())


    @pyqtProperty(str)
    def getYMax(self):
        # called by qml to get the max y coord
        return str(self.print_surface.getYMax())


    @pyqtProperty(str)
    def getZMax(self):
        # called by qml to get the max z coord
        return str(self.print_surface.getZMax())


    @pyqtSlot(str, str)
    def setCoord(self, attribute, coord_val):
        # slot for qml to set the value of one of the home coordinates

        # updating coordinate value
        if attribute == "fisnar_x_min":
            self.print_surface.setXMin(float(coord_val))
        elif attribute == "fisnar_x_max":
            self.print_surface.setXMax(float(coord_val))
        elif attribute == "fisnar_y_min":
            self.print_surface.setYMin(float(coord_val))
        elif attribute == "fisnar_y_max":
            self.print_surface.setYMax(float(coord_val))
        elif attribute == "fisnar_z_max":
            self.print_surface.setZMax(float(coord_val))
        else:
            Logger.log("w", "setCoord() attribute not recognized: '" + str(attribute) + "'")

        self.updatePreferencedValues()
        self.resetDisallowedAreas()  # updating disallowed areas on the build plate


    @pyqtProperty(int)
    def getNumExtruders(self):
        # called by qml to get the number of active extruders in Cura
        self.num_extruders = len(Application.getInstance().getExtrudersModel()._active_machine_extruders)
        # Logger.log("i", "***** number of extruders: " + str(self.num_extruders))  # test
        return self.num_extruders


    @pyqtSlot(str, str)
    def setExtruderOutput(self, extruder_num, output_val):
        # slot for qml to set the output associated with one of the extruders

        extruder_num = int(extruder_num)
        if extruder_num in (1, 2, 3, 4):
            self.extruder_outputs.setOutput(extruder_num, output_val)
        else:  # throw a warning and return
            Logger.log("w", "Out of range extruder number set in setExtruderOutput(): " + str(extruder_num))
            return
        self.updatePreferencedValues()


    @pyqtProperty(int)
    def getExt1OutputInd(self):
        # get the output of extruder 1 as the index of the list model of outputs in qml code.
        # for reference, 0->None, 1->1, 2->2, 3->3, 4->4
        if self.extruder_outputs.getOutput(1) is None:
            return 0
        else:
            return int(self.extruder_outputs.getOutput(1))


    @pyqtProperty(int)
    def getExt2OutputInd(self):
        if self.extruder_outputs.getOutput(2) is None:
            return 0
        else:
            return int(self.extruder_outputs.getOutput(2))


    @pyqtProperty(int)
    def getExt3OutputInd(self):
        if self.extruder_outputs.getOutput(3) is None:
            return 0
        else:
            return int(self.extruder_outputs.getOutput(3))


    @pyqtProperty(int)
    def getExt4OutputInd(self):
        if self.extruder_outputs.getOutput(4) is None:
            return 0
        else:
            return int(self.extruder_outputs.getOutput(4))


    @pyqtProperty(str)
    def getFisnarControlText(self):
        return "The most recently saved Fisnar CSV will be uploaded to the Fisnar. To go back, press 'Cancel'. To begin the uploading process, press 'Begin'. Once the process begins, a 'terminate' button will appear that can be used to kill the process."


    @pyqtProperty(str)
    def getPrintingProgress(self):
        # called by qml to get a string representing the printing progress
        # Logger.log("i", "getPrintingProgress() called")

        progress = self.fisnar_controller.getPrintingProgress()
        if progress is None:
            return "--%"
        else:
            return str(round(float(progress) * 100, 2)) + "%"


    @pyqtProperty(str)
    def getFisnarControlErrorMsg(self):
        return "Error occured while uploading commands: " + self.fisnar_controller.getInformation()


    @pyqtSlot()
    def cancelFisnarControl(self):
        # called when the user presses cancel on the fisnar control initial window
        Logger.log("i", "Fisnar control cancelled")


    @pyqtSlot()
    def terminateFisnarControl(self):
        # called by qml when 'terminate' button is pressed during fisnar printing
        # Logger.log("d", "terminateFisnarControl() called")  # test
        self.fisnar_controller.setTerminateRunning(True)


    def trackUploadProgress(self):
        # check if the print is done or has been terminated or has thrown an error
        # and update ui. Update progress if print is still going.

        if (self.fisnar_controller.successful_print is not None) or self.fisnar_controller.getTerminateRunning():  # print either failed or finished or terminated
            self.progress_update_timer.stop()  # stopping timer because print is done
            self.fisnar_progress_window.close()  # closing the progress window

            if self.fisnar_controller.getTerminateRunning():  # print was terminated
                Logger.log("i", "print terminated.")
            elif self.fisnar_controller.successful_print:  # print finished succesfully
                Logger.log("i", "Successful fisnar print!")
            else:  # error occured while uploading
                self.showFisnarErrorWindow()
                Logger.log("i", "Fisnar print failed...")

            # resetting FisnarController internal state
            self.fisnar_reset_timer.start()

    @pyqtSlot()
    def beginFisnarControl(self):
        # called when the user presses begin on the fisnar control initial window
        Logger.log("i", "Attempting to control Fisnar")

        # showing progress window
        self.showFisnarProgressWindow()

        # setting commands
        self.fisnar_controller.setCommands(self.most_recent_fisnar_commands)

        # starting upload thread
        upload_thread = threading.Thread(target=self.fisnar_controller.runCommands)
        upload_thread.start()

        # starting update progress timer, which will update the progress window
        self.progress_update_timer.start()


    def showDefineSetupWindow(self):
        Logger.log("i", "Define setup window called")  # test
        if not self.define_setup_window:
            self.define_setup_window = self._createDialogue("define_setup_window.qml")
        self.define_setup_window.show()


    def showFisnarControlWindow(self):
        Logger.log("i", "Fisnar control window called")  # test
        if not self.fisnar_control_window:
            self.fisnar_control_window = self._createDialogue("fisnar_control_window.qml")
        self.fisnar_control_window.show()


    def showFisnarErrorWindow(self):
        Logger.log("i", "Fisnar error msg window called")  # test
        if not self.fisnar_error_window:
            self.fisnar_error_window = self._createDialogue("fisnar_control_error.qml")
        self.fisnar_error_window.show()


    def showFisnarProgressWindow(self):
        Logger.log("i", "Fisnar progress window called")  # test

        # displaying window
        if not self.fisnar_progress_window:
            self.fisnar_progress_window = self._createDialogue("fisnar_control_prog.qml")
        self.fisnar_progress_window.show()

        # connecting timer
        self.progress_update_timer.timeout.connect(self.fisnar_progress_window.updateProgress)
        self.progress_update_timer.timeout.connect(self.trackUploadProgress)


    def _createDialogue(self, qml_file_name):
        # Logger.log("i", "***** Fisnar CSV Writer dialogue created")  # test
        qml_file_path = os.path.join(PluginRegistry.getInstance().getPluginPath(self.getPluginId()), "resources", "qml", qml_file_name)
        component = Application.getInstance().createQmlComponent(qml_file_path, {"main": self})
        return component


    class HandledPolygon(Polygon):
        # class that extends Polygon object so a polygon can be checked if it has been set in this extension or by something else
        # to see if a 'Polygon' object is HandledPolygon, just check the instance's type
        def __init__(self, points: Optional[Union[numpy.ndarray, List]] = None):
            super().__init__(points)
