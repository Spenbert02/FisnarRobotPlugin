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
  property bool parentEnabled: parent.enabled

  Behavior on opacity {
    NumberAnimation{ duration: 200; }
  }

  function show() {
    if (parentEnabled) {
      tooltipBaseRect.opacity = 1;
    }
  }

  function hide() {
    tooltipBaseRect.opacity = 0;
  }

  Rectangle {
    id: pointer
    property var sideLength: Math.round((UM.Theme.getSize("default_margin").width * 2) / (Math.pow(3, 0.5) * 2))

    anchors.left: parent.right
    anchors.verticalCenter: parent.verticalCenter
    height: 2 * sideLength
    width: UM.Theme.getSize("default_margin").width

    Canvas {
      anchors.fill: parent

      onPaint: {
        var context = getContext("2d");

        context.beginPath();
        context.moveTo(0, Math.round((parent.height / 2) - (parent.sideLength)));
        context.lineTo(Math.round((parent.sideLength * Math.pow(3, 0.5)) / 2), Math.round(parent.height / 2));
        context.lineTo(0, Math.round((parent.height / 2) + (parent.sideLength)));
        context.closePath();

        context.fillStyle = UM.Theme.getColor("tooltip");
        context.fill()
      }
    }
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
