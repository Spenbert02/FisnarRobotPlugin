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

from .FisnarController import FisnarController
from .Converter import Converter
from .PrinterAttributes import PrintSurface, ExtruderArray

catalog = i18nCatalog("cura")

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
            "com_port": None
        }
        self.preferences.addPreference("fisnar/setup", json.dumps(default_preferences))

        # internal preference values
        self.print_surface = PrintSurface(0.0, 200.0, 0.0, 200.0, 150.0)
        self.num_active_extruders = None
        self.extruder_outputs = ExtruderArray(4)  # array of 4 'extruders'
        self.com_port = None

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

    @classmethod
    def getInstance(cls):
        # factory method
        return cls._instance

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
        if pref_dict.get("com_port", -1) is not -1:
            if pref_dict["com_port"] is None or pref_dict["com_port"] == "None":
                self.com_port = None
            else:
                self.com_port = pref_dict["com_port"]
            self.fisnar_controller.setComPort(self.com_port)

        Logger.log("d", "preference values retrieved: " + str(self.print_surface.getDebugString()) + str(self.extruder_outputs.getDebugString()) + f"com_port: {self.com_port}")

    def updatePreferencedValues(self):
        # update the stored preference values from the user entered values
        new_pref_dict = {
            "print_surface": self.print_surface.getAsTuple(),
            "extruder_outputs": self.extruder_outputs.getAsTuple(),
            "com_port": self.com_port
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

    def resetFisnarState(self):
        # reset the internal state of the FisnarController object
        self.fisnar_controller.resetInternalState()

    def logMessage(self):
        # logging message when one of the windows is opened
        Logger.log("i", "Fisnar window opened")

    printSurfaceChanged = pyqtSignal() # signal to notify print surface properties

    def setXMin(self, x_min):
        # x min setter
        self.print_surface.setXMin(float(x_min))

    def getXMin(self):
        # x min getter
        return str(self.print_surface.getXMin())

    x_min = pyqtProperty(str, fset=setXMin, fget=getXMin, notify=printSurfaceChanged)

    def setXMax(self, x_max):
        # x max setter
        self.print_surface.setXMax(float(x_max))

    def getXMax(self):
        # x max getter
        return str(self.print_surface.getXMax())

    x_max = pyqtProperty(str, fset=setXMax, fget=getXMax, notify=printSurfaceChanged)

    def setYMin(self, y_min):
        # y min setter
        self.print_surface.setYMin(float(y_min))

    def getYMin(self):
        # y min getter
        return str(self.print_surface.getYMin())

    y_min = pyqtProperty(str, fset=setYMin, fget=getYMin, notify=printSurfaceChanged)

    def setYMax(self, y_max):
        # y max setter
        self.print_surface.setYMax(float(y_max))

    def getYMax(self):
        # y max getter
        return str(self.print_surface.getYMax())

    y_max = pyqtProperty(str, fset=setYMax, fget=getYMax, notify=printSurfaceChanged)

    def setZMax(self, z_max):
        # z max setter
        Logger.log("d", f"***** z max set: {z_max}")
        self.print_surface.setZMax(float(z_max))

    def getZMax(self):
        # z max getter
        Logger.log("d", f"****** z max got: {self.print_surface.getZMax()}")
        return(str(self.print_surface.getZMax()))

    z_max = pyqtProperty(str, fset=setZMax, fget=getZMax, notify=printSurfaceChanged)

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

    comPortNameUpdated = pyqtSignal()  # signal emitted when com port name is updated

    def setComPortName(self, new_com_port):
        # com port name setter
        if new_com_port == "None" or new_com_port == None:
            self.com_port = None
        else:
            self.com_port = str(new_com_port)

    def getComPortName(self):
        # com port name getter
        return str(self.com_port)

    com_port_name = pyqtProperty(str, fset=setComPortName, fget=getComPortName, notify=comPortNameUpdated)

    @pyqtSlot(str)
    def updateComPort(self, com_port):
        # set the com port value connected to the Fisnar
        Logger.log("d", f"com port set to: '{com_port}'")
        self.setComPortName(com_port)
        self.fisnar_controller.setComPort(self.com_port)
        self.updatePreferencedValues()

    @pyqtProperty(str, constant=True)
    def fisnar_control_text(self):
        # text for fisnar control initial window
        return "The most recently saved Fisnar CSV will be uploaded to the Fisnar. To go back, press 'Cancel'. To begin the uploading process, press 'Begin'. Once the process begins, a 'terminate' button will appear that can be used to kill the process."

    updatePrintingProgress = pyqtSignal()
    @pyqtProperty(str, notify=updatePrintingProgress)
    def printing_progress(self):
        # called by qml to get a string representing the printing progress
        # Logger.log("i", "getPrintingProgress() called")
        progress = self.fisnar_controller.getPrintingProgress()
        if progress is None:
            return "--%"
        else:
            return str(round(float(progress) * 100, 2)) + "%"

    updateFisnarControlErrorMsg = pyqtSignal()
    @pyqtProperty(str, notify=updateFisnarControlErrorMsg)
    def fisnar_control_error_msg(self):
        # QML property for fisnar control error message
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
        # Logger.log("i", "Define setup window called")  # test
        if not self.define_setup_window:
            self.define_setup_window = self._createDialogue("define_setup_window.qml")
        self.define_setup_window.show()

    def showFisnarControlWindow(self):
        # Logger.log("i", "Fisnar control window called")  # test
        if not self.fisnar_control_window:
            self.fisnar_control_window = self._createDialogue("fisnar_control_window.qml")
        self.fisnar_control_window.show()

    def showFisnarErrorWindow(self):
        # Logger.log("i", "Fisnar error msg window called")  # test
        if not self.fisnar_error_window:
            self.fisnar_error_window = self._createDialogue("fisnar_control_error.qml")
        self.fisnar_error_window.show()

    def showFisnarProgressWindow(self):
        # Logger.log("i", "Fisnar progress window called")  # test

        # displaying window
        if not self.fisnar_progress_window:
            self.fisnar_progress_window = self._createDialogue("fisnar_control_prog.qml")
        self.fisnar_progress_window.show()

        # connecting timer
        self.progress_update_timer.timeout.connect(self.fisnar_progress_window.updateProgress)
        self.progress_update_timer.timeout.connect(self.trackUploadProgress)

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
