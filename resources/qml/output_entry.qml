import UM 1.5 as UM // This allows you to use all of Uranium's built-in QML items.
import QtQuick 2.2 // This allows you to use QtQuick's built-in QML items.
import QtQuick.Controls 1.1
import Cura 1.1 as Cura

UM.Dialog //Creates a modal window that pops up above the interface.
{
    id: base

    property int numExtruders: main.getNumExtruders

    width: 250 * screenScaleFactor
    minimumWidth: 250 * screenScaleFactor

    // one extruder
    height: (40 + getAdditionalHeightFactor()) * screenScaleFactor
    minimumHeight: (40 + getAdditionalHeightFactor()) * screenScaleFactor

    function getAdditionalHeightFactor() {  // function to get additional height factor
      return (numExtruders * 30 * screenScaleFactor)
    }

    onAfterAnimating: {
      numExtruders = main.getNumExtruders
    }

    Grid
    {
      id: checkboxTextGrid
      columns: 2
      spacing: 5 * screenScaleFactor
      anchors.top: base.top
      anchors.topMargin: 10 * screenScaleFactor
      anchors.left: base.left
      anchors.leftMargin: 10 * screenScaleFactor

      CheckBox
      {
        id: ioCheckbox
        text: "Convert for i/o card use"
        checked: true
        onClicked: {
          main.setOutputMode(checked)  // updating status in FisnarCSVParameterExtension
          // if (checked) {  // updating window height
          //   base.height = 100 + getAdditionalHeightFactor()
          // } else {
          //   base.height = 100
          // }
        }
      }
    }

    Grid
    {
      id: extruderOutputGrid
      columns: 1
      spacing: 5 * screenScaleFactor
      enabled: ioCheckbox.checked

      anchors.top: checkboxTextGrid.bottom
      anchors.topMargin: 10 * screenScaleFactor
      anchors.left: base.left
      anchors.leftMargin: 10 * screenScaleFactor

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
