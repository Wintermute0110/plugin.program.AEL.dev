# --- Python standard library ---
import sys, os

from main import *

sys.path.append('..')
from utils import *
from utils_kodi import *
from filename import *
from constants import *
from disk_IO import *

MIGRATION_CLASS_NAME = 'Migration_0_9_9'

class Migration_0_9_9(Migration):
        
    def execute(self, addon_path, addon_data_path):
        log_info('[Migration][0.9.9] Starting migration to version 0.9.9')
        
        categories_file = addon_data_path.pjoin('categories.xml')

        categories = {}
        launchers = {}
        fs_load_catfile(categories_file, categories, launchers)

        for key, launcher in launchers.iteritems():
            # does not yet contain launcher type?
            if not 'type' in launcher:
                self._set_launchertype(launcher)

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
        
        log_debug('Cannot set type for launcher "{}"'.format(name))
