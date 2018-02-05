# --- Python standard library ---
import sys, os

from main import *

sys.path.append('..')
from utils import *
from utils_kodi import *
from filename import *
from disk_IO import *

MIGRATION_CLASS_NAME = 'Migration_0_9_9'

class Migration_0_9_9(Migration):
        
    def execute(self, addon_path, addon_data_path):
        log_info('[Migration][0.9.9] Starting migration to version 0.9.9')
        
        categories_file = addon_data_path.pjoin('categories.xml')

        categories = {}
        launchers = {}
        fs_load_catfile(categories_file, categories, launchers)



