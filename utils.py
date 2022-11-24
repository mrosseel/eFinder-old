import os
from pathlib import Path

def create_dir(adir: str):
    create_path(Path(adir)) 

def create_path(apath: Path):
    os.makedirs(apath, exist_ok=True)
