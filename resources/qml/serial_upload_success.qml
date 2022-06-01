import UM 1.5 as UM // This allows you to use all of Uranium's built-in QML items.
import QtQuick 2.2 // This allows you to use QtQuick's built-in QML items.
import QtQuick.Controls 1.1
import Cura 1.1 as Cura

UM.Dialog
{
  id: serialUploadErrorDialog
  width: 500 * screenScaleFactor
  height: 150 * screenScaleFactor
  minimumWidth: 500 * screenScaleFactor
  minimumHeight: 150 * screenScaleFactor

  Label
  {
    text: "Fisnar commands successfully uploaded. Press 'Run' on the Fisnar teach pendant to start printing."
    wrapMode: Label.WordWrap
    width: Math.floor(parent.width * .9)
    anchors.horizontalCenter: serialUploadErrorDialog.horizontalCenter
  }

  rightButtons: [
    Button {
      text: "Close"
      onClicked:
      {
        serialUploadErrorDialog.close()
      }
    }
  ]
}
