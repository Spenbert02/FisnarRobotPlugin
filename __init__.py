from . import FisnarCSVWriter
from . import FisnarRobotExtension


def getMetaData():
    return {
        "mesh_writer": {
            "output": [{
                "mime_type": "text/csv",
                "mode": FisnarCSVWriter.FisnarCSVWriter.OutputMode.TextMode,
                "extension": "csv",
                "description": "Fisnar Command CSV"
                }]
        }
    }


def register(app):
    return {
    "extension": FisnarRobotExtension.FisnarRobotExtension(),
    "mesh_writer": FisnarCSVWriter.FisnarCSVWriter()
    }
