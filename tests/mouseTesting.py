import pyautogui, sys

try:
    while True:
        x, y = pyautogui.position()
        pos_str = "(" + str(x) + ", " + str(y) + ")"
        print(pos_str, end='')
        print('\b' * len(pos_str), end='', flush=True)
except KeyboardInterrupt:
    print("\n")
