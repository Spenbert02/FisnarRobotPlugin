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

    width: minimumWidth
    height: minimumHeight
    minimumWidth: 1000 * screenScaleFactor
    minimumHeight: 350 * screenScaleFactor

    onAfterAnimating: {  // updates the extruder numbers somewhat frequently - this should probably be set on a timer, but this works for now
      numExtruders = main.num_extruders
    }

    // PrintSetupTooltip {  // eventually tooltips will be added
    //   id: tooltip
    // }

    // Rectangle {  // test
    //   color: "red"
    //   anchors.fill: sectionRow
    // }

    Row {
      id: sectionRow
      height: parent.height - (2 * UM.Theme.getSize("default_margin").height)
      width: parent.width - (2 * UM.Theme.getSize("default_margin").width)
      anchors.top: parent.top
      anchors.topMargin: UM.Theme.getSize("default_margin").height
      anchors.left: parent.left
      anchors.leftMargin: UM.Theme.getSize("default_margin").width
      spacing: UM.Theme.getSize("thick_margin").width

      GroupBox {
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

          TextField {  // x-min text input
            id: xMinEntry
            width: UM.Theme.getSize("setting_control").width
            height: UM.Theme.getSize("setting_control").height
            anchors.right: parent.right
            anchors.top: xRangeLabel.top
            text: main.x_min
            validator: DoubleValidator {
              decimals: 3
              locale: "en_US"
              bottom: 0
              top: 200
            }
            onEditingFinished: {
              main.setCoord("fisnar_x_min", text)
            }
          }

          UnitLabel {
            anchors.right: xMinEntry.right
            anchors.top: xMinEntry.top
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

          TextField {  // x max entry
            id: xMaxEntry
            width: UM.Theme.getSize("setting_control").width
            height: UM.Theme.getSize("setting_control").height
            anchors.right: parent.right
            anchors.top: xMaxLabel.top
            text: main.x_max
            validator: DoubleValidator {
              decimals: 3
              locale: "en_US"
              bottom: 0
              top: 200
            }
            onEditingFinished: {
              main.setCoord("fisnar_x_max", text)
            }
          }

          UnitLabel {
            anchors.top: xMaxEntry.top
            anchors.right: xMaxEntry.right
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

          TextField {  // y min entry
            id: yMinEntry
            width: UM.Theme.getSize("setting_control").width
            height: UM.Theme.getSize("setting_control").height
            anchors.right: parent.right
            anchors.top: yMinLabel.top
            text: main.y_min
            validator: DoubleValidator {
              decimals: 3
              locale: "en_US"
              bottom: 0
              top: 200
            }
            onEditingFinished: {
              main.setCoord("fisnar_y_min", text)
            }
          }

          UnitLabel {  // y min unit label
            anchors.top: yMinEntry.top
            anchors.right: yMinEntry.right
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

          TextField {  // y max entry
            id: yMaxEntry
            width: UM.Theme.getSize("setting_control").width
            height: UM.Theme.getSize("setting_control").height
            anchors.right: parent.right
            anchors.top: yMaxLabel.top
            text: main.y_max
            validator: DoubleValidator {
              decimals: 3
              locale: "en_US"
              bottom: 0
              top: 200
            }
            onEditingFinished: {
              main.setCoord("fisnar_y_max", text)
            }
          }

          UnitLabel {  // y max entry
            anchors.top: yMaxEntry.top
            anchors.right: yMaxEntry.right
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

          TextField {  // z min 'entry' - will always be disabled
            id: zMinEntry
            enabled: false
            text: "0.0"
            width: UM.Theme.getSize("setting_control").width
            height: UM.Theme.getSize("setting_control").height
            anchors.right: parent.right
            anchors.top: zMinLabel.top
          }

          UnitLabel {  // z min units
            anchors.right: zMinEntry.right
            anchors.top: zMinEntry.top
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

          TextField {  // z max entry
            id: zMaxEntry
            width: UM.Theme.getSize("setting_control").width
            height: UM.Theme.getSize("setting_control").height
            anchors.top: zMaxLabel.top
            anchors.right: parent.right
            text: main.z_max
            validator: DoubleValidator {
              decimals: 3
              locale: "en_US"
              bottom: 0
              top: 200
            }
            onEditingFinished: {
              main.setCoord("fisnar_z_max", text)
            }
          }

          UnitLabel {  // z max units
            anchors.right: zMaxEntry.right
            anchors.top: zMaxEntry.top
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

          UM.Label {  //
            id: fisnarComLabel
            text: "Fisnar"
            font: UM.Theme.getFont("default")
            height: UM.Theme.getSize("setting_control").height
            anchors.left: parent.left
            anchors.top: parent.top
          }

          TextField {
            id: fisnarComEntry
            width: UM.Theme.getSize("setting_control").width
            height: UM.Theme.getSize("setting_control").height
            anchors.right: parent.right
            anchors.top: fisnarComLabel.top
            text: main.com_port_name
            onEditingFinished: {
              main.updateComPort(text)
            }
          }

          UM.Label {  // dispenser com label
            id: dispenserComLabel
            text: "Pick and place dispenser"
            font: UM.Theme.getFont("default")
            height: UM.Theme.getSize("setting_control").height
            anchors.left: parent.left
            anchors.top: fisnarComLabel.bottom
            anchors.topMargin: UM.Theme.getSize("default_margin").height
          }

          TextField {
            id: dispenserComEntry
            width: UM.Theme.getSize("setting_control").width
            height: UM.Theme.getSize("setting_control").height
            anchors.right: parent.right
            anchors.top: dispenserComLabel.top
            text: main.dispenser_serial_port
            onEditingFinished: {
              main.updateDispenserSerialPort(text)
            }
          }
        }
      }
    }
}
