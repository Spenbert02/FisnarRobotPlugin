import UM 1.5 as UM // This allows you to use all of Uranium's built-in QML items.
import QtQuick 2.2 // This allows you to use QtQuick's built-in QML items.
import QtQuick.Controls 1.1
import Cura 1.1 as Cura

UM.Dialog //Creates a modal window that pops up above the interface.
{
    id: base

    width: 250 * screenScaleFactor
    height: 155 * screenScaleFactor
    minimumWidth: 250 * screenScaleFactor
    minimumHeight: 155 * screenScaleFactor

    Label //Creates a bit of text.
    {
        id: introLabel
        //This aligns the text to the top-left corner of the dialogue window.
        anchors.top: base.top //Reference the dialogue window by its ID: "base".
        anchors.topMargin: 10 * screenScaleFactor
        anchors.left: base.left
        anchors.leftMargin: 10 * screenScaleFactor

        text: "Fisnar Print Surface Information:"
        font.bold: true
    }

    Grid
    {
      anchors.top: introLabel.bottom
      anchors.topMargin: 10 * screenScaleFactor
      anchors.left: base.left
      anchors.leftMargin: 10 * screenScaleFactor

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

        width: 200

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

        width: 200

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

        width: 200

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

        width: 200

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

        width: 200

        validator: DoubleValidator {  // ensures entry is in the right format, idk exactly how this works
          decimals: 4
          locale: "en_US"
          bottom: 0
          top: 200
        }

        onEditingFinished: {  // called when return or enter is pressed or when text entry box loses focus
          main.setCoord("fisnar_z_max", zMaxTextField.text)
        }
      }

    }
}
