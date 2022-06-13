import UM 1.5 as UM // This allows you to use all of Uranium's built-in QML items.
import QtQuick 2.2 // This allows you to use QtQuick's built-in QML items.
import QtQuick.Controls 1.1
import Cura 1.1 as Cura

UM.Dialog
{
  id: fisnarProgressDialog

  width: 500 * screenScaleFactor
  minimumWidth: 500 * screenScaleFactor
  height: 150 * screenScaleFactor
  minimumHeight: 150 * screenScaleFactor

  Label
  {
    id: mainText
    anchors.horizontalCenter: fisnarProgressDialog.horizontalCenter
    text: "Printing in progress. Progress: "
  }

  Label
  {
    id: progressLabel
    anchors.left: mainText.right
    text: "--%"
  }

  function updateProgress() {
    progressLabel.text = main.getPrintingProgress
  }

  onRejected: {
    main.terminateFisnarControl();
  }

  rightButtons: [
    Button {
      text: "Terminate"
      onClicked:
      {
        fisnarProgressDialog.reject()
        fisnarProgressDialog.hide()
      }
    }
  ]
}
