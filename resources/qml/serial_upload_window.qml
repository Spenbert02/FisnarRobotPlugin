import UM 1.5 as UM // This allows you to use all of Uranium's built-in QML items.
import QtQuick 2.2 // This allows you to use QtQuick's built-in QML items.
import QtQuick.Controls 1.1
import Cura 1.1 as Cura

UM.Dialog
{
  id: serialUploadDialog

  width: 500 * screenScaleFactor
  height: 150 * screenScaleFactor
  minimumWidth: 500 * screenScaleFactor
  minimumHeight: 150 * screenScaleFactor

  Label
  {
    text: main.getSerialUploadWindowText
    wrapMode: Label.WordWrap
    width: Math.floor(parent.width * .9)
    anchors.horizontalCenter: serialUploadDialog.horizontalCenter
  }

  onRejected: {
    main.cancelSerialUpload();
  }

  onAccepted: {
    main.startSerialUpload();
  }

  rightButtons: [
    Button {
      text: "Cancel"
      onClicked:
      {
        serialUploadDialog.reject()
        serialUploadDialog.hide()
      }
    },
    Button {
      text: "OK"
      onClicked: {
        serialUploadDialog.accept()
        serialUploadDialog.hide()
      }
    }
  ]
}
