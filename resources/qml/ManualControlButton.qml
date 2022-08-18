// manualControlButton is a wrapper for the Cura.SecondaryButton item, pretty much just
// so the button changes color when pressed down.

import QtQuick 2.10
import QtQuick.Layouts 1.1
import QtQuick.Controls 2.15

import UM 1.5 as UM
import Cura 1.0 as Cura

Cura.SecondaryButton {
  // constant properties, set on startup from Cura.SecondaryButton definiton file (just for future-proofing)
  property color unclickedTextColor
  property color unclickedOutlineColor
  property color unclickedBackgroundColor

  property color clickedTextColor
  property color clickedOutlineColor
  property color clickedBackgroundColor

  Component.onCompleted: {  // getting base colors on startup
    unclickedTextColor = textColor;
    clickedTextColor = Qt.tint(unclickedTextColor, Qt.rgba(0, 0, 0, 0));  // tint has no effect - can be changed

    unclickedOutlineColor = outlineColor;
    clickedOutlineColor = Qt.tint(unclickedOutlineColor, Qt.rgba(0, 0, 0, 0));  // another tint that has no effect

    unclickedBackgroundColor = hoverColor;
    clickedBackgroundColor = Qt.tint(unclickedBackgroundColor, Qt.rgba(0, 0, 0, .1));
  }

  onPressed: {
    textColor = clickedTextColor;
    outlineColor = clickedOutlineColor;
    hoverColor = clickedBackgroundColor;
  }

  onReleased: {
    textColor = unclickedTextColor;
    outlineColor = unclickedOutlineColor;
    hoverColor = unclickedBackgroundColor;
  }
}
