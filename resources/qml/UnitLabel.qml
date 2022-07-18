import QtQuick 2.10
import QtQuick.Layouts 1.1
import QtQuick.Controls 2.15

import UM 1.5 as UM
import Cura 1.0 as Cura

Item {
  property var label: "mm"
  width: childrenRect.width
  height: childrenRect.height
  anchors.rightMargin: UM.Theme.getSize("setting_unit_margin").width

  UM.Label {
    text: parent.label
    font: UM.Theme.getFont("small")
    color: UM.Theme.getColor("setting_unit")
    height: UM.Theme.getSize("setting_control").height
    anchors {  // probably don't need this
      top: parent.top
      left: parent.left
    }
  }
}
