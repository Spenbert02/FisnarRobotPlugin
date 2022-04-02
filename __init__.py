from . import FisnarCSVWriter
from . import FisnarCSVParameterExtension


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
    "extension": FisnarCSVParameterExtension.FisnarCSVParameterExtension(),
    "mesh_writer": FisnarCSVWriter.FisnarCSVWriter()
    }
