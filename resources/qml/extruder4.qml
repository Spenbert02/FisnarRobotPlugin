import UM 1.5 as UM
import QtQuick 2.15
import QtQuick.Controls 2.1
import Cura 1.1 as Cura

Grid {
  id: baseGrid
  columns: 2
  spacing: 5 * screenScaleFactor

  Label
  {
    id: extLabel
    text: "Extruder 4: Output"
    horizontalAlignment: Text.AlignRight
  }

  ComboBox {
    editable: false
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
