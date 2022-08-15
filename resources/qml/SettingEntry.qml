import QtQuick 2.10
import QtQuick.Layouts 1.1
import QtQuick.Controls 2.15

import UM 1.5 as UM
import Cura 1.0 as Cura

Rectangle {
  id: settingEntryBaseRect

  property var valId
  property var text
  property var label
  property var tooltipId

  // text validator
  property var bottomLim: 0.0
  property var topLim: 200.0
  property var validator: DoubleValidator {
    decimals: 3
    locale: "en_US"
    bottom: bottomLim
    top: topLim
  }

  width: UM.Theme.getSize("setting_control").width
  height: UM.Theme.getSize("setting_control").height
  radius: UM.Theme.getSize("setting_control_radius").width

  color: !enabled ? UM.Theme.getColor("setting_control_disabled") : "white"
  border.color: !enabled ? UM.Theme.getColor("setting_control_border") : (entryMouseArea.containsMouse ? UM.Theme.getColor("setting_control_border_highlight") : UM.Theme.getColor("setting_control_border"))

  MouseArea {
    id: entryMouseArea
    hoverEnabled: true
    anchors.fill: parent
    cursorShape: Qt.IBeamCursor

    onHoveredChanged: {
      if (containsMouse) {
        tooltip.show()
      } else {
        tooltip.hide()
      }
    }
  }

  TextInput {
    id: textEntry
    anchors.left: parent.left
    anchors.leftMargin: UM.Theme.getSize("setting_unit_margin").width
    anchors.right: unitLabel.right
    anchors.rightMargin: UM.Theme.getSize("setting_unit_margin").width
    anchors.verticalCenter: parent.verticalCenter
    text: parent.text
    color: parent.enabled ? UM.Theme.getColor("setting_control_text") : UM.Theme.getColor("setting_control_disabled_text")
    validator: parent.validator
    onEditingFinished: base.updateVal(parent.valId, text)
  }

  UnitLabel {
    id: unitLabel
    anchors.top: parent.top
    anchors.right: parent.right
    label: parent.label
  }

  DefineSetupTooltip {
    id: tooltip
    label: base.getTooltip(settingEntryBaseRect.tooltipId)
    anchors.right: parent.left
    anchors.rightMargin: UM.Theme.getSize("default_margin").width
    anchors.verticalCenter: parent.verticalCenter
  }
}
