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
    minimumWidth: 430 * screenScaleFactor
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
    }


    /* below this is old code */

    // Grid
    // {
    //     columns: 1
    //     id: mainGrid
    //     spacing: (40 * screenScaleFactor) / 2
    //
    //     anchors.top: base.top
    //     anchors.topMargin: 10 * screenScaleFactor
    //     anchors.left: base.left
    //     anchors.leftMargin: 10 * screenScaleFactor
    //
    //     Grid
    //     {
    //       columns: 1
    //       spacing: (10 * screenScaleFactor) / 2
    //       id: leftColumn
    //
    //       Label //Creates a bit of text.
    //       {
    //           id: introLabel
    //           text: "Fisnar Print Surface Definition:"
    //           font.bold: true
    //       }
    //
    //       Grid
    //       {
    //         columns: 2
    //         spacing: (10 * screenScaleFactor) / 2
    //
    //         // minimum x coordinate
    //         Label
    //         {
    //           text: "Minimum x-coordinate:"
    //           horizontalAlignment: Text.AlignRight
    //         }
    //
    //         TextField
    //         {
    //           id: xMinTextField  // probably for reference within python?
    //           text: main.getXMin  // probably for reference somewhere, idk where
    //
    //           width: 100
    //
    //           validator: DoubleValidator {  // ensures entry is in the right format, idk exactly how this works
    //             decimals: 4
    //             locale: "en_US"
    //             bottom: 0
    //             top: 200
    //           }
    //
    //           onEditingFinished: {  // called when return or enter is pressed or when text entry box loses focus
    //             main.setCoord("fisnar_x_min", xMinTextField.text)
    //           }
    //         }
    //
    //         // maximum x coordinate
    //         Label
    //         {
    //           text: "Maximum x-coordinate:"
    //           horizontalAlignment: Text.AlignRight
    //         }
    //
    //         TextField
    //         {
    //           id: xMaxTextField  // probably for reference within python?
    //           text: main.getXMax  // probably for reference somewhere, idk where
    //
    //           width: 100
    //
    //           validator: DoubleValidator {  // ensures entry is in the right format, idk exactly how this works
    //             decimals: 4
    //             locale: "en_US"
    //             bottom: 0
    //             top: 200
    //           }
    //
    //           onEditingFinished: {  // called when return or enter is pressed or when text entry box loses focus
    //             main.setCoord("fisnar_x_max", xMaxTextField.text)
    //           }
    //         }
    //
    //         // minimum y coordinate
    //         Label
    //         {
    //           text: "Minimum y-coordinate:"
    //           horizontalAlignment: Text.AlignRight
    //         }
    //
    //         TextField
    //         {
    //           id: yMinTextField  // probably for reference within python?
    //           text: main.getYMin  // probably for reference somewhere, idk where
    //
    //           width: 100
    //
    //           validator: DoubleValidator {  // ensures entry is in the right format, idk exactly how this works
    //             decimals: 4
    //             locale: "en_US"
    //             bottom: 0
    //             top: 200
    //           }
    //
    //           onEditingFinished: {  // called when return or enter is pressed or when text entry box loses focus
    //             main.setCoord("fisnar_y_min", yMinTextField.text)
    //           }
    //         }
    //
    //
    //         // maximum y coordinate
    //         Label
    //         {
    //           text: "Maximum y-coordinate:"
    //           horizontalAlignment: Text.AlignRight
    //         }
    //
    //         TextField
    //         {
    //           id: yMaxTextField  // probably for reference within python?
    //           text: main.getYMax  // probably for reference somewhere, idk where
    //
    //           width: 100
    //
    //           validator: DoubleValidator {  // ensures entry is in the right format, idk exactly how this works
    //             decimals: 4
    //             locale: "en_US"
    //             bottom: 0
    //             top: 200
    //           }
    //
    //           onEditingFinished: {  // called when return or enter is pressed or when text entry box loses focus
    //             main.setCoord("fisnar_y_max", yMaxTextField.text)
    //           }
    //         }
    //
    //
    //         // maximum z coordinate
    //         Label
    //         {
    //           text: "Maximum z-coordinate:"
    //           horizontalAlignment: Text.AlignRight
    //         }
    //
    //         TextField
    //         {
    //           id: zMaxTextField  // probably for reference within python?
    //           text: main.getZMax  // probably for reference somewhere, idk where
    //
    //           width: 100
    //
    //           validator: DoubleValidator {  // ensures entry is in the right format, idk exactly how this works
    //             decimals: 4
    //             locale: "en_US"
    //             bottom: 0
    //             top: 150
    //           }
    //
    //           onEditingFinished: {  // called when return or enter is pressed or when text entry box loses focus
    //             main.setCoord("fisnar_z_max", zMaxTextField.text)
    //           }
    //         }
    //       }
    //     }
    //
    //     Grid
    //     {
    //       id: rightColumn
    //       columns: 1
    //       spacing: (10 * screenScaleFactor) / 2
    //
    //       Label
    //       {
    //         text: "Extruder-Output Assignments:"
    //         font.bold: true
    //       }
    //
    //       Grid
    //       {
    //         id: extruderOutputGrid
    //         columns: 1
    //         spacing: 5 * screenScaleFactor
    //
    //         Loader {  // extruder 1
    //           id: extruder1Entry
    //           source: (base.numExtruders >= 1) ? "extruder1.qml" : "dummyItem.qml"
    //         }
    //
    //         Loader {  // extruder 2
    //           id: extruder2Entry
    //           source: (base.numExtruders >= 2) ? "extruder2.qml" : "dummyItem.qml"
    //         }
    //
    //         Loader {  // extruder 3
    //           id: extruder3Entry
    //           source: (base.numExtruders >= 3) ? "extruder3.qml" : "dummyItem.qml"
    //         }
    //
    //         Loader {  // extruder 4
    //           id: extruder4Entry
    //           source: (base.numExtruders >= 4) ? "extruder4.qml" : "dummyItem.qml"
    //         }
    //
    //       }
    //     }
    // }
}
