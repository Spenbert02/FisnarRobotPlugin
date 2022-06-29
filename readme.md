# FisnarRobotPlugin
Fisnar Robot Plugin adds the Fisnar F5200N dispensing robot to Cura,
allows slicer output to be saved in the Fisnar command .csv format, and
enables 'USB' printing using the F5200N's RS232 port.

# Table of Contents

## Introduction
FisnarRobotPlugin is a plugin for [Ultimaker Cura](https://ultimaker.com/software/ultimaker-cura) version 5.0.0+. Broadly speaking, it makes the Fisnar F5200N
robot compatible with Cura. This plugin contains the necessary files to add
the Fisnar F5200N printer to Cura and enables exporting slicer output in the
Fisnar .csv format. Additionally, this plugin allows the user to print
with the Fisnar F5200N over the RS232 port, which eliminates any command limit
issues sometimes seen with Fisnar's proprietary command upload software ('Smart
Robot Edit').

A lot of this plugin was written using other existing plugins as guides. This
includes Ultimaker's [GCodeWriter](https://github.com/Ultimaker/Cura/tree/main/plugins/GCodeWriter) plugin and Tim Schoenmackers' [Dremel Printer](https://github.com/timmehtimmeh/Cura-Dremel-Printer-Plugin) plugin.

If you find any bugs/issues or have suggestions for the plugin, contact me
using the info below or use one of the GitHub communication features.

Lastly, the development of this plugin was funded by the [McAlpine Research
Group](https://sites.google.com/view/mcalpineresearchgroup/home) at the University of Minnesota.

## Installation and Initial Setup
This plugin has been submitted to the [Ultimaker Marketplace](https://marketplace.ultimaker.com/app/cura/plugins) and as of now (6/29/2022) it is under review. Until it is accepted, the only way to install it is by packaging it
from source. Instructions to do so can be found [here](https://community.ultimaker.com/topic/26046-writing-a-custom-cura-package/).

Once the plugin is accepted, a more user-friendly description of how to download
it will be provided.

## Usage

### Necessary Physical Printer Configuration
In order to use the plugin, the Fisnar F5200N in use needs to be using an
i/o card to control its outputs. This i/o card can be purchased from Fisnar,
and is pictured below.

![i/o card diagram from Fisnar F5200N manual](docs/doc_pics/io_card_2.png)

![](docs/doc_pics/io_card_setup_marked.jpg)

### Entering Setup Information

### Saving Output to CSV

### Printing Over RS232 Port

## Technical Details

### Fisnar CSV Format

## Contact
