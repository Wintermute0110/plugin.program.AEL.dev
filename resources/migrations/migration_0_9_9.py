# --- Python standard library ---
import sys, os

from main import *

current_dir = os.path.dirname(os.path.abspath(__file__))
resources_dir = os.path.abspath(os.path.join(current_dir, os.pardir))
sys.path.append(resources_dir)
from .. import *

from utils import *
from utils_kodi import *
from filename import *
from constants import *
from disk_IO import *

MIGRATION_CLASS_NAME = 'Migration_0_9_9'

#
# Release 0.9.9
# This migration will do the following upgrade actions:
#   - Add a 'type' field to each launcher, guessing the correct launcher type.
#   - todo
#
class Migration_0_9_9(Migration):
        
    def execute(self, addon_path, addon_data_path):
        log_info('[Migration][0.9.9] Starting migration')
        
        categories_file = addon_data_path.pjoin('categories.xml')

        categories = {}
        launchers = {}
        fs_load_catfile(categories_file, categories, launchers)

        for key, launcher in launchers.iteritems():
            # does not yet contain launcher type?
            if not 'type' in launcher:
                self._set_launchertype(launcher)

        log_info('[Migration][0.9.9] Finished migration')

    def _set_launchertype(self, launcher):

        application = KodiFileName(launcher['application'])
        name = launcher['m_name']

        if application.getOriginalPath() == RETROPLAYER_LAUNCHER_APP_NAME:
            log_debug('Setting launcher "{}" with type RETROPLAYER'.format(name))
            launcher['type'] = LAUNCHER_RETROPLAYER
            return

        if application.getOriginalPath() == LNK_LAUNCHER_APP_NAME:
            log_debug('Setting launcher "{}" with type LNK'.format(name))
            launcher['type'] = LAUNCHER_LNK
            return

        if 'rompath' in launcher and launcher['rompath'] != '':
            log_debug('Setting launcher "{}" with type ROM LAUNCHER'.format(name))
            launcher['type'] = LAUNCHER_ROM
            return
        
        launcher['type'] = LAUNCHER_STANDALONE
        log_debug('Setting launcher "{}" with type STANDALONE'.format(name))
