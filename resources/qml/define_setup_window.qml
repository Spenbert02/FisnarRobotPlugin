import QtQuick 2.10
import QtQuick.Layouts 1.1
import QtQuick.Controls 2.15

import UM 1.5 as UM
import Cura 1.0 as Cura

import "."

UM.Dialog {
    id: base
    title: "Fisnar Setup"

    property int numExtruders: main.num_extruders
    property bool fisnarConnected: main.fisnar_connection_state
    property bool dispenserConnected: main.dispenser_connection_state

    width: minimumWidth
    height: minimumHeight
    minimumWidth: 1000 * screenScaleFactor
    minimumHeight: 350 * screenScaleFactor

    function updateVal(valId, val) {
      if (valId.includes("fisnar")) {
        main.setCoord(valId, val);
      } else if (valId == "com_port") {
        main.updateComPort(val);
      } else if (valId == "dispenser_com_port") {
        main.updateDispenserSerialPort(val);
      }
    }

    Row {
      id: sectionRow
      height: parent.height - (2 * UM.Theme.getSize("default_margin").height)
      width: parent.width - (2 * UM.Theme.getSize("default_margin").width)
      anchors.top: parent.top
      anchors.topMargin: UM.Theme.getSize("default_margin").height
      anchors.left: parent.left
      anchors.leftMargin: UM.Theme.getSize("default_margin").width
      spacing: UM.Theme.getSize("thick_margin").width

      // function showTooltip(item, position, text) {
      //   tooltip.text = text;
      //   position = item.mapToItem(sectionRow, position.x - UM.Theme.getSize("default_arrow").width, position.y);
      //   tooltip.show(position);
      // }
      //
      // function hideTooltip() {
      //   tooltip.hide();
      // }

      GroupBox {
        id: printSurfaceBox
        title: "Print Surface"
        width: 0.3333 * (parent.width - (2 * parent.spacing))
        anchors.top: parent.top
        anchors.bottom: parent.bottom

        Rectangle {
          anchors.fill: parent

          UM.Label {  // x-range label
            id: xRangeLabel
            text: "X Range"
            font: UM.Theme.getFont("default")
            height: UM.Theme.getSize("setting_control").height
            anchors.left: parent.left
            anchors.top: parent.top
          }

          UM.Label {  // x min label
            id: xMinLabel
            text: "Min"
            font: UM.Theme.getFont("default_bold")
            height: UM.Theme.getSize("setting_control").height
            anchors.right: xMinEntry.left
            anchors.rightMargin: UM.Theme.getSize("default_margin").width
            anchors.top: xRangeLabel.top
          }

          SettingEntry {  // x min text entry
            id: xMinEntry
            anchors.top: xMinLabel.top
            anchors.right: parent.right
            text: main.x_min
            valId: "fisnar_x_min"
            label: "mm"
          }

          UM.Label {  // x-max label
            id: xMaxLabel
            text: "Max"
            font: UM.Theme.getFont("default_bold")
            height: UM.Theme.getSize("setting_control").height
            anchors.right: xMaxEntry.left
            anchors.rightMargin: UM.Theme.getSize("default_margin").width
            anchors.top: xMinLabel.bottom
            anchors.topMargin: UM.Theme.getSize("default_lining").height
          }

          SettingEntry {
            id: xMaxEntry
            anchors.top: xMaxLabel.top
            anchors.right: parent.right
            text: main.x_max
            valId: "fisnar_x_max"
            label: "mm"
          }

          UM.Label {  // y range label
            id: yRangeLabel
            text: "Y Range"
            font: UM.Theme.getFont("default")
            height: UM.Theme.getSize("setting_control").height
            anchors.left: parent.left
            anchors.top: xMaxLabel.bottom
            anchors.topMargin: UM.Theme.getSize("default_margin").height
          }

          UM.Label {  // y min label
            id: yMinLabel
            text: "Min"
            font: UM.Theme.getFont("default_bold")
            height: UM.Theme.getSize("setting_control").height
            anchors.right: yMinEntry.left
            anchors.rightMargin: UM.Theme.getSize("default_margin").width
            anchors.top: yRangeLabel.top
          }

          SettingEntry {
            id: yMinEntry
            anchors.top: yMinLabel.top
            anchors.right: parent.right
            text: main.y_min
            valId: "fisnar_y_min"
            label: "mm"
          }

          UM.Label {  // y max label
            id: yMaxLabel
            font: UM.Theme.getFont("default_bold")
            height: UM.Theme.getSize("setting_control").height
            text: "Max"
            anchors.right: yMaxEntry.left
            anchors.rightMargin: UM.Theme.getSize("default_margin").width
            anchors.top: yMinLabel.bottom
            anchors.topMargin: UM.Theme.getSize("default_lining").height
          }

          SettingEntry {
            id: yMaxEntry
            anchors.right: parent.right
            anchors.top: yMaxLabel.top
            text: main.y_max
            valId: "fisnar_y_max"
            label: "mm"
          }

          UM.Label {  // z range label
            id: zRangeLabel
            text: "Z Range"
            font: UM.Theme.getFont("default")
            height: UM.Theme.getSize("setting_control").height
            anchors.left: parent.left
            anchors.top: yMaxLabel.bottom
            anchors.topMargin: UM.Theme.getSize("default_margin").height
          }

          UM.Label {  // z min label
            id: zMinLabel
            text: "Min"
            font: UM.Theme.getFont("default_bold")
            height: UM.Theme.getSize("setting_control").height
            anchors.top: zRangeLabel.top
            anchors.right: zMinEntry.left
            anchors.rightMargin: UM.Theme.getSize("default_margin").width
          }

          SettingEntry {
            id: zMinEntry
            enabled: false
            anchors.right: parent.right
            anchors.top: zMinLabel.top
            text: "0.0"
            valId: "<none>"
            label: "mm"
          }

          UM.Label {  // z max label
            id: zMaxLabel
            text: "Max"
            font: UM.Theme.getFont("default_bold")
            height: UM.Theme.getSize("setting_control").height
            anchors.top: zMinLabel.bottom
            anchors.topMargin: UM.Theme.getSize("default_lining").height
            anchors.right: zMaxEntry.left
            anchors.rightMargin: UM.Theme.getSize("default_margin").width
          }

          SettingEntry {
            id: zMaxEntry
            anchors.right: parent.right
            anchors.top: zMaxLabel.top
            text: main.z_max
            valId: "fisnar_z_max"
            label: "mm"
          }
        }
      }

      GroupBox {  // extruder output correlation group box
        title: "Extruder Outputs"
        width: 0.3333 * (parent.width - (2 * parent.spacing))
        anchors.top: parent.top
        anchors.bottom: parent.bottom

        Rectangle {
          anchors.fill: parent

          ListModel {  // extruder output model
            id: outputsModel
            ListElement{label: "None"; value: 0}
            ListElement{label: "Output 1"; value: 1}
            ListElement{label: "Output 2"; value: 2}
            ListElement{label: "Output 3"; value: 3}
            ListElement{label: "Output 4"; value: 4}
          }

          UM.Label {  // extruder 1 label
            id: ext1Label
            enabled: base.numExtruders >= 1
            text: "Extruder 1"
            font: UM.Theme.getFont("default")
            height: UM.Theme.getSize("setting_control").height
            anchors.left: parent.left
            anchors.top: parent.top
          }

          ComboBox {  // extruder 1 dropdown
            id: ext1Dropdown
            enabled: base.numExtruders >= 1
            width: UM.Theme.getSize("setting_control").width
            height: UM.Theme.getSize("setting_control").height
            anchors.right: parent.right
            anchors.top: ext1Label.top

            model: outputsModel
            textRole: "label"
            currentIndex: main.ext_1_output_ind
            onCurrentIndexChanged: {
              main.setExtruderOutput(1, currentIndex)
            }
          }

          UM.Label {  // extruder 2 label
            id: ext2Label
            enabled: base.numExtruders >= 2
            text: "Extruder 2"
            font: UM.Theme.getFont("default")
            height: UM.Theme.getSize("setting_control").height
            anchors.left: parent.left
            anchors.top: ext1Label.bottom
            anchors.topMargin: UM.Theme.getSize("default_margin").height
          }

          ComboBox {  // extruder 2 dropdown
            id: ext2Dropdown
            enabled: base.numExtruders >= 2
            width: UM.Theme.getSize("setting_control").width
            height: UM.Theme.getSize("setting_control").height
            anchors.right: parent.right
            anchors.top: ext2Label.top

            model: outputsModel
            textRole: "label"
            currentIndex: main.ext_2_output_ind
            onCurrentIndexChanged: {
              main.setExtruderOutput(2, currentIndex)
            }
          }

          UM.Label {  // extruder 3 label
            id: ext3Label
            enabled: base.numExtruders >= 3
            text: "Extruder 3"
            font: UM.Theme.getFont("default")
            height: UM.Theme.getSize("setting_control").height
            anchors.left: parent.left
            anchors.top: ext2Label.bottom
            anchors.topMargin: UM.Theme.getSize("default_margin").height
          }

          ComboBox {  // extruder 3 dropdown
            id: ext3Dropdown
            enabled: base.numExtruders >= 3
            width: UM.Theme.getSize("setting_control").width
            height: UM.Theme.getSize("setting_control").height
            anchors.right: parent.right
            anchors.top: ext3Label.top

            model: outputsModel
            textRole: "label"
            currentIndex: main.ext_3_output_ind
            onCurrentIndexChanged: {
              main.setExtruderOutput(3, currentIndex)
            }
          }

          UM.Label {  // extruder 4 label
            id: ext4Label
            enabled: base.numExtruders >= 4
            text: "Extruder 4"
            font: UM.Theme.getFont("default")
            height: UM.Theme.getSize("setting_control").height
            anchors.left: parent.left
            anchors.top: ext3Label.bottom
            anchors.topMargin: UM.Theme.getSize("default_margin").height
          }

          ComboBox {  // extruder 4 dropdown
            id: ext4Dropdown
            enabled: base.numExtruders >= 4
            width: UM.Theme.getSize("setting_control").width
            height: UM.Theme.getSize("setting_control").height
            anchors.right: parent.right
            anchors.top: ext4Label.top

            model: outputsModel
            textRole: "label"
            currentIndex: main.ext_4_output_ind
            onCurrentIndexChanged: {
              main.setExtruderOutput(4, currentIndex)
            }
          }
        }
      }

      GroupBox {
        title: "Serial Ports"
        width: 0.3333 * (parent.width - (2 * parent.spacing))
        anchors.top: parent.top
        anchors.bottom: parent.bottom

        Rectangle {
          anchors.fill: parent

          UM.Label {
            id: fisnarComLabel
            text: "Fisnar"
            font: UM.Theme.getFont("default")
            height: UM.Theme.getSize("setting_control").height
            anchors.left: parent.left
            anchors.top: parent.top
          }

          SettingEntry {
            id: fisnarComEntry
            anchors.right: parent.right
            anchors.top: fisnarComLabel.top
            text: main.com_port_name
            valId: "com_port"
            validator: null  // don't want default DoubleValidator
            label: ""  // dont' want unit label
          }

          UM.Label {
            id: fisnarConnectionStateLabel
            text: base.fisnarConnected ? "Connected" : "Not Connected"
            color: base.fisnarConnected ? UM.Theme.getColor("success") : UM.Theme.getColor("error")
            font: UM.Theme.getFont("small")
            anchors.right: parent.right
            anchors.top: fisnarComEntry.bottom
            anchors.topMargin: UM.Theme.getSize("default_lining").height
          }

          UM.Label {  // dispenser com label
            id: dispenserComLabel
            text: "Pick and place dispenser"
            font: UM.Theme.getFont("default")
            height: UM.Theme.getSize("setting_control").height
            anchors.left: parent.left
            anchors.top: fisnarConnectionStateLabel.bottom
            anchors.topMargin: UM.Theme.getSize("default_margin").height
          }

          SettingEntry {
            id: dispenserComEntry
            anchors.right: parent.right
            anchors.top: dispenserComLabel.top
            text: main.dispenser_serial_port
            valId: "dispenser_com_port"
            validator: null
            label: ""
          }

          UM.Label {
            id: dispenserConnectionStateLabel
            text: base.dispenserConnected ? "Connected" : "Not Connected"
            color: base.dispenserConnected ? UM.Theme.getColor("success") : UM.Theme.getColor("error")
            font: UM.Theme.getFont("small")
            anchors.right: parent.right
            anchors.top: dispenserComEntry.bottom
            anchors.topMargin: UM.Theme.getSize("default_lining").height
          }
        }
      }

      // PrintSetupTooltip {
      //   id: tooltip
      // }
    }
}
