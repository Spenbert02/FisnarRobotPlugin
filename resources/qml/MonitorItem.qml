// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

// Opened with FisnarOutputDevice instance as 'OutputDevice'

// This is a horrendously long qml file, and should probably be broken
// into individual files. In fact, the qml used by the USBPrinterOutputDevice
// plugin should eventually be used here, but the FisnarOutputDevice plugin
// isn't yet compatible some of the references in those qml files

import QtQuick 2.10
import QtQuick.Layouts 1.1
import QtQuick.Controls 2.15

import UM 1.5 as UM
import Cura 1.0 as Cura

import "."

Component
{
    Item
    {
        id: base
        property bool debug: false  // set to true to see 'colors' of different UI components, false for actual display
        property var _buttonSize: UM.Theme.getSize("setting_control").height + UM.Theme.getSize("thin_margin").height  // taken from Cura's ManualPrinterControl.qml
        property bool isConnected: OutputDevice.connectionState == 2
        // property bool isConnected: true  // for debugging
        property bool isPrinting: OutputDevice.printing_status
        // property bool isPrinting: false  // for debugging
        property bool isPickPlacing: OutputDevice.pick_place_status

        function updateVal(valId, val) {
          if (valId == "pick_place_dispenser") {
            // pass
          } else if (valId == "pick_x") {
            OutputDevice.setPickLocation(val, -1, -1);
          } else if (valId == "pick_y") {
            OutputDevice.setPickLocation(-1, val, -1);
          } else if (valId == "pick_z") {
            OutputDevice.setPickLocation(-1, -1, val);
          } else if (valId == "place_x") {
            OutputDevice.setPlaceLocation(val, -1, -1);
          } else if (valId == "place_y") {
            OutputDevice.setPlaceLocation(-1, val, -1);
          } else if (valId == "place_z") {
            OutputDevice.setPlaceLocation(-1, -1, val);
          } else if (valId == "vacuum_pressure") {
            OutputDevice.setVacuumPressure(val);
          } else if (valId == "xy_travel_speed") {
            OutputDevice.setXYSpeed(val);
          } else if (valId == "pick_z_travel_speed") {
            OutputDevice.setPickZSpeed(val);
          } else if (valId == "place_z_travel_speed") {
            OutputDevice.setPlaceZSpeed(val);
          } else if (valId == "pick_dwell_time") {
            OutputDevice.setPickDwell(val);
          } else if (valId == "place_dwell_time") {
            OutputDevice.setPlaceDwell(val);
          } else if (valId == "repititions") {
            OutputDevice.setReps(val);
          }
        }

        function getTooltip(val) {
          return OutputDevice.getTooltip(val);
        }

        Rectangle
        {
            color: UM.Theme.getColor("main_background")

            anchors.right: parent.right
            width: Math.floor(parent.width * 0.3)
            anchors.top: parent.top
            anchors.bottom: parent.bottom

            ScrollView {  // start of 'Cura.PrintMonitor'
              id: scrollView
              width: parent.width
              anchors.left: parent.left
              anchors.top: parent.top
              anchors.bottom: footerSeparator.top

              contentHeight: printMonitor.height + UM.Theme.getSize("default_margin").height

              ScrollBar.vertical: UM.ScrollBar {  // ScrollBar only shows up if the contentHeight is greater than the ScrollView height?
                  id: scrollbar
                  parent: parent.parent
                  anchors {
                    right: parent.right
                    top: parent.top
                    bottom: parent.bottom
                  }
              }
              clip: true

              Rectangle {
                anchors {
                  left: parent.left
                  right: parent.right
                  rightMargin: UM.Theme.getSize("default_margin").width
                  top: parent.top
                  bottom: parent.bottom
                }

                Column {
                  id: printMonitor
                  width: parent.width - scrollbar.width
                  property var scrollbarwidth: scrollbar.width
                  enabled: base.isConnected && !base.isPrinting

                  Rectangle {  // top stuff - fisnar name and serial port connected to
                    id: outputDeviceHeader
                    height: childrenRect.height + (2 * UM.Theme.getSize("default_margin").height)
                    width: parent.width
                    color: base.debug ? "lightgreen" : UM.Theme.getColor("setting_category")

                    UM.Label {  // 'Fisnar F5200N' label
                      id: fisnarNameLabel
                      font: UM.Theme.getFont("large_bold")
                      text: "Fisnar F5200N"
                      anchors.left: parent.left
                      anchors.leftMargin: UM.Theme.getSize("default_margin").width
                      anchors.top: parent.top
                      anchors.topMargin: UM.Theme.getSize("default_margin").height
                    }

                    UM.Label {  // serial port label
                      id: serialPortLabel
                      font: UM.Theme.getFont("default_bold")
                      color: UM.Theme.getColor("text_inactive")
                      text: OutputDevice.fisnar_serial_port
                      anchors.top: fisnarNameLabel.bottom
                      anchors.topMargin: UM.Theme.getSize("default_margin").height
                      anchors.left: parent.left
                      anchors.leftMargin: UM.Theme.getSize("default_margin").width
                    }
                  }

                  Rectangle {  // padding for inbetween output device header and current state section
                    height: UM.Theme.getSize("thick_margin").height
                    width: parent.width
                    color: base.debug ? "lightyellow" : "#00000000"
                  }

                  Rectangle {  // 'current state' header
                    id: currentStateHeader
                    height: UM.Theme.getSize("section").height
                    width: parent.width
                    color: base.debug ? "lightblue" : UM.Theme.getColor("setting_category")

                    UM.Label {
                      text: "Current State"
                      font: UM.Theme.getFont("medium")
                      anchors.verticalCenter: parent.verticalCenter
                      anchors.left: parent.left
                      anchors.leftMargin: UM.Theme.getSize("default_margin").width
                    }
                  }

                  Rectangle {  // position subheader
                    id: positionSubHeader
                    height: UM.Theme.getSize("section_control").height
                    width: parent.width
                    color: base.debug ? "lightcyan" : UM.Theme.getColor("setting_category")

                    UM.Label {
                      text: "Position"
                      font: UM.Theme.getFont("default")
                      anchors.verticalCenter: parent.verticalCenter
                      anchors.left: parent.left
                      anchors.leftMargin: UM.Theme.getSize("default_margin").width
                    }
                  }

                  Rectangle {  // 'current state' contents
                    id: currentStateBody
                    height: childrenRect.height + UM.Theme.getSize("thick_margin").height
                    width: parent.width
                    color: base.debug ? "lightgreen" : UM.Theme.getColor("setting_category")

                    Rectangle {
                      height: childrenRect.height
                      width: parent.width - UM.Theme.getSize("default_margin").width
                      anchors.left: parent.left
                      anchors.leftMargin: UM.Theme.getSize("default_margin").width
                      anchors.top: parent.top
                      color: base.debug ? "red" : "#00000000"

                      Row {  // current position coordinates row
                        spacing: UM.Theme.getSize("default_margin").width

                        UM.Label {
                          text: "X"
                          font: UM.Theme.getFont("large_bold")
                        }

                        UM.Label {
                          text: enabled ? OutputDevice.x_pos : "--"
                          width: UM.Theme.getSize("setting_control").width / 2
                          font: UM.Theme.getFont("large_bold")
                          color: UM.Theme.getColor("text_inactive")
                        }

                        UM.Label {
                          text: "Y"
                          font: UM.Theme.getFont("large_bold")
                        }

                        UM.Label {
                          text: enabled ? OutputDevice.y_pos : "--"
                          width: UM.Theme.getSize("setting_control").width / 2
                          font: UM.Theme.getFont("large_bold")
                          color: UM.Theme.getColor("text_inactive")
                        }

                        UM.Label {
                          text: "Z"
                          font: UM.Theme.getFont("large_bold")
                        }

                        UM.Label {
                          text: enabled ? OutputDevice.z_pos : "--"
                          width: UM.Theme.getSize("setting_control").width / 2
                          font: UM.Theme.getFont("large_bold")
                          color: UM.Theme.getColor("text_inactive")
                        }
                      }
                    }
                  }

                  Rectangle {  // printer control header
                    id: printerControlHeader
                    height: UM.Theme.getSize("section").height
                    width: parent.width
                    color: base.debug ? "lightblue" : UM.Theme.getColor("setting_category")

                    UM.Label {
                      text: "Manual Control"
                      font: UM.Theme.getFont("medium")
                      anchors.verticalCenter: parent.verticalCenter
                      anchors.left: parent.left
                      anchors.leftMargin: UM.Theme.getSize("default_margin").width
                    }
                  }

                  Row {  // jog position subheader and manual control buttons
                    id: manualControlRow
                    width: parent.width - (2 * UM.Theme.getSize("default_margin").width)
                    height: childrenRect.height + UM.Theme.getSize("default_margin").height
                    anchors.left: parent.left
                    anchors.leftMargin: UM.Theme.getSize("default_margin").width
                    spacing: UM.Theme.getSize("thick_margin").width

                    UM.Label {  // jog position subheader
                      text: "Jog Position"
                      font: UM.Theme.getFont("default")
                      height: UM.Theme.getSize("setting_control").height
                    }

                    Rectangle {
                      id: xyManualRect
                      width: childrenRect.width
                      height: childrenRect.height

                      Rectangle {
                        id: middleFiller
                        height: UM.Theme.getSize("thick_lining").height
                        width: xyLabel.width
                        anchors.top: yNegButton.bottom
                        anchors.horizontalCenter: xyLabel.horizontalCenter
                      }

                      Rectangle {
                        id: leftFiller
                        height: xyLabel.height  // this has no effect, so long as it isn't larger than the height of the parent rectangle
                        width: middleFiller.height
                        anchors.right: xyLabel.left
                        anchors.verticalCenter: middleFiller.verticalCenter
                      }

                      Rectangle {
                        id: rightFiller
                        height: xyLabel.height  // as above, this has no effect
                        width: middleFiller.height
                        anchors.left: xyLabel.right
                        anchors.verticalCenter: middleFiller.verticalCenter
                      }

                      UM.Label {  // actual x/y label
                        id: xyLabel
                        text: "X/Y"
                        color: UM.Theme.getColor("setting_control_text")
                        width: xNegButton.width
                        height: UM.Theme.getSize("setting_control").height
                        horizontalAlignment: Text.AlignHCenter

                        anchors.top: parent.top
                        anchors.left: parent.left
                        anchors.leftMargin: xPosButton.width + leftFiller.width
                      }

                      ManualControlButton {  // 'up' button
                        id: yNegButton
                        width: base._buttonSize
                        height: base._buttonSize
                        iconSource: UM.Theme.getIcon("ChevronSingleUp")
                        anchors.horizontalCenter: xyLabel.horizontalCenter
                        anchors.top: xyLabel.bottom
                        leftPadding: (width - iconSize) / 2

                        onClicked: {
                          OutputDevice.moveHead(0, -jogRow.selectedDistance, 0);
                        }
                      }

                      ManualControlButton {  // 'down' button
                        id: yPosButton
                        width: base._buttonSize
                        height: base._buttonSize
                        iconSource: UM.Theme.getIcon("ChevronSingleDown")
                        anchors.horizontalCenter: xyLabel.horizontalCenter
                        anchors.top: middleFiller.bottom
                        leftPadding: (width - iconSize) / 2
                        onClicked: {
                          OutputDevice.moveHead(0, jogRow.selectedDistance, 0)
                        }
                      }

                      ManualControlButton {  // 'left' button
                        id: xPosButton
                        width: base._buttonSize
                        height: base._buttonSize
                        iconSource: UM.Theme.getIcon("ChevronSingleLeft")
                        anchors.verticalCenter: leftFiller.verticalCenter
                        anchors.right: leftFiller.left
                        leftPadding: (width - iconSize) / 2
                        onClicked: {
                          OutputDevice.moveHead(jogRow.selectedDistance, 0, 0)
                        }
                      }

                      ManualControlButton {  // 'right' button
                        id: xNegButton
                        width: base._buttonSize
                        height: base._buttonSize
                        iconSource: UM.Theme.getIcon("ChevronSingleRight")
                        anchors.verticalCenter: rightFiller.verticalCenter
                        anchors.left: rightFiller.right
                        leftPadding: (width - iconSize) / 2
                        onClicked: {
                          OutputDevice.moveHead(-jogRow.selectedDistance, 0, 0)
                        }
                      }
                    }

                    Rectangle {  // home button rectangle
                      id: homeManualRect
                      width: childrenRect.width
                      height: childrenRect.height

                      UM.Label {
                        id: homeLabel
                        text: "Home"
                        horizontalAlignment: Text.AlignHCenter
                        color: UM.Theme.getColor("setting_control_text")
                        width: homeButton.width
                        height: UM.Theme.getSize("setting_control").height
                        anchors.left: parent.left
                        anchors.top: parent.top
                        anchors.topMargin: (base._buttonSize + UM.Theme.getSize("thick_lining").height) / 2  // kind of hacky
                      }

                      ManualControlButton {
                        id: homeButton
                        width: base._buttonSize
                        height: base._buttonSize
                        iconSource: UM.Theme.getIcon("House")
                        anchors.top: homeLabel.bottom
                        anchors.horizontalCenter: homeLabel.horizontalCenter
                        leftPadding: (width - iconSize) / 2
                        onClicked: {
                          OutputDevice.home()
                        }
                      }
                    }

                    Rectangle {
                      id: zManualRect
                      width: childrenRect.width
                      height: childrenRect.height

                      Rectangle {  // filler between up and down buttons
                        id: upDownFiller
                        width: zNegButton.width
                        height: UM.Theme.getSize("thick_lining").height
                        anchors.top: zNegButton.bottom
                        anchors.horizontalCenter: zNegButton.horizontalCenter
                      }

                      UM.Label {
                        id: zManualLabel
                        text: "Z"
                        color: UM.Theme.getColor("setting_control_text")
                        horizontalAlignment: Text.AlignHCenter
                        width: zNegButton.width
                        height: UM.Theme.getSize("setting_control").height
                        anchors.left: parent.left
                        anchors.top: parent.top
                      }

                      ManualControlButton {  // neg z label
                        id: zNegButton
                        width: base._buttonSize
                        height: base._buttonSize
                        iconSource: UM.Theme.getIcon("ChevronSingleUp")
                        anchors.top: zManualLabel.bottom
                        anchors.horizontalCenter: zManualLabel.horizontalCenter
                        leftPadding: (width - iconSize) / 2
                        onClicked: {
                          OutputDevice.moveHead(0, 0, -jogRow.selectedDistance)
                        }
                      }

                      ManualControlButton {
                        id: zPosButton
                        width: base._buttonSize
                        height: base._buttonSize
                        iconSource: UM.Theme.getIcon("ChevronSingleDown")
                        anchors.top: upDownFiller.bottom
                        anchors.horizontalCenter: upDownFiller.horizontalCenter
                        leftPadding: (width - iconSize) / 2
                        onClicked: {
                          OutputDevice.moveHead(0, 0, jogRow.selectedDistance)
                        }
                      }
                    }
                  }

                  Row {  // jog distance subheader and buttons
                    id: jogRow

                    width: parent.width - (2 * UM.Theme.getSize("default_margin").width)
                    height: childrenRect.height + UM.Theme.getSize("default_margin").height
                    anchors.left: parent.left
                    anchors.leftMargin: UM.Theme.getSize("default_margin").width
                    spacing: UM.Theme.getSize("default_margin").width

                    property real selectedDistance: 1

                    UM.Label {
                      text: "Jog distance"
                      font: UM.Theme.getFont("default")
                      height: UM.Theme.getSize("setting_control").height
                    }

                    Row {  // buttons for jog distance selection
                      Repeater {
                        model: distancesModel
                        delegate: Cura.SecondaryButton {
                          height: base._buttonSize
                          text: model.label
                          ButtonGroup.group: distanceGroup
                          color: jogRow.selectedDistance == model.value ? UM.Theme.getColor("primary_button") : UM.Theme.getColor("secondary_button")
                          textColor: jogRow.selectedDistance == model.value ? UM.Theme.getColor("primary_button_text") : UM.Theme.getColor("secondary_button_text")
                          hoverColor: jogRow.selectedDistance == model.value ? UM.Theme.getColor("primary_button_hover") : UM.Theme.getColor("secondary_button_hover")
                          onClicked: {
                            jogRow.selectedDistance = model.value
                          }
                        }
                      }
                    }
                  }

                  Rectangle {  // RS232 custom command
                    width: parent.width - (2 * UM.Theme.getSize("default_margin").width)
                    height: childrenRect.height + UM.Theme.getSize("default_margin").height
                    anchors.left: parent.left
                    anchors.leftMargin: UM.Theme.getSize("default_margin").width

                    Row {
                      width: parent.width
                      height: childrenRect.height
                      anchors.left: parent.left
                      spacing: UM.Theme.getSize("default_margin").width

                      UM.Label {
                        text: "Send command over RS232"
                        font: UM.Theme.getFont("default")
                        height: UM.Theme.getSize("setting_control").height
                      }

                      Row {
                        Rectangle {
                          id: textRect

                          color: enabled ? UM.Theme.getColor("setting_validation_ok") : UM.Theme.getColor("setting_control_disabled")
                          border.width: UM.Theme.getSize("default_lining").width
                          border.color: enabled ? (textEntryMouseArea.containsMouse ? UM.Theme.getColor("setting_control_border_highlight") : UM.Theme.getColor("setting_control_border")) : UM.Theme.getColor("setting_control_disabled_border")

                          width: UM.Theme.getSize("setting_control").width
                          height: UM.Theme.getSize("setting_control").height

                          Rectangle {
                            anchors.fill: parent
                            anchors.margins: UM.Theme.getSize("default_lining").width
                            color: UM.Theme.getColor("setting_control_highlight")
                            opacity: textRect.hovered ? 1.0 : 0.0
                          }

                          MouseArea {
                            id: textEntryMouseArea
                            hoverEnabled: true
                            anchors.fill: parent
                            cursorShape: Qt.IBeamCursor
                          }

                          TextInput {
                            id: textEntryBox
                            font: UM.Theme.getFont("default")
                            color: enabled ? UM.Theme.getColor("setting_control_text") : UM.Theme.getColor("setting_control_disabled_text")
                            selectByMouse: true
                            clip: true
                            enabled: parent.enabled
                            renderType: Text.NativeRendering

                            anchors.left: parent.left
                            anchors.leftMargin: UM.Theme.getSize("setting_unit_margin").width
                            anchors.right: parent.right
                            anchors.verticalCenter: parent.verticalCenter

                            Keys.onReturnPressed: {
                              OutputDevice.sendRawCommand(text)
                              textEntryBox.text = ""
                            }
                          }
                        }
                      }
                    }
                  }

                  Rectangle {  // pick and place header
                    id: pickPlaceHeader
                    height: UM.Theme.getSize("section").height
                    width: parent.width
                    color: base.debug ? "lightblue" : UM.Theme.getColor("setting_category")

                    UM.Label {
                      text: "Pick-and-Place"
                      font: UM.Theme.getFont("medium")
                      anchors.verticalCenter: parent.verticalCenter
                      anchors.left: parent.left
                      anchors.leftMargin: UM.Theme.getSize("default_margin").width
                    }
                  }

                  Row {  // pick and place 'setup' area
                    width: parent.width - (2 * UM.Theme.getSize("default_margin").width)
                    height: childrenRect.height
                    anchors.left: parent.left
                    anchors.leftMargin: UM.Theme.getSize("default_margin").width
                    spacing: UM.Theme.getSize("default_margin").width

                    UM.Label {
                      id: setupLabel
                      text: "Setup"
                      font: UM.Theme.getFont("default")
                      height: UM.Theme.getSize("setting_control").height
                    }

                    Rectangle {
                      width: parent.width - setupLabel.width
                      height: childrenRect.height
                      color: base.debug ? "red" : UM.Theme.getColor("setting_category")

                      Column {  // column for pick and place entries
                        width: parent.width
                        spacing: UM.Theme.getSize("default_margin").height

                        Rectangle {   // pick and place dispenser selection
                          width: parent.width
                          height: childrenRect.height
                          anchors.topMargin: UM.Theme.getSize("default_margin").height

                          UM.Label {
                            id: pickPlaceDispenserLabel
                            text: "Dispenser"
                            font: UM.Theme.getFont("default")
                            anchors.left: parent.left
                            anchors.top: parent.top
                          }

                          ComboBox {
                            id: pickPlaceDispenserDropdown
                            width: UM.Theme.getSize("setting_control").width
                            height: UM.Theme.getSize("setting_control").height
                            anchors.right: parent.right
                            anchors.top: parent.top
                            editable: false
                            currentIndex: OutputDevice.pick_place_dispenser_index
                            textRole: "text"
                            model: ListModel {
                              id: dispenserListModel
                              ListElement {
                                enabled: true
                                text: "Dispenser 1"
                                value: "dispenser_1"
                              }
                              ListElement {
                                text: "Dispenser 2"
                                value: "dispenser_2"
                              }
                            }
                            onCurrentIndexChanged: {
                              OutputDevice.setPickPlaceDispenser(dispenserListModel.get(currentIndex).value)
                            }
                          }
                        }

                        Rectangle {  // pick location
                          width: parent.width
                          height: childrenRect.height
                          anchors.topMargin: UM.Theme.getSize("default_margin").height

                          UM.Label {
                            id: pickLocLabel
                            text: "Pick Location"
                            font: UM.Theme.getFont("default")
                            anchors.left: parent.left
                            anchors.top: parent.top
                          }

                          UM.Label {  // x label
                            id: pickXLabel
                            text: "X"
                            font: UM.Theme.getFont("default_bold")
                            height: UM.Theme.getSize("setting_control").height
                            anchors.right: pickXEntry.left
                            anchors.rightMargin: UM.Theme.getSize("default_margin").width
                            anchors.top: parent.top
                          }

                          SettingEntry {  // pick x entry
                            id: pickXEntry
                            anchors.right: parent.right
                            anchors.top: pickXLabel.top
                            text: OutputDevice.pick_x
                            label: "mm"
                            valId: "pick_x"
                            tooltipId: "pick_x"
                          }

                          UM.Label {  // y label
                            id: pickYLabel
                            text: "Y"
                            font: UM.Theme.getFont("default_bold")
                            height: UM.Theme.getSize("setting_control").height
                            anchors.left: pickXLabel.left
                            anchors.top: pickXLabel.bottom
                            anchors.topMargin: UM.Theme.getSize("default_lining").height
                          }

                          SettingEntry {
                            id: pickYEntry
                            anchors.right: parent.right
                            anchors.top: pickXEntry.bottom
                            anchors.topMargin: UM.Theme.getSize("default_lining").height
                            text: OutputDevice.pick_y
                            label: "mm"
                            valId: "pick_y"
                            tooltipId: "pick_y"
                          }

                          UM.Label {  // pick z label
                            id: pickZLabel
                            text: "Z"
                            font: UM.Theme.getFont("default_bold")
                            height: UM.Theme.getSize("setting_control").height
                            anchors.left: pickYLabel.left
                            anchors.top: pickYLabel.bottom
                            anchors.topMargin: UM.Theme.getSize("default_lining").height
                          }

                          SettingEntry {  // pick z entry
                            id: pickZEntry
                            anchors.right: parent.right
                            anchors.top: pickYEntry.bottom
                            anchors.topMargin: UM.Theme.getSize("default_lining").height
                            text: OutputDevice.pick_z
                            label: "mm"
                            valId: "pick_z"
                            tooltipId: "pick_z"
                          }
                        }

                        Rectangle {  // place location
                          id: placeRect
                          width: parent.width
                          height: childrenRect.height
                          anchors.topMargin: UM.Theme.getSize("default_margin").height

                          UM.Label {  // place location label
                            id: placeLocLabel
                            text: "Place Location"
                            font: UM.Theme.getFont("default")
                            anchors.left: parent.left
                            anchors.top: parent.top
                          }

                          UM.Label {  // place x label
                            id: placeXLabel
                            text: "X"
                            font: UM.Theme.getFont("default_bold")
                            height: UM.Theme.getSize("setting_control").height
                            anchors.top: parent.top
                            anchors.right: placeXEntry.left
                            anchors.rightMargin: UM.Theme.getSize("default_margin").width
                          }

                          SettingEntry {
                            id: placeXEntry
                            anchors.top: parent.top
                            anchors.right: parent.right
                            text: OutputDevice.place_x
                            label: "mm"
                            valId: "place_x"
                            tooltipId: "place_x"
                          }

                          UM.Label {  // place y label
                            id: placeYLabel
                            text: "Y"
                            font: UM.Theme.getFont("default_bold")
                            height: UM.Theme.getSize("setting_control").height
                            anchors.top: placeXLabel.bottom
                            anchors.topMargin: UM.Theme.getSize("default_lining").height
                            anchors.left: placeXLabel.left
                          }

                          SettingEntry {
                            id: placeYEntry
                            anchors.right: parent.right
                            anchors.top: placeXEntry.bottom
                            anchors.topMargin: UM.Theme.getSize("default_lining").height
                            text: OutputDevice.place_y
                            label: "mm"
                            valId: "place_y"
                            tooltipId: "place_y"
                          }

                          UM.Label {  // place z label
                            id: placeZLabel
                            text: "Z"
                            font: UM.Theme.getFont("default_bold")
                            height: UM.Theme.getSize("setting_control").height
                            anchors.top: placeYLabel.bottom
                            anchors.topMargin: UM.Theme.getSize("default_lining").height
                            anchors.left: placeYLabel.left
                          }

                          SettingEntry {
                            id: placeZEntry
                            anchors.right: parent.right
                            anchors.top: placeYEntry.bottom
                            anchors.topMargin: UM.Theme.getSize("default_lining").height
                            text: OutputDevice.place_z
                            label: "mm"
                            valId: "place_z"
                            tooltipId: "place_z"
                          }
                        }

                        Rectangle {  // vacuum pressure
                          width: parent.width
                          height: childrenRect.height
                          anchors.topMargin: UM.Theme.getSize("default_margin").height

                          UM.Label {
                            id: vacuumPressureLabel
                            text: "Vacuum pressure"
                            font: UM.Theme.getFont("default")
                            height: UM.Theme.getSize("setting_control").height
                            anchors.top: parent.top
                            anchors.left: parent.left
                          }

                          SettingEntry {
                            id: vacuumPressureEntry
                            anchors.right: vacuumPressureUnitsDropdown.left
                            anchors.top: parent.top
                            width: UM.Theme.getSize("setting_control").width - vacuumPressureUnitsDropdown.width
                            text: OutputDevice.vacuum_pressure
                            label: ""
                            valId: "vacuum_pressure"
                            tooltipId: "vacuum_pressure"
                          }

                          ComboBox {  // vacuum pressure unit dropdown
                            id: vacuumPressureUnitsDropdown
                            textRole: "text"
                            width: 75 * screenScaleFactor
                            height: UM.Theme.getSize("setting_control").height
                            anchors.right: parent.right
                            anchors.top: parent.top
                            currentIndex: OutputDevice.vacuum_units
                            editable: false
                            model: pressureUnitsModel
                            onCurrentIndexChanged: {
                              OutputDevice.setVacuumUnits(currentIndex)
                            }
                          }
                        }

                        Rectangle {  // movement speed
                          width: parent.width
                          height: childrenRect.height
                          anchors.topMargin: UM.Theme.getSize("default_margin").height

                          UM.Label {  // travel speed label
                            id: movementSpeedLabel
                            text: "Travel speed"
                            font: UM.Theme.getFont("default")
                            height: UM.Theme.getSize("setting_control").height
                            anchors.top: parent.top
                            anchors.left: parent.left
                          }

                          UM.Label {
                            id: xySpeedLabel
                            text: "X/Y"
                            font: UM.Theme.getFont("default_bold")
                            height: UM.Theme.getSize("setting_control").height
                            anchors.right: xySpeedEntry.left
                            anchors.rightMargin: UM.Theme.getSize("default_margin").width
                            anchors.top: parent.top
                          }

                          SettingEntry {
                            id: xySpeedEntry
                            anchors.right: parent.right
                            anchors.top: parent.top
                            text: OutputDevice.xy_speed
                            label: "mm/s"
                            valId: "xy_travel_speed"
                            tooltipId: "xy_travel_speed"
                          }

                          UM.Label {
                            id: pickZSpeedLabel
                            text: "Pick Z"
                            font: UM.Theme.getFont("default_bold")
                            height: UM.Theme.getSize("setting_control").height
                            anchors.right: pickZSpeedEntry.left
                            anchors.rightMargin: UM.Theme.getSize("default_margin").width
                            anchors.top: xySpeedLabel.bottom
                            anchors.topMargin: UM.Theme.getSize("default_lining").height
                          }

                          SettingEntry {
                            id: pickZSpeedEntry
                            anchors.right: parent.right
                            anchors.top: xySpeedEntry.bottom
                            anchors.topMargin: UM.Theme.getSize("default_lining").height
                            text: OutputDevice.pick_z_speed
                            label: "mm/s"
                            valId: "pick_z_travel_speed"
                            tooltipId: "pick_z_travel_speed"
                          }

                          UM.Label {
                            id: placeZSpeedLabel
                            text: "Place Z"
                            font: UM.Theme.getFont("default_bold")
                            height: UM.Theme.getSize("setting_control").height
                            anchors.right: placeZSpeedEntry.left
                            anchors.rightMargin: UM.Theme.getSize("default_margin").width
                            anchors.top: pickZSpeedEntry.bottom
                            anchors.topMargin: UM.Theme.getSize("default_lining").height
                          }

                          SettingEntry {
                            id: placeZSpeedEntry
                            anchors.right: parent.right
                            anchors.top: pickZSpeedEntry.bottom
                            anchors.topMargin: UM.Theme.getSize("default_lining").height
                            text: OutputDevice.place_z_speed
                            label: "mm/s"
                            valId: "place_z_travel_speed"
                            tooltipId: "place_z_travel_speed"
                          }
                        }

                        Rectangle {  // dwell time rectangle
                          width: parent.width
                          height: childrenRect.height
                          anchors.topMargin: UM.Theme.getSize("default_margin").height

                          UM.Label {  // dwell time label
                            id: dwellTimeLabel
                            text: "Dwell time"
                            font: UM.Theme.getFont("default")
                            height: UM.Theme.getSize("setting_control").height
                            anchors.left: parent.left
                            anchors.top: parent.top
                          }

                          UM.Label {  // pick dwell time label
                            id: pickDwellLabel
                            text: "Pick"
                            font: UM.Theme.getFont("default_bold")
                            height: UM.Theme.getSize("setting_control").height
                            anchors.right: pickDwellEntry.left
                            anchors.rightMargin: UM.Theme.getSize("default_margin").width
                            anchors.top: pickDwellEntry.top
                          }

                          SettingEntry {
                            id: pickDwellEntry
                            anchors.right: parent.right
                            anchors.top: parent.top
                            text: OutputDevice.pick_dwell
                            label: "sec"
                            valId: "pick_dwell_time"
                            tooltipId: "place_dwell_time"
                          }

                          UM.Label {  // place dwell time label
                            id: placeDwellLabel
                            text: "Place"
                            font: UM.Theme.getFont("default_bold")
                            height: UM.Theme.getSize("setting_control").height
                            anchors.right: placeDwellEntry.left
                            anchors.rightMargin: UM.Theme.getSize("default_margin").width
                            anchors.top: pickDwellLabel.bottom
                            anchors.topMargin: UM.Theme.getSize("default_lining").height
                          }

                          SettingEntry {
                            id: placeDwellEntry
                            anchors.right: parent.right
                            anchors.top: pickDwellEntry.bottom
                            anchors.topMargin: UM.Theme.getSize("default_lining").height
                            text: OutputDevice.place_dwell
                            label: "sec"
                            valId: "place_dwell_time"
                            tooltipId: "place_dwell_time"
                          }
                        }

                        Rectangle {  // repitions rectangle
                          width: parent.width
                          height: childrenRect.height
                          anchors.topMargin: UM.Theme.getSize("default_margin").height

                          UM.Label {  // repitions label
                            id: repsLabel
                            text: "Repititions"
                            height: UM.Theme.getSize("setting_control").height
                            anchors.top: parent.top
                            anchors.left: parent.left
                          }

                          SettingEntry {
                            id: repsEntry
                            anchors.top: parent.top
                            anchors.right: parent.right
                            validator: IntValidator {
                              locale: "en_US"
                              bottom: 1
                              top: 100
                            }
                            text: OutputDevice.reps
                            label: ""
                            valId: "repititions"
                            tooltipId: "repitions"
                          }
                        }

                        Rectangle {  // buttons rectangle
                          width: parent.width
                          height: childrenRect.height
                          anchors.topMargin: UM.Theme.getSize("default_margin").height

                          Cura.SecondaryButton {
                            id: terminatePickPlaceButton
                            enabled: base.isPickPlacing
                            visible: base.isPickPlacing
                            height: UM.Theme.getSize("save_button_save_to_button").height
                            anchors.right: executePickPlaceButton.left
                            anchors.rightMargin: UM.Theme.getSize("default_margin").width
                            anchors.top: parent.top
                            text: "Stop"
                            onClicked: {
                              OutputDevice.terminatePickPlace()
                            }
                          }

                          Cura.SecondaryButton {  // execute button
                            id: executePickPlaceButton
                            enabled: !base.isPickPlacing
                            height: UM.Theme.getSize("save_button_save_to_button").height
                            anchors.right: parent.right
                            anchors.top: parent.top
                            text: base.isPickPlacing ? "In progress..." : "Execute Pick and Place Procedure"
                            onClicked: {
                              OutputDevice.executePickPlace()
                            }
                          }
                        }
                      }
                    }
                  }
                }
              }

              ListModel {
                id: distancesModel
                ListElement {label: "0.001"; value: 0.001}
                ListElement {label: "0.01"; value: 0.01}
                ListElement {label: "0.1"; value: 0.1}
                ListElement {label: "1"; value: 1.0}
                ListElement {label: "10"; value: 10.0}
              }
              ListModel {
                id: pressureUnitsModel
                ListElement{text: "kPa"; value: 0}
                ListElement{text: "in. H20"; value: 1}
                ListElement{text: "in. Hg"; value: 2}
                ListElement{text: "mm Hg"; value: 3}
                ListElement{text: "Torr"; value: 4}
              }
              ButtonGroup {
                id: distanceGroup
              }
            }  // end of 'Cura.PrintMonitor'

            Rectangle {  // footer separator
              id: footerSeparator
              width: parent.width
              height: UM.Theme.getSize("wide_lining").height
              color: UM.Theme.getColor("wide_lining")
              anchors.bottom: monitorFooter.top
              anchors.bottomMargin: UM.Theme.getSize("thick_margin").height
            }

            Item {  // start of "MonitorButton"
              id: monitorFooter
              height: childrenRect.height + UM.Theme.getSize("thick_margin").height
              anchors.bottom: parent.bottom
              anchors.left: parent.left
              anchors.right: parent.right
              visible: base.isPrinting
              enabled: base.isPrinting

              UM.Label {  // Progress label
                id: progressTextLabel
                text: "Progress:"
                font: UM.Theme.getFont("large_bold")
                color: UM.Theme.getColor("text")
                anchors.top: parent.top
                anchors.left: parent.left
                anchors.leftMargin: UM.Theme.getSize("thick_margin").width
              }

              UM.Label {  // Progress percentage label
                id: progressPercentageLabel
                text: OutputDevice.print_progress + "%"
                font: UM.Theme.getFont("large_bold")
                anchors.top: parent.top
                anchors.left: progressTextLabel.right
                anchors.leftMargin: UM.Theme.getSize("default_margin").width
              }

              Row {
                id: bottomRightButtonsRow
                height: terminateButton.height
                anchors.right: parent.right
                anchors.rightMargin: UM.Theme.getSize("thick_margin").width
                anchors.bottom: parent.bottom
                anchors.bottomMargin: UM.Theme.getSize("thick_margin").height
                spacing: UM.Theme.getSize("default_margin").width

                Cura.SecondaryButton {  // pause/resume button
                  id: pauseResumeButton
                  height: UM.Theme.getSize("save_button_save_to_button").height
                  text: "Pause"
                  onClicked: {
                    if (text == "Pause") {
                      text = "Resume"
                    } else {
                      text = "Pause"
                    }
                    OutputDevice.pauseOrResumePrint()
                  }
                }

                Cura.SecondaryButton {  // Terminate button
                  id: terminateButton
                  height: UM.Theme.getSize("save_button_save_to_button").height
                  text: "Terminate"
                  onClicked: {
                    OutputDevice.terminatePrint()
                    pauseResumeButton.text = "Pause"  // resetting this to prep for the next print
                  }
                }
              }
            }  // end of 'MonitorButton'
        }
    }
}
