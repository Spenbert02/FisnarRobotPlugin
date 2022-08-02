import QtQuick 2.10
import QtQuick.Layouts 1.1
import QtQuick.Controls 2.15
import QtQuick.Shapes 1.3

import UM 1.5 as UM
import Cura 1.0 as Cura

Rectangle {
  id: tooltipBaseRect
  property var label: "<none>"

  width: Math.round(UM.Theme.getSize("tooltip").width / 2)
  height: tooltipText.height + (2 * UM.Theme.getSize("thin_margin").height)
  color: UM.Theme.getColor("tooltip")

  opacity: 0
  enabled: opacity > 0

  Behavior on opacity {
    NumberAnimation{ duration: 200; }
  }

  function show() {
    tooltipBaseRect.opacity = 1;
  }

  function hide() {
    tooltipBaseRect.opacity = 0;
  }

  UM.Label {
    id: tooltipText
    text: parent.label
    color: UM.Theme.getColor("tooltip_text")
    width: parent.width - (2 * UM.Theme.getSize("thin_margin").width)
    anchors.verticalCenter: parent.verticalCenter
    anchors.horizontalCenter: parent.horizontalCenter
  }
}
