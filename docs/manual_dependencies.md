# Manually included libraries
Any external libraries that are used in the plugin are included by manually
putting the library source code in the plugin's main directory. From here, python
files can import the libraries. This document describes the libraries that are
manually included in the plugin's main directory, and shows a dependency tree
for the dependencies of the python files and manually imported libraries in
this plugin, starting with the main file which is

## List of manually included libraries
[gcodeBuddy](https://github.com/Spenbert02/gcodeBuddy), [keyboard](https://github.com/boppreh/keyboard), [pyautogui](https://github.com/asweigart/pyautogui),
[PyGetWindow](https://github.com/asweigart/PyGetWindow), [pyperclip](https://github.com/asweigart/pyperclip), [PyRect](https://github.com/asweigart/PyRect)

## Dependency tree of python files and manually imported libraries
__init__.py  
|  
├─── FisnarCSVWriter.py  
|    ├─── AutoUploader.py  
|    |    ├─── pyautogui  
|    |    ├─── keyboard  
|    |    ├─── pyperclip  
|    |    └─── PyGetWindow  
|    |         └─── PyRect  
|    ├─── convert.py  
|    |    └─── gcodeBuddy  
|    └─── FisnarCSVParameterExtension.py  
|         ├─── pyperclip  
|         └─── AutoUploader.py  
|              ├─── pyautogui  
|              ├─── keyboard  
|              ├─── pyperclip  
|              └─── PyGetWindow  
|                   └─── PyRect  
└─── FisnarCSVParameterExtension.py  
     ├─── pyperclip  
     └─── AutoUploader.py  
          ├─── pyautogui  
          ├─── keyboard  
          ├─── pyperclip  
          └─── PyGetWindow  
               └─── PyRect  

## Importing manually included libraries
The technique for importing the manually included libraries is shown near the
top of the python files listed in the above section.
