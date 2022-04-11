import UM 1.5 as UM // This allows you to use all of Uranium's built-in QML items.
import QtQuick 2.2 // This allows you to use QtQuick's built-in QML items.
import QtQuick.Controls 1.1
import Cura 1.1 as Cura

Grid {

  columns: 2
  spacing: 5 * screenScaleFactor

  Label
  {
    text: "Extruder 1 Output:"
    horizontalAlignment: Text.AlignRight
  }

  TextField
  {
    id: extruder1Output  // probably for reference within python?
    text: main.getExtruder1Output  // probably for reference somewhere, idk where

    width: 100

    validator: IntValidator {  // ensures entry is in the right format, idk exactly how this works
      bottom: 1
      top: 4
    }

    onEditingFinished: {  // called when return or enter is pressed or when text entry box loses focus
      main.setExtruderOutput("extruder_1_output", extruder1Output.text)
    }
  }
}
