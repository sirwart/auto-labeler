import os
import shutil

from .data_dir import get_data_dir

def unlink():
    dir = get_data_dir()
    if os.path.exists(dir):
        shutil.rmtree(dir)