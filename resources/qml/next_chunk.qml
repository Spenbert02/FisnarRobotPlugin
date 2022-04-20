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
    id: informativeText
    text: manager.getCurrentMessage
    wrapMode: Label.WordWrap
    width: Math.floor(parent.width * .9)
    anchors.horizontalCenter: nextChunkDialog.horizontalCenter
  }

  onRejected: {
    manager.terminate();
  }

  rightButtons: [
    Button {
      text: "Terminate"
      onClicked:
      {
        nextChunkDialog.reject()
        nextChunkDialog.hide()
      }
    },
    Button {
      id: nextSegmentButton
      text: manager.getRightButtonText
      onClicked: {
        manager.rightButtonPressed()
        nextSegmentButton.text = manager.getRightButtonText
        informativeText.text = manager.getCurrentMessage
      }
    }
  ]
}
