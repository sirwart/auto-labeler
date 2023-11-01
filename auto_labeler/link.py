import os
import shutil

from .data_dir import get_data_dir
from .gmail import get_creds

def link():
    get_creds()

def unlink():
    dir = get_data_dir()
    if os.path.exists(dir):
        shutil.rmtree(dir)