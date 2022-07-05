// Copyright (c) 2018 Ultimaker B.V.
// Cura is released under the terms of the LGPLv3 or higher.

// Opened with FisnarOutputDevice instance as 'OutputDevice'

import QtQuick 2.10
import QtQuick.Layouts 1.1
import QtQuick.Controls 2.15

import UM 1.5 as UM
import Cura 1.0 as Cura

Component
{
    Item
    {
        Rectangle
        {
            id: rect  // added
            color: UM.Theme.getColor("main_background")

            anchors.right: parent.right
            width: parent.width * 0.3
            anchors.top: parent.top
            anchors.bottom: parent.bottom

            // designed off of Cura.PrintMonitor
            ScrollView {
              height: parent.height
              width: parent.width
              contentHeight: progressMonitor.height

              ScrollBar.vertical: UM.ScrollBar {
                  id: scrollbar
                  parent: rect
                  anchors {
                      right: parent.right
                      top: parent.top
                      bottom: parent.bottom
                  }
              }
              clip: true

              Column {
                width: parent.width - scrollbar.width

                Row {  // temp, looks horrible but can clean up later
                  Label {
                    text: "Printing Progress: "
                  }

                  Label {
                    text: OutputDevice.print_progress
                  }

                  Button {
                    text: "Pause/Resume"
                    onClicked:
                    {
                      OutputDevice.pauseOrResumePrint()
                    }
                  }

                  Button {
                    text: "Terminate"
                    onClicked:
                    {
                      OutputDevice.terminatePrint()
                    }
                  }
                }

              }
            }

            // Cura.PrintMonitor
            // {
            //     anchors.top: parent.top
            //     anchors.left: parent.left
            //     anchors.right: parent.right
            //     anchors.bottom: footerSeparator.top
            // }
            //
            // Rectangle
            // {
            //     id: footerSeparator
            //     width: parent.width
            //     height: UM.Theme.getSize("wide_lining").height
            //     color: UM.Theme.getColor("wide_lining")
            //     anchors.bottom: monitorButton.top
            //     anchors.bottomMargin: UM.Theme.getSize("thick_margin").height
            // }
            //
            // // MonitorButton is actually the bottom footer panel.
            // Cura.MonitorButton
            // {
            //     id: monitorButton
            //     anchors.bottom: parent.bottom
            //     anchors.left: parent.left
            //     anchors.right: parent.right
            // }
        }
    }
}
