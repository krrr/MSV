import sys
if sys.path[0].endswith('.zip'):  # python embeddable version
    sys.path.insert(0, '')
import multiprocessing
from msv import main_entry

if __name__ == "__main__":  # required by multiprocessing on Windows
    multiprocessing.freeze_support()
    sys.exit(main_entry())
