import UM 1.5 as UM
import QtQuick 2.15
import QtQuick.Controls 2.1
import Cura 1.1 as Cura

UM.Dialog {
    id: base
    title: "Fisnar Setup"

    property int numExtruders: main.getNumExtruders

    width: minimumWidth
    height: minimumHeight
    minimumWidth: 645 * screenScaleFactor
    minimumHeight: 235 * screenScaleFactor

    onAfterAnimating: {  // updates the extruder numbers somewhat frequently - this should probably be set on a timer, but this works for now
      numExtruders = main.getNumExtruders
    }

    Row {
      anchors.top: parent.top
      anchors.left: parent.left
      height: parent.height
      width: parent.width
      spacing: UM.Theme.getSize("default_margin").width

      GroupBox {  // print surface box
        title: "Print Surface"
        width: 200 * screenScaleFactor
        height: Math.round(parent.height)

        Grid {  //
          columns: 2
          spacing: UM.Theme.getSize("default_margin").height
          height: parent.height
          width: parent.width
          anchors.top: parent.top
          anchors.horizontalCenter: parent.horizontalCenter

          Label {  // x-min label/text input
            text: "x-minimum"
            horizontalAlignment: Text.AlignRight
            verticalAlignment: Text.AlignVCenter
          }
          TextField {
            id: xMinEntry
            width: 100
            text: main.getXMin
            validator: DoubleValidator {
              decimals: 4
              locale: "en_US"
              bottom: 0
              top: 200
            }
            onEditingFinished: {
              main.setCoord("fisnar_x_min", text)
            }
          }

          Label {  // x-max label/text input
            text: "x-maximum"
            horizontalAlignment: Text.AlignRight
            verticalAlignment: Text.AlignVCenter
          }
          TextField {
            id: xMaxEntry
            width: 100
            text: main.getXMax
            validator: DoubleValidator {
              decimals: 4
              locale: "en_US"
              bottom: 0
              top: 200
            }
            onEditingFinished: {
              main.setCoord("fisnar_x_max", text)
            }
          }

          Label {  // y-min label/text input
            text: "y-minimum"
            horizontalAlignment: Text.AlignRight
            verticalAlignment: Text.AlignVCenter
          }
          TextField {
            id: yMinEntry
            width: 100
            text: main.getYMin
            validator: DoubleValidator {
              decimals: 4
              locale: "en_US"
              bottom: 0
              top: 200
            }
            onEditingFinished: {
              main.setCoord("fisnar_y_min", text)
            }
          }

          Label {  // y-max label/text input
            text: "y-maximum"
            horizontalAlignment: Text.AlignRight
            verticalAlignment: Text.AlignVCenter
          }
          TextField {
            id: yMaxEntry
            width: 100
            text: main.getYMax
            validator: DoubleValidator {
              decimals: 4
              locale: "en_US"
              bottom: 0
              top: 200
            }
            onEditingFinished: {
              main.setCoord("fisnar_y_max", text)
            }
          }

          Label {  // z-max label/text input
            text: "z-maximum"
            horizontalAlignment: Text.AlignRight
            verticalAlignment: Text.AlignVCenter
          }
          TextField {
            id: zMaxEntry
            width: 100
            text: main.getZMax
            validator: DoubleValidator {
              decimals: 4
              locale: "en_US"
              bottom: 0
              top: 200
            }
            onEditingFinished: {
              main.setCoord("fisnar_z_max", text)
            }
          }
        }
      }

      GroupBox {  // group box for extruder output correlations
        title: "Extruder Outputs"
        width: 200 * screenScaleFactor
        height: Math.round(parent.height)

        Grid {
          columns: 2
          spacing: UM.Theme.getSize("default_margin").height
          height: parent.height
          width: parent.width
          anchors.top: parent.top
          anchors.horizontalCenter: parent.horizontalCenter

          Label {  // extruder 1 output entry
            enabled: base.numExtruders >= 1
            text: "Extruder 1: Output"
            horizontalAlignment: Text.AlignRight
          }
          ComboBox {
            currentIndex: main.getExt1OutputInd
            enabled: base.numExtruders >= 1
            editable: false
            width: 70 * screenScaleFactor
            model: ListModel {
              id: ext1List
              ListElement {text: "None"}
              ListElement {text: "1"}
              ListElement {text: "2"}
              ListElement {text: "3"}
              ListElement {text: "4"}
            }
            onCurrentIndexChanged: {
              main.setExtruderOutput("1", ext1List.get(currentIndex).text)
            }
          }

          Label {  // extruder 2 output entry
            enabled: base.numExtruders >= 2
            text: "Extruder 2: Output"
            horizontalAlignment: Text.AlignRight
          }
          ComboBox {
            currentIndex: main.getExt2OutputInd
            enabled: base.numExtruders >= 2
            editable: false
            width: 70 * screenScaleFactor
            model: ListModel {
              id: ext2List
              ListElement {text: "None"}
              ListElement {text: "1"}
              ListElement {text: "2"}
              ListElement {text: "3"}
              ListElement {text: "4"}
            }
            onCurrentIndexChanged: {
              main.setExtruderOutput("2", ext2List.get(currentIndex).text)
            }
          }

          Label {  // extruder 3 output entry
            enabled: base.numExtruders >= 3
            text: "Extruder 3: Output"
            horizontalAlignment: Text.AlignRight
          }
          ComboBox {
            currentIndex: main.getExt3OutputInd
            enabled: base.numExtruders >= 3
            editable: false
            width: 70 * screenScaleFactor
            model: ListModel {
              id: ext3List
              ListElement {text: "None"}
              ListElement {text: "1"}
              ListElement {text: "2"}
              ListElement {text: "3"}
              ListElement {text: "4"}
            }
            onCurrentIndexChanged: {
              main.setExtruderOutput("3", ext3List.get(currentIndex).text)
            }
          }

          Label {  // extruder 4 output entry
            enabled: base.numExtruders >= 4
            text: "Extruder 4: Output"
            horizontalAlignment: Text.AlignRight
          }
          ComboBox {
            currentIndex: main.getExt4OutputInd
            enabled: base.numExtruders >= 4
            editable: false
            width: 70 * screenScaleFactor
            model: ListModel {
              id: ext4List
              ListElement {text: "None"}
              ListElement {text: "1"}
              ListElement {text: "2"}
              ListElement {text: "3"}
              ListElement {text: "4"}
            }
            onCurrentIndexChanged: {
              main.setExtruderOutput("4", ext4List.get(currentIndex).text)
            }
          }
        }
      }

      GroupBox {  // groupbox for com port
        title: "COM Ports"
        width: 200 * screenScaleFactor
        height: Math.round(parent.height)

        Grid {  // grid for com port entries
          columns: 2
          spacing: UM.Theme.getSize("default_margin").height
          height: parent.height
          width: parent.width
          anchors.top: parent.top
          anchors.horizontalCenter: parent.horizontalCenter

          Label {  // fisnar com port label/input
            text: "Fisnar"
            horizontalAlignment: Text.AlignRight
            verticalAlignment: Text.AlignVCenter
          }
          TextField {
            id: fisnarComEntry
            width: 100
            text: main.getComPort
            onEditingFinished: {
              main.setComPort(text)
            }
          }
        }
      }
    }
}
