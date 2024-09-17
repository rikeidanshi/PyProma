import os
from pathlib import Path

from PyProma_project_view import PyProma_project_view_script

if __name__ == "__main__":
    script_path = Path(__file__).resolve().parent.parent
    os.chdir(script_path)
    PyProma_project_view_script.ProjectView()
