# functions dealing with the autoupload process for the smart robot edit software.

import copy
import importlib
import os.path
import sys
import time

from PyQt5.QtCore import QObject, QUrl, pyqtSlot, pyqtProperty, pyqtSignal
from threading import Event, Thread
from UM.Application import Application
from UM.Logger import Logger


# importing pyautogui
plugin_folder_path = os.path.dirname(__file__)
pyautogui_path = os.path.join(plugin_folder_path, "pyautogui", "pyautogui", "__init__.py")
spec = importlib.util.spec_from_file_location("pyautogui", pyautogui_path)
pyautogui_module = importlib.util.module_from_spec(spec)
sys.modules["pyautogui"] = pyautogui_module
spec.loader.exec_module(pyautogui_module)
import pyautogui

# # importing keyboard (i dont think i need to use this library at all)
keyboard_path = os.path.join(plugin_folder_path, "keyboard", "keyboard", "__init__.py")
spec_2 = importlib.util.spec_from_file_location("keyboard", keyboard_path)
keyboard_module = importlib.util.module_from_spec(spec_2)
sys.modules["keyboard"] = keyboard_module
spec_2.loader.exec_module(keyboard_module)
import keyboard


class AutoUploader(QObject):
    # class for running the auto upload process. Once instantiated,
    # the startAutoUpload() function can be called to start the auto upload
    # process. This also doubles as a QObject to handle all the necessary
    # windows and whatnot


    def __init__(self, parent=None):
        QObject.__init__(self, parent)
        self.test_window = None


    def test(self):
        Logger.log("d", "***** test called")  # debug
        self.createWindow()


    @pyqtSlot()
    def accepted(self):
        Logger.log("d", "****** accept called")  # debug


    @pyqtSlot()
    def rejected(self):
        Logger.log("d", "***** reject called")  # debug


    def createWindow(self):
        Logger.log("d", "***** createWindow called")  # debug
        if not self.test_window:
            self.test_window = self._createDialogue("next_chunk.qml")
        self.test_window.show()


    def _createDialogue(self, qml_file_name):
        Logger.log("d", "***** _createDialogue called")  # debug
        qml_file_path = os.path.join(os.path.dirname(__file__), "resources", "qml", qml_file_name)
        component = Application.getInstance().createQmlComponent(qml_file_path, {"manager": self})
        return component


    @staticmethod
    def fisnarCommandsToCSVString(fisnar_commands):
        # turn a 2d list of fisnar commands into a csv string

        ret_string = ""
        for i in range(len(fisnar_commands)):
            for j in range(len(fisnar_commands[i])):
                ret_string += str(fisnar_commands[i][j])
                if j == len(fisnar_commands[i]) - 1:
                    ret_string += "\n"
                else:
                    ret_string += ","

        return ret_string


    @staticmethod
    def chunkCommands(fisnar_command_list, command_limit):
        # given a list of fisnar commands and a command limit, return a list of lists of commands, each which can be
        # sequentially uploaded to the fisnar for printing, 'cleaning up' the start and beginning to ensure nothing
        # goes wrong.

        fisnar_commands = copy.deepcopy(fisnar_command_list)  # making a deep copy
        last_line_speed_used = 10  # to be called upon if the current 'chunk' doesn't have any line speed commands
        ret_command_lists = []  # list of lists of commands to return

        while len(fisnar_commands) > 0:  # while there are still commands to include
            comm_lim = command_limit - 5  # 5 to account for the 4 output 0 commands, and
            curr_command_list = []

            # checking if a line speed and z clearance need to be set
            first_2_commands = {fisnar_commands[0][0], fisnar_commands[1][0]}  # set, order doesn't matter
            if first_2_commands != {"Line Speed", "Z Clearance"}:
                comm_lim -= 2  # accounting for two added commands

                line_speed_val = -1  # line speed value to add to start of current chunk

                if len(ret_command_lists) > 0:  # if there is a previous chunk to call upon
                    i = len(ret_command_lists[-1]) - 1
                    while line_speed_val == -1 and i >= 0:  # until found or reach beginning of list
                        if ret_command_lists[-1][i][0] == "Line Speed":  # found
                            line_speed_val = ret_command_lists[-1][i][1]
                            last_line_speed_used = line_speed_val  # storing to use if needed in the future
                            break
                        i -= 1  # haven't found, so decrement index
                    if line_speed_val == -1:  # no line speed found
                        line_speed_val = last_line_speed_used
                else:
                    line_speed_val = last_line_speed_used

                curr_command_list.append(["Line Speed", line_speed_val])
                curr_command_list.append(["Z Clearance", 5, 1])  # defaulting to 5, can find last if needed

            # finding last output 0 command and appending list to return list
            if len(fisnar_commands) > comm_lim:  # if not at the last chunk
                output_0_comm_ind = -1
                i = comm_lim - 1
                while output_0_comm_ind == -1 and i >= 0:  # while not found or reach beginning of list
                    if fisnar_commands[i][0] == "Output" and fisnar_commands[i][2] == 0:  # output 0 found
                        output_0_comm_ind = i
                        break  # found, so break
                    i -= 1  # not found, so decrement index

                if output_0_comm_ind == -1:  # no output 0 command found TODO: make a way to get around this. its possible.
                    return None  # represents error

                for i in range(output_0_comm_ind + 1):
                    curr_command_list.append(fisnar_commands[i])

                fisnar_commands = fisnar_commands[(output_0_comm_ind + 1):]  # removing part that was 'chopped'

                for i in (1, 2, 3, 4):  # appending output offs to end, to be safe
                    curr_command_list.append(["Output", i, 0])
                curr_command_list.append(["End Program"])

            else:  # at the last chunk, so just append the rest of the commands
                for i in range(len(fisnar_commands)):
                    curr_command_list.append(fisnar_commands[i])
                fisnar_commands = []  # resetting fisnar commands

            ret_command_lists.append(curr_command_list)

        return ret_command_lists
