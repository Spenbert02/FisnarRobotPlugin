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
    height: getHeightFactor() * screenScaleFactor
    minimumHeight: getHeightFactor() * screenScaleFactor

    function getHeightFactor() {
      if (numExtruders == 1) {  // one extruder
        return 60;
      } else if (numExtruders == 2) {  // two extruders
        return 90;
      } else if (numExtruders == 3) {  // three extruders
        return 120;
      } else {  // four or more extruders
        return 150;
      }
    }

    onAfterAnimating: {
      numExtruders = main.getNumExtruders;
    }

    Label //Creates a bit of text.
    {
        id: introLabel
        //This aligns the text to the top-left corner of the dialogue window.
        anchors.top: base.top //Reference the dialogue window by its ID: "base".
        anchors.topMargin: 10 * screenScaleFactor
        anchors.left: base.left
        anchors.leftMargin: 10 * screenScaleFactor

        text: "Extruder-Output Correlation:"
        font.bold: true
    }

    Grid
    {
      id: extruderOutputGrid
      columns: 1
      spacing: 5 * screenScaleFactor

      anchors.top: introLabel.bottom
      anchors.topMargin: 10 * screenScaleFactor
      anchors.left: base.top
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
