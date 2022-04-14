import UM 1.5 as UM // This allows you to use all of Uranium's built-in QML items.
import QtQuick 2.2 // This allows you to use QtQuick's built-in QML items.
import QtQuick.Controls 1.1
import Cura 1.1 as Cura

UM.Dialog
{
  id: nextChunkDialog

  width: 500 * screenScaleFactor
  height: 100 * screenScaleFactor
  minimumWidth: 500 * screenScaleFactor
  minimumHeight: 100 * screenScaleFactor

  Label
  {
    text: "something"
    wrapMode: Label.WordWrap
    width: Math.floor(parent.width * .9)
    anchors.horizontalCenter: nextChunkDialog.horizontalCenter
  }

  onRejected: {
    manager.rejected();
  }

  onAccepted: {
    manager.accepted();
  }

  rightButtons: [
    Button {
      text: "Reject"
      onClicked:
      {
        nextChunkDialog.reject()
        nextChunkDialog.hide()
      }
    },
    Button {
      text: "Accept"
      onClicked: {
        nextChunkDialog.accept()
        nextChunkDialog.hide()
      }
    }
  ]
}
