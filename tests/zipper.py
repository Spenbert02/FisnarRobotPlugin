# a file for compressing necessary files into zip file to upload to cura packaging website
from zipfile import ZipFile
import os


if __name__ == "__main__":
    content_folder_path = "../"
    zip_file_path = "packaging_station\\FisnarRobotPlugin.zip"

    with ZipFile(zip_file_path, "w") as zip_obj:
        for top_folder, sub_folders, files in os.walk(content_folder_path):
            if "VirtEnv" not in top_folder and "tests" not in top_folder and "pycache" not in top_folder:  # disregarding virtual environment folder
                for filename in files:
                    file_path = os.path.join(top_folder, filename)
                    zip_obj.write(file_path, os.path.join("FisnarRobotPlugin", os.path.relpath(file_path, content_folder_path)))
