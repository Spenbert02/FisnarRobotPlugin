import win32api
import win32gui

window = win32gui.GetActiveWindow()
dc = win32gui.GetDC(window)
color = win32gui.GetPixel(dc, 0, 0)
hex_color = hex(color)

print(hex_color)

hex_color = hex_color[2:]
rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
print("rgb", rgb, sep=": ")
