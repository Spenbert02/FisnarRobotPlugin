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
        property bool isPrinting: OutputDevice.printing_status
        property bool isPickPlacing: OutputDevice.pick_place_status

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
                          font: UM.Theme.getFont("large_bold")
                          color: UM.Theme.getColor("text_inactive")
                        }

                        UM.Label {  // filler - kind of hacky, but it works
                          text: "    "
                        }

                        UM.Label {
                          text: "Y"
                          font: UM.Theme.getFont("large_bold")
                        }

                        UM.Label {
                          text: enabled ? OutputDevice.y_pos : "--"
                          font: UM.Theme.getFont("large_bold")
                          color: UM.Theme.getColor("text_inactive")
                        }

                        UM.Label {  // another filler
                          text: "    "
                        }

                        UM.Label {
                          text: "Z"
                          font: UM.Theme.getFont("large_bold")
                        }

                        UM.Label {
                          text: enabled ? OutputDevice.z_pos : "--"
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
                    width: parent.width - (2 * UM.Theme.getSize("default_margin").width)
                    height: childrenRect.height + UM.Theme.getSize("default_margin").height
                    anchors.left: parent.left
                    anchors.leftMargin: UM.Theme.getSize("default_margin").width
                    spacing: UM.Theme.getSize("default_margin").width

                    UM.Label {  // jog position subheader
                      text: "Jog Position"
                      font: UM.Theme.getFont("default")
                      height: UM.Theme.getSize("setting_control").height
                    }

                    GridLayout {  // X/Y control interface
                      columns: 3
                      rows: 4
                      columnSpacing: UM.Theme.getSize("default_lining").width
                      rowSpacing: UM.Theme.getSize("default_lining").height

                      UM.Label {
                        text: "X/Y"
                        color: UM.Theme.getColor("setting_control_text")
                        width: height
                        height: UM.Theme.getSize("setting_control").height
                        horizontalAlignment: Text.AlignHCenter

                        Layout.row: 0
                        Layout.column: 1
                        Layout.preferredWidth: width
                        Layout.preferredHeight: height
                      }

                      Cura.SecondaryButton {  // X/Y 'up' (negative y)
                        Layout.row: 1
                        Layout.column: 1
                        Layout.preferredWidth: base._buttonSize
                        Layout.preferredHeight: base._buttonSize
                        iconSource: UM.Theme.getIcon("ChevronSingleUp")
                        leftPadding: (Layout.preferredWidth - iconSize) / 2
                        onClicked: {
                          OutputDevice.moveHead(0, -jogRow.selectedDistance, 0)
                        }
                      }

                      Cura.SecondaryButton {  // X/Y 'left' (positive x)
                        Layout.row: 2
                        Layout.column: 0
                        Layout.preferredWidth: base._buttonSize
                        Layout.preferredHeight: base._buttonSize
                        iconSource: UM.Theme.getIcon("ChevronSingleLeft")
                        leftPadding: (Layout.preferredWidth - iconSize) / 2
                        onClicked: {
                          OutputDevice.moveHead(jogRow.selectedDistance, 0, 0)
                        }
                      }

                      Cura.SecondaryButton {  // X/Y 'right' (negative x)
                        Layout.row: 2
                        Layout.column: 2
                        Layout.preferredWidth: base._buttonSize
                        Layout.preferredHeight: base._buttonSize
                        iconSource: UM.Theme.getIcon("ChevronSingleRight")
                        leftPadding: (Layout.preferredWidth - iconSize) / 2
                        onClicked: {
                          OutputDevice.moveHead(-jogRow.selectedDistance, 0, 0)
                        }
                      }

                      Cura.SecondaryButton {  // X/Y 'down' (positive y)
                        Layout.row: 3
                        Layout.column: 1
                        Layout.preferredWidth: base._buttonSize
                        Layout.preferredHeight: base._buttonSize
                        iconSource: UM.Theme.getIcon("ChevronSingleDown")
                        leftPadding: (Layout.preferredWidth - iconSize) / 2
                        onClicked: {
                          OutputDevice.moveHead(0, jogRow.selectedDistance, 0)
                        }
                      }

                      Cura.SecondaryButton {  // home x/y axes
                        Layout.row: 2
                        Layout.column: 1
                        Layout.preferredWidth: base._buttonSize
                        Layout.preferredHeight: base._buttonSize
                        iconSource: UM.Theme.getIcon("House")
                        leftPadding: (Layout.preferredWidth - iconSize) / 2
                        onClicked: {
                          OutputDevice.homeXY()
                        }
                      }
                    }

                    Rectangle {  // filler for in between x/y and z manual control buttons
                      height: zControlButtons.height
                      width: UM.Theme.getSize("thick_margin").width
                      color: base.debug ? "lightyellow" : "#00000000"
                    }

                    GridLayout {  // z manual control buttons
                      id: zControlButtons
                      rows: 4
                      columns: 1
                      rowSpacing: UM.Theme.getSize("default_lining").height
                      columnSpacing: UM.Theme.getSize("default_lining").width

                      UM.Label {
                        text: "Z"
                        color: UM.Theme.getColor("setting_control_text")
                        width: height
                        height: UM.Theme.getSize("setting_control").height
                        horizontalAlignment: Text.AlignHCenter

                        Layout.row: 0
                        Layout.column: 0
                        Layout.preferredWidth: width
                        Layout.preferredHeight: height
                      }

                      Cura.SecondaryButton {  // z up
                        Layout.row: 1
                        Layout.column: 0
                        Layout.preferredWidth: base._buttonSize
                        Layout.preferredHeight: base._buttonSize
                        iconSource: UM.Theme.getIcon("ChevronSingleUp")
                        leftPadding: (Layout.preferredWidth - iconSize) / 2
                        onClicked: {
                          OutputDevice.moveHead(0, 0, -jogRow.selectedDistance)
                        }
                      }

                      Cura.SecondaryButton {
                        Layout.row: 2
                        Layout.column: 0
                        Layout.preferredWidth: base._buttonSize
                        Layout.preferredHeight: base._buttonSize
                        iconSource: UM.Theme.getIcon("House")
                        leftPadding: (Layout.preferredWidth - iconSize) / 2
                        onClicked: {
                          OutputDevice.homeZ()
                        }
                      }

                      Cura.SecondaryButton {
                        Layout.row: 3
                        Layout.column: 0
                        Layout.preferredWidth: base._buttonSize
                        Layout.preferredHeight: base._buttonSize
                        iconSource: UM.Theme.getIcon("ChevronSingleDown")
                        leftPadding: (Layout.preferredWidth - iconSize) / 2
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

                          enabled: false  // TODO: actually implement this, should be dynamic and sould check then send bytes

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
                            text: "feature coming soon..."  // temporary, for first publish
                            color: enabled ? UM.Theme.getColor("setting_control_text") : UM.Theme.getColor("setting_control_disabled_text")
                            selectByMouse: true
                            clip: true
                            enabled: parent.enabled
                            renderType: Text.NativeRendering

                            anchors.left: parent.left
                            anchors.leftMargin: UM.Theme.getSize("setting_unit_margin").width
                            anchors.right: parent.right
                            anchors.verticalCenter: parent.verticalCenter

                            // Keys.onReturnPressed: {  // TODO: activate for next publish
                            //   textEntryBox.text = ""
                            // }
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

                      Column {  // column for pick and place entries; TODO: these text box values should be able to be updated from python
                        width: parent.width
                        spacing: UM.Theme.getSize("default_margin").height

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

                          TextField {  // x entry
                            id: pickXEntry
                            anchors.right: parent.right
                            anchors.top: parent.top
                            width: UM.Theme.getSize("setting_control").width
                            height: UM.Theme.getSize("setting_control").height
                            text: OutputDevice.pick_x
                            validator: DoubleValidator {
                              decimals: 3
                              locale: "en_US"
                              bottom: 0
                              top: 200
                            }
                            onEditingFinished: {
                              OutputDevice.setPickLocation(text, pickYEntry.text, pickZEntry.text)
                            }
                          }

                          UM.Label {  // x entry unit
                            text: "mm"
                            font: UM.Theme.getFont("small")
                            color: UM.Theme.getColor("setting_unit")
                            height: UM.Theme.getSize("setting_control").height
                            anchors.top: pickXEntry.top
                            anchors.right: pickXEntry.right
                            anchors.rightMargin: UM.Theme.getSize("setting_unit_margin").width
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

                          TextField {  // pick y entry
                            id: pickYEntry
                            anchors.left: pickXEntry.left
                            anchors.top: pickXEntry.bottom
                            anchors.topMargin: UM.Theme.getSize("default_lining").height
                            width: UM.Theme.getSize("setting_control").width
                            height: UM.Theme.getSize("setting_control").height
                            text: OutputDevice.pick_y
                            validator: DoubleValidator {
                              decimals: 3
                              locale: "en_US"
                              bottom: 0
                              top: 200
                            }
                            onEditingFinished: {
                              OutputDevice.setPickLocation(pickXEntry.text, text, pickZEntry.text)
                            }
                          }

                          UM.Label {  // y entry unit
                            text: "mm"
                            font: UM.Theme.getFont("small")
                            color: UM.Theme.getColor("setting_unit")
                            height: UM.Theme.getSize("setting_control").height
                            anchors.top: pickYEntry.top
                            anchors.right: pickYEntry.right
                            anchors.rightMargin: UM.Theme.getSize("setting_unit_margin").width
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

                          TextField {  // z entry
                            id: pickZEntry
                            anchors.left: pickYEntry.left
                            anchors.top: pickYEntry.bottom
                            anchors.topMargin: UM.Theme.getSize("default_lining").height
                            width: UM.Theme.getSize("setting_control").width
                            height: UM.Theme.getSize("setting_control").height
                            text: OutputDevice.pick_z
                            validator: DoubleValidator {
                              decimals: 3
                              locale: "en_US"
                              bottom: 0
                              top: 200
                            }
                            onEditingFinished: {
                              OutputDevice.setPickLocation(pickXEntry.text, pickYEntry.text, text)
                            }
                          }

                          UM.Label {  // z entry unit
                            text: "mm"
                            font: UM.Theme.getFont("small")
                            color: UM.Theme.getColor("setting_unit")
                            height: UM.Theme.getSize("setting_control").height
                            anchors.top: pickZEntry.top
                            anchors.right: pickZEntry.right
                            anchors.rightMargin: UM.Theme.getSize("setting_unit_margin").width
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

                          TextField {  // place x entry
                            id: placeXEntry
                            anchors.top: parent.top
                            anchors.right: parent.right
                            width: UM.Theme.getSize("setting_control").width
                            height: UM.Theme.getSize("setting_control").height
                            text: OutputDevice.place_x
                            validator: DoubleValidator {
                              decimals: 3
                              locale: "en_US"
                              bottom: 0
                              top: 200
                            }
                            onEditingFinished: {
                              OutputDevice.setPlaceLocation(text, placeYEntry.text, placeZEntry.text)
                            }
                          }

                          UM.Label {  // x entry unit
                            text: "mm"
                            font: UM.Theme.getFont("small")
                            color: UM.Theme.getColor("setting_unit")
                            height: UM.Theme.getSize("setting_control").height
                            anchors.top: placeXEntry.top
                            anchors.right: placeXEntry.right
                            anchors.rightMargin: UM.Theme.getSize("setting_unit_margin").width
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

                          TextField {  // place y entry
                            id: placeYEntry
                            anchors.top: placeYLabel.top
                            anchors.left: placeXEntry.left
                            width: UM.Theme.getSize("setting_control").width
                            height: UM.Theme.getSize("setting_control").height
                            text: OutputDevice.place_y
                            validator: DoubleValidator {
                              decimals: 3
                              locale: "en_US"
                              bottom: 0
                              top: 200
                            }
                            onEditingFinished: {
                              OutputDevice.setPlaceLocation(placeXEntry.text, text, placeZEntry.text)
                            }
                          }

                          UM.Label {  // y entry unit
                            text: "mm"
                            font: UM.Theme.getFont("small")
                            color: UM.Theme.getColor("setting_unit")
                            height: UM.Theme.getSize("setting_control").height
                            anchors.top: placeYEntry.top
                            anchors.right: placeYEntry.right
                            anchors.rightMargin: UM.Theme.getSize("setting_unit_margin").width
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

                          TextField {  // place z entry
                            id: placeZEntry
                            anchors.top: placeZLabel.top
                            anchors.left: placeYEntry.left
                            width: UM.Theme.getSize("setting_control").width
                            height: UM.Theme.getSize("setting_control").height
                            text: OutputDevice.place_z
                            validator: DoubleValidator {
                              decimals: 3
                              locale: "en_US"
                              bottom: 0
                              top: 200
                            }
                            onEditingFinished: {
                              OutputDevice.setPlaceLocation(placeXEntry.text, placeYEntry.text, text)
                            }
                          }

                          UM.Label {  // z entry unit
                            text: "mm"
                            font: UM.Theme.getFont("small")
                            color: UM.Theme.getColor("setting_unit")
                            height: UM.Theme.getSize("setting_control").height
                            anchors.top: placeZEntry.top
                            anchors.right: placeZEntry.right
                            anchors.rightMargin: UM.Theme.getSize("setting_unit_margin").width
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

                          TextField {
                            id: vacuumPressureEntry
                            anchors.right: vacuumPressureUnitsDropdown.left
                            anchors.top: parent.top
                            text: OutputDevice.vacuum_pressure
                            width: UM.Theme.getSize("setting_control").width - vacuumPressureUnitsDropdown.width
                            height: UM.Theme.getSize("setting_control").height
                            onEditingFinished: {
                              OutputDevice.setVacuumPressure(text)
                            }
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

                          TextField {
                            id: xySpeedEntry
                            text: OutputDevice.xy_speed
                            anchors.right: parent.right
                            anchors.top: parent.top
                            width: UM.Theme.getSize("setting_control").width
                            height: UM.Theme.getSize("setting_control").height
                            validator: DoubleValidator {
                              decimals: 3
                              locale: "en_US"
                              bottom: 0
                              top: 100
                            }
                            onEditingFinished: {
                              OutputDevice.setXYSpeed(text)
                            }
                          }

                          UM.Label {  // x/y speed entry unit
                            text: "mm/s"
                            font: UM.Theme.getFont("small")
                            color: UM.Theme.getColor("setting_unit")
                            height: UM.Theme.getSize("setting_control").height
                            anchors.top: xySpeedEntry.top
                            anchors.right: xySpeedEntry.right
                            anchors.rightMargin: UM.Theme.getSize("setting_unit_margin").width
                          }

                          UM.Label {
                            id: zSpeedLabel
                            text: "Z"
                            font: UM.Theme.getFont("default_bold")
                            height: UM.Theme.getSize("setting_control").height
                            anchors.right: zSpeedEntry.left
                            anchors.rightMargin: UM.Theme.getSize("default_margin").width
                            anchors.top: xySpeedLabel.bottom
                            anchors.topMargin: UM.Theme.getSize("default_lining").height
                          }

                          TextField {
                            id: zSpeedEntry
                            text: OutputDevice.z_speed
                            anchors.right: parent.right
                            anchors.top: zSpeedLabel.top
                            width: UM.Theme.getSize("setting_control").width
                            height: UM.Theme.getSize("setting_control").height
                            validator: DoubleValidator {
                              decimals: 3
                              locale: "en_US"
                              bottom: 0
                              top: 200
                            }
                            onEditingFinished: {
                              OutputDevice.setZSpeed(text)
                            }
                          }

                          UM.Label {  // z speed entry unit
                            text: "mm/s"
                            font: UM.Theme.getFont("small")
                            color: UM.Theme.getColor("setting_unit")
                            height: UM.Theme.getSize("setting_control").height
                            anchors.top: zSpeedEntry.top
                            anchors.right: zSpeedEntry.right
                            anchors.rightMargin: UM.Theme.getSize("setting_unit_margin").width
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

                          TextField {  // pick dwell time entry
                            id: pickDwellEntry
                            text: OutputDevice.pick_dwell
                            anchors.right: parent.right
                            anchors.top: parent.top
                            width: UM.Theme.getSize("setting_control").width
                            height: UM.Theme.getSize("setting_control").height
                            validator: DoubleValidator {
                              decimals: 1
                              locale: "en_US"
                              bottom: 0.0
                              top: 60.0
                            }
                            onEditingFinished: {
                              OutputDevice.setPickDwell(text)
                            }
                          }

                          UnitLabel {  // pick dwell entry unit
                            anchors.right: pickDwellEntry.right
                            anchors.top: pickDwellEntry.top
                            label: "sec"
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

                          TextField {  // place dwell entry
                            id: placeDwellEntry
                            text: OutputDevice.place_dwell
                            width: UM.Theme.getSize("setting_control").width
                            height: UM.Theme.getSize("setting_control").height
                            anchors.right: parent.right
                            anchors.top: placeDwellLabel.top
                            validator: DoubleValidator {
                              decimals: 1
                              locale: "en_US"
                              bottom: 0.0
                              top: 60.0
                            }
                            onEditingFinished: {
                              OutputDevice.setPlaceDwell(text)
                            }
                          }

                          UnitLabel {  // place dwell unit
                            anchors.top: placeDwellEntry.top
                            anchors.right: placeDwellEntry.right
                            label: "sec"
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

                          TextField {
                            id: repsEntry
                            text: OutputDevice.reps
                            width: UM.Theme.getSize("setting_control").width
                            height: UM.Theme.getSize("setting_control").height
                            anchors.right: parent.right
                            anchors.top: parent.top
                            validator: IntValidator {
                              locale: "en_US"
                              bottom: 1
                              top: 100
                            }
                            onEditingFinished: {
                              OutputDevice.setReps(text)
                            }
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
