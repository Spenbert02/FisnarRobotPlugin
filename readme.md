# README
FisnarCSVWriter is a plugin for Utlimaker's [Cura](https://github.com/Ultimaker/Cura) slicer software that adds functionality for printing
CAD files with Fisnar dispensing robots. It is still in development and this
page will be updated regularly.

## Fisnar Robots
Fisnar dispensing robots are used extensively in industry to automate fluid
dispensing processes. These robots also function well as direct-ink-writing
3D printers for additive manufacturing at the micro to meso-scale. Fisnar dispensing robots
do not come with support for printing CAD files, however. Their command language
is unique and is not supported by any reliable slicer software. This plugin
solves this issue, by allowing the output of Cura's slicing algorithm to be
saved as a CSV file of Fisnar commands, that can be uploaded to a Fisnar
printer for fabrication.

## Caveats
- This plugin was built for use with a Fisnar model F5200N, so the plugin will
output commands that will work for a Fisnar that meets the following criteria:
  - test

## Downloading
The easiest way to download the plugin will be to download it from Ultimaker's
[plugin marketplace](https://marketplace.ultimaker.com/app/cura/plugins). This
plugin isn't published there yet, but once it is it can be found by searching
'FisnarCSVWriter' on the plugin marketplace page.

To download the version specifically for the Fisnar in the 3D Printing
Functional Materials and Devices Lab, see the 'McAlpine_lab_packaged_plugin'
directory. In there is a file that can be drag and dropped into Cura
for installation. This version of the plugin includes the 'auto-upload'
functionality.
