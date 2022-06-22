# Repository overview
This document describes the overall structure of this repository, as well as
what is contained in different folders/files.

## Documentation
In the 'docs' folder resides this and all other documentation files. These
documentation files describe how the plugin works and the different files
that make it up.

## External libraries
The main repository level contains folders of several external libraries. These
libraries are depended upon by other parts of the plugin (or sometimes each other),
so their source code is included here for easy access. More information on these
external libraries and the dependencies of different areas of the plugin, see
the documentation on [manual dependencies](manual_dependencies.md).

## Resources
The 'resources' folder contains the QML files that are used in the UI design
of the plugin. There is also an 'images' subfolder here, which contains images
of different icons on the computer connected to the Fisnar in the 3D Printing Lab.
These images were going to be used by an autoclicker in the auto-upload process,
but an easier way was found (using PyGetWindow), so these images don't really
serve a purpose.

## Tests
The 'tests' folder contains python files that are used for different experimentation
purposes, except for the zipper.py file, which serves a purpose in the development process (described below). They are not unit tests, and do not verify the functionality of any
part of the plugin.

### zipper.py
zipper.py is a python script that automatically places all of the necessary
files from a certain directory into a zip file. This is useful for the packaging
process - [Ultimaker's Contributor Portal](https://contribute.ultimaker.com/app/developer/plugins)
requires a zip file with a single folder in it to be uploaded, and this script can be used
during the development process to generate this zip file.

## GitHub logistics
The following files are 'logistical' files for aiding in the push/pull process
and for the display of this GitHub repository: .gitignore, readme.md

.gitignore basically tells git to skip over certain files when pushing an update,
and readme.md provides the main documentation at the home page of this repository.

## Actual source code
The actual source code of this project lies in the following files (plus the QML
folder described above): \_\_init\_\_.py, plugin.json, AutoUploader.py, convert.py,
FisnarRobotExtension.py, FisnarCSVWriter.py

\_\_init\_\_.py, plugin.json, FisnarCSVWriter.py, and FisnarRobotExtension.py
are described in the [flow of control](flow_of_control.md) documentation, AutoUploader.py
is described in the [functional_classes](functional_classes.md) documentation, and convert.py
is described in the [conversion algorithm](conversion_algorithm.md) documentation.
