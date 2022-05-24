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
This plugin was built for use with a Fisnar model F5200N, so the plugin will
save commands in a format that will be accepted by a Fisnar dispenser that
meets the following criteria:
- The build area is 200 x 200 [mm] in the x/y directions. This is critical,
because Cura's build plate coordinate system and the Fisnar coordinate system
are inverted. During the conversion process, all slicer output commands (gcode commands)
need to be flipped along the x and y directions before being translated into Fisnar
commands. The plugin assumes that the Fisnar has x/y dimensions of 200 x 200 [mm]
when it does this 'flipping'.
- The Fisnar must be using an output i/o card. This card forks the output
of the Fisnar using the i/o port, and allows for multiple dispensers to be
used. The Fisnar command system that is used looks very different depending
on whether or not the output i/o card is being used. This plugin assumes the
output i/o card __is__ being used, so as to support conversion of multiple
extruder prints. In the future, work may be done to add support for setups
that do not use the Fisnar i/o card. For reference, an image of a Fisnar i/o
card is shown below.

![](doc_pics/io_card.png)

- The Fisnar in use must be able to accept commands of the format described
[here](docs/conversion_algorithm.md# Conversion Algorithm ## Fisnar command system)

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
