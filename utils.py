import os

def create_dir(adir: str):
    os.makedirs(adir, exist_ok=True)
