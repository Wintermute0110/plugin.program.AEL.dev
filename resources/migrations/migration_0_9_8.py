# --- Python standard library ---
import sys, os

from main import *

sys.path.append('..')
from utils import *
from utils_kodi import *

MIGRATION_CLASS_NAME = 'Migration_0_9_8'

class Migration_0_9_8(Migration):
        
    def execute(self, addon_path, addon_data_path):
        log_info('[Migration][0.9.8] Just for testing purposes')

