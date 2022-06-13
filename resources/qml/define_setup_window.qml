import UM 1.5 as UM // This allows you to use all of Uranium's built-in QML items.
import QtQuick 2.2 // This allows you to use QtQuick's built-in QML items.
import QtQuick.Controls 1.1
import Cura 1.1 as Cura

UM.Dialog //Creates a modal window that pops up above the interface.
{
    id: base
    property int numExtruders: main.getNumExtruders

    width: 250 * screenScaleFactor
    height: (185 + getAdditionalHeightFactor()) * screenScaleFactor
    minimumWidth: 250 * screenScaleFactor
    minimumHeight: (185 + getAdditionalHeightFactor()) * screenScaleFactor

    onAfterAnimating: {  // updates the extruder numbers somewhat frequently - this should probably be set on a timer, but this works for now
      numExtruders = main.getNumExtruders
    }

    function getAdditionalHeightFactor() {  // function to get additional height factor
      return (numExtruders * 30)
    }

    Grid
    {
        columns: 1
        id: mainGrid
        spacing: (40 * screenScaleFactor) / 2

        anchors.top: base.top
        anchors.topMargin: 10 * screenScaleFactor
        anchors.left: base.left
        anchors.leftMargin: 10 * screenScaleFactor

        Grid
        {
          columns: 1
          spacing: (10 * screenScaleFactor) / 2
          id: leftColumn

          Label //Creates a bit of text.
          {
              id: introLabel
              text: "Fisnar Print Surface Definition:"
              font.bold: true
          }

          Grid
          {
            columns: 2
            spacing: (10 * screenScaleFactor) / 2

            // minimum x coordinate
            Label
            {
              text: "Minimum x-coordinate:"
              horizontalAlignment: Text.AlignRight
            }

            TextField
            {
              id: xMinTextField  // probably for reference within python?
              text: main.getXMin  // probably for reference somewhere, idk where

              width: 100

              validator: DoubleValidator {  // ensures entry is in the right format, idk exactly how this works
                decimals: 4
                locale: "en_US"
                bottom: 0
                top: 200
              }

              onEditingFinished: {  // called when return or enter is pressed or when text entry box loses focus
                main.setCoord("fisnar_x_min", xMinTextField.text)
              }
            }

            // maximum x coordinate
            Label
            {
              text: "Maximum x-coordinate:"
              horizontalAlignment: Text.AlignRight
            }

            TextField
            {
              id: xMaxTextField  // probably for reference within python?
              text: main.getXMax  // probably for reference somewhere, idk where

              width: 100

              validator: DoubleValidator {  // ensures entry is in the right format, idk exactly how this works
                decimals: 4
                locale: "en_US"
                bottom: 0
                top: 200
              }

              onEditingFinished: {  // called when return or enter is pressed or when text entry box loses focus
                main.setCoord("fisnar_x_max", xMaxTextField.text)
              }
            }

            // minimum y coordinate
            Label
            {
              text: "Minimum y-coordinate:"
              horizontalAlignment: Text.AlignRight
            }

            TextField
            {
              id: yMinTextField  // probably for reference within python?
              text: main.getYMin  // probably for reference somewhere, idk where

              width: 100

              validator: DoubleValidator {  // ensures entry is in the right format, idk exactly how this works
                decimals: 4
                locale: "en_US"
                bottom: 0
                top: 200
              }

              onEditingFinished: {  // called when return or enter is pressed or when text entry box loses focus
                main.setCoord("fisnar_y_min", yMinTextField.text)
              }
            }


            // maximum y coordinate
            Label
            {
              text: "Maximum y-coordinate:"
              horizontalAlignment: Text.AlignRight
            }

            TextField
            {
              id: yMaxTextField  // probably for reference within python?
              text: main.getYMax  // probably for reference somewhere, idk where

              width: 100

              validator: DoubleValidator {  // ensures entry is in the right format, idk exactly how this works
                decimals: 4
                locale: "en_US"
                bottom: 0
                top: 200
              }

              onEditingFinished: {  // called when return or enter is pressed or when text entry box loses focus
                main.setCoord("fisnar_y_max", yMaxTextField.text)
              }
            }


            // maximum z coordinate
            Label
            {
              text: "Maximum z-coordinate:"
              horizontalAlignment: Text.AlignRight
            }

            TextField
            {
              id: zMaxTextField  // probably for reference within python?
              text: main.getZMax  // probably for reference somewhere, idk where

              width: 100

              validator: DoubleValidator {  // ensures entry is in the right format, idk exactly how this works
                decimals: 4
                locale: "en_US"
                bottom: 0
                top: 150
              }

              onEditingFinished: {  // called when return or enter is pressed or when text entry box loses focus
                main.setCoord("fisnar_z_max", zMaxTextField.text)
              }
            }
          }
        }

        Grid
        {
          id: rightColumn
          columns: 1
          spacing: (10 * screenScaleFactor) / 2

          Label
          {
            text: "Extruder-Output Assignments:"
            font.bold: true
          }

          Grid
          {
            id: extruderOutputGrid
            columns: 1
            spacing: 5 * screenScaleFactor

            Loader {  // extruder 1
              id: extruder1Entry
              source: (base.numExtruders >= 1) ? "extruder1.qml" : "dummyItem.qml"
            }

            Loader {  // extruder 2
              id: extruder2Entry
              source: (base.numExtruders >= 2) ? "extruder2.qml" : "dummyItem.qml"
            }

            Loader {  // extruder 3
              id: extruder3Entry
              source: (base.numExtruders >= 3) ? "extruder3.qml" : "dummyItem.qml"
            }

            Loader {  // extruder 4
              id: extruder4Entry
              source: (base.numExtruders >= 4) ? "extruder4.qml" : "dummyItem.qml"
            }

          }
        }
    }
}
