import UM 1.5 as UM // This allows you to use all of Uranium's built-in QML items.
import QtQuick 2.2 // This allows you to use QtQuick's built-in QML items.
import QtQuick.Controls 1.1
import Cura 1.1 as Cura

UM.Dialog
{
  id: autoUploadErrorDialog
  width: 500 * screenScaleFactor
  height: 150 * screenScaleFactor
  minimumWidth: 500 * screenScaleFactor
  minimumHeight: 150 * screenScaleFactor

  Label
  {
    text: "Slicer output must be saved as a CSV file before starting the auto upload process."
    wrapMode: Label.WordWrap
    width: Math.floor(parent.width * .9)
    anchors.horizontalCenter: autoUploadDialog.horizontalCenter
  }

  rightButtons: [
    Button {
      text: "Ok"
      onClicked:
      {
        autoUploadErrorDialog.close()
      }
    }
  ]
}
