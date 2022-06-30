import UM 1.5 as UM
import QtQuick 2.15
import QtQuick.Controls 2.1
import Cura 1.1 as Cura

UM.Dialog
{
  id: fisnarControllerErrorDialog
  width: 500 * screenScaleFactor
  height: 150 * screenScaleFactor
  minimumWidth: 500 * screenScaleFactor
  minimumHeight: 150 * screenScaleFactor

  Label
  {
    text: main.fisnar_control_error_msg
    wrapMode: Label.WordWrap
    width: Math.floor(parent.width * .9)
    anchors.horizontalCenter: fisnarControllerErrorDialog.horizontalCenter
  }

  rightButtons: [
    Button {
      text: "Ok"
      onClicked:
      {
        fisnarControllerErrorDialog.close()
      }
    }
  ]
}
