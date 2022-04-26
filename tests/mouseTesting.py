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
import time

excel_windows = gw.getWindowsWithTitle("Excel")
if excel_windows is None:
    pass  # open excel, then call again

print(ret_val)
excel = ret_val[0]
excel.activate()

time.sleep(2)

if not excel.isMaximized:
    excel.maximize()
