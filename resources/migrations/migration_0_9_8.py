# --- Python standard library ---
import sys, os

from main import *

current_dir = os.path.dirname(os.path.abspath(__file__))
resources_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
sys.path.append(resources_dir)
from .. import *

from utils import *
from utils_kodi import *

MIGRATION_CLASS_NAME = 'Migration_0_9_8'

#
# Release 0.9.8
# This migration will has no actions for now.
#
class Migration_0_9_8(Migration):
    def execute(self, addon_path, addon_data_path):
        log_info('[Migration][0.9.8] Migration start / end')
