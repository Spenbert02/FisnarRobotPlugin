# Manually included libraries
Any external libraries that are used in the plugin are included by manually
putting the library source code in the plugin's main directory. They are then added
to the modules (manually) in each file where they need to be used. Below is a
tree showing which files depend on which manually imported libraries. Note: the
files noted below also depend on other libraries not shown - these are automatically
included with Cura, so their source code does not need to be manually included
in this plugin.

## List of manually included libraries
[gcodeBuddy](https://github.com/Spenbert02/gcodeBuddy), [keyboard](https://github.com/boppreh/keyboard), [pyautogui](https://github.com/asweigart/pyautogui),
[PyGetWindow](https://github.com/asweigart/PyGetWindow), [pyperclip](https://github.com/asweigart/pyperclip), [PyRect](https://github.com/asweigart/PyRect)

## Dependencies of manually included libraries on other manually included libraries
gcodeBuddy  
|---> None  

keyboard  
|---> None  

pyautogui  
|---> None  

PyGetWindow  
|---> PyRect  

pyperclip  
|---> None  

PyRect  
|---> None  

## Dependencies of each python file
AutoUploader.py  
|---> pyautogui  
|---> keyboard  
|---> pyperclip  

convert.py  
|---> None  

FisnarCSVParameterExtension.py  
|---> pyperclip  

FisnarCSVWriter.py  
|---> None  

## Importing manually included libraries
The technique for importing the manually included libraries is shown near the
top of the python files listed in the above section.
