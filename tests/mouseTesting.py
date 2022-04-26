# #  code to track mouse position (for testing)
# import pyautogui, sys
#
# try:
#     while True:
#         x, y = pyautogui.position()
#         pos_str = "(" + str(x) + ", " + str(y) + ")"
#         print(pos_str, end='')
#         print('\b' * len(pos_str), end='', flush=True)
# except KeyboardInterrupt:
#     print("\n")

import pygetwindow as gw
import pyautogui as pg
import time
import os


NEW_FILE_COORDS = (17, 65)
PASTE_BOX_COORDS = (289, 151)
UPLOAD_BOX_COORDS = (401, 68)
SMART_ROBOT_LOOKUP_NAME = "Smart Robot Edit"
CURA_LOOKUP_NAME = "Cura"


def autoUpload():
    pg.moveTo(NEW_FILE_COORDS[0], NEW_FILE_COORDS[1], 1)
    pg.moveTo(PASTE_BOX_COORDS[0], PASTE_BOX_COORDS[1], 1)
    pg.moveTo(UPLOAD_BOX_COORDS[0], UPLOAD_BOX_COORDS[1], 1)


smart_robot_windows = gw.getWindowsWithTitle(SMART_ROBOT_LOOKUP_NAME)
for i in range(len(smart_robot_windows)):
    if smart_robot_windows[i].width == 0 and smart_robot_windows[i].height == 0:
        print(smart_robot_windows[i].height, smart_robot_windows[i].width)

smart_robot_windows_2 = [i for i in smart_robot_windows if (i.height != 0 and i.size != 0)]
print(smart_robot_windows, smart_robot_windows_2)


# smart_robot_window = None
# if not smart_robot_windows:
#     print("not open")
#     os.startfile("C:\\Program Files (x86)\\SmartRotbotEdit\\Smart Robot Edit.exe")
#     smart_robot_windows = gw.getWindowsWithTitle(SMART_ROBOT_LOOKUP_NAME)
#     print(smart_robot_windows)
#
# smart_robot_window = smart_robot_windows[0]
# smart_robot_window.activate()
# time.sleep(2)
# if not smart_robot_window.isMaximized:
#     smart_robot_window.maximize()
# autoUpload()
