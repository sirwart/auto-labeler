import appdirs
import os

def get_data_dir(create_if_missing=False):
    def get_data_dir_aux():
        if 'AUTO_LABELER_DATA_DIR' in os.environ:
            return os.environ['AUTO_LABELER_DATA_DIR']
        else:
            return appdirs.user_data_dir('auto-labeler')
    dir = get_data_dir_aux()
    if create_if_missing and not os.path.exists(dir):
        os.mkdir(dir)
    return dir