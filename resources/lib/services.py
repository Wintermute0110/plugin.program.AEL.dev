import threading
import logging
import sys
import json

from datetime import datetime
from distutils.version import LooseVersion

import xbmc

from resources.lib import globals
from resources.lib.repositories import UnitOfWork
from resources.lib.webservice import WebService
from resources.lib.commands.mediator import AppMediator
import resources.lib.commands
        
from akl.utils import io, kodi
from akl import settings

logger = logging.getLogger(__name__)

class AppService(object):

    def __init__(self):
        
        threading.Thread.name = 'akl'

        globals.g_bootstrap_instances()
        
        self.queue = []
        self.monitor = AppMonitor(addon_id=globals.addon_id, action=self.queue.append)

    def _execute_service_actions(self, action_data):
        cmd = action_data['action']
        args = action_data['data']
        AppMediator.sync_cmd(cmd, args)

    def run(self):        
        kodi.set_windowprop('akl_server_state', 'STARTING')
        
        # --- Some debug stuff for development ---
        logger.info('------------ Called Advanced Kodi Launcher : Service ------------')
        logger.debug('sys.platform   "{}"'.format(sys.platform))
        if io.is_android(): logger.debug('OS             "Android"')
        if io.is_windows(): logger.debug('OS             "Windows"')
        if io.is_osx():     logger.debug('OS             "OSX"')
        if io.is_linux():   logger.debug('OS             "Linux"')
        logger.debug('Python version "' + sys.version.replace('\n', '') + '"')
        logger.debug('addon.id         "{}"'.format(globals.addon_id))
        logger.debug('addon.version    "{}"'.format(globals.addon_version))
        logger.debug("Starting AKL service")

        uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
        if not uow.check_database():
            logger.info("No database present. Going to create database file.")
            self._initial_setup(uow)
            
        db_version = uow.get_database_version()
        current_version = kodi.get_addon_version()
        if db_version is None or LooseVersion(db_version) < LooseVersion(current_version):
            self._do_version_upgrade(uow, LooseVersion(db_version))
        
        if self._last_time_scanned_is_too_long_ago():
            self._perform_scans()
 
        # WEBSERVICE
        self.webservice = WebService()
        self.webservice.start()
                
        logger.debug("Processing service events")
        kodi.set_windowprop('akl_server_state', 'STARTED')
        while not self.monitor.abortRequested():
            
            self.monitor.process_events()
            while len(self.queue) and (not self.monitor.abortRequested()):
                data = self.queue.pop(0)
                self._execute_service_actions(data)

            if self.monitor.waitForAbort(0.5):
                # abort requested, end service
                break
    
        self.shutdown()

    def shutdown(self):
        logger.debug("Shutting down AKL service")        
        kodi.set_windowprop('akl_server_state', 'STOPPING')        
        
        self.webservice.stop()
        del self.monitor
        del self.webservice
        
        kodi.set_windowprop('akl_server_state', 'STOPPED')
        logger.debug("AKL service stopped")
        
    def _initial_setup(self, uow:UnitOfWork):
        kodi.notify('Creating new AKL database')
        uow.create_empty_database(globals.g_PATHS.DATABASE_SCHEMA_PATH)
        logger.info("Database created.")
        
        self._perform_scans()

    def _do_version_upgrade(self, uow:UnitOfWork, db_version:LooseVersion):
        migrations_files_available  = globals.g_PATHS.DATABASE_MIGRATIONS_PATH.scanFilesInPath("*.sql")
        migrations_files_to_execute = []
        for migration_file in migrations_files_available:
            if LooseVersion(migration_file.getBaseNoExt()) > db_version:
                migrations_files_to_execute.append(migration_file)
        
        migrations_files_to_execute.sort(key = lambda f: (LooseVersion(f.getBaseNoExt())))
        uow.migrate_database(migrations_files_to_execute)
    
    def _perform_scans(self):
        # SCAN FOR ADDONS
        self._execute_service_actions({'action': 'SCAN_FOR_ADDONS', 'data': None})
        # REBUILD VIEWS
        self._execute_service_actions({'action': 'RENDER_VIEWS', 'data': None})
        # Write to scan indicator
        globals.g_PATHS.SCAN_INDICATOR_FILE.writeAll(f'last scan all on {datetime.now()} ')

    def _last_time_scanned_is_too_long_ago(self):
        if not globals.g_PATHS.SCAN_INDICATOR_FILE.exists():
            return True
        
        min_days_ago = settings.getSettingAsInt('regeneration_days_period')
        if not min_days_ago or min_days_ago == 0: 
            logger.info('Automatic scan and view generation disabled.')
            return
        
        modification_timestamp = globals.g_PATHS.SCAN_INDICATOR_FILE.stat().st_mtime
        modification_time = datetime.fromtimestamp(modification_timestamp)
        
        then = modification_time.toordinal()
        now = datetime.now().toordinal()
        too_long_ago = (now - then) >= min_days_ago
        
        if too_long_ago:
            logger.info(f'Triggering automatic scan and view generation. Last scan was {now-then} days ago')
        else:
            logger.info(f'Skipping automatic scan and view generation. Last scan was {now-then} days ago')        
        return too_long_ago
        
class AppMonitor(xbmc.Monitor):
    
    def __init__(self, *args, **kwargs):
        self.addon_id = kwargs['addon_id']
        self.action = kwargs['action']
        logger.debug("[AKL Monitor] Initalized.")

    def process_events(self):
        pass

    def onNotification(self, sender, method, data):
        if sender != self.addon_id:
            return

        logger.info(data)
        data_obj = None
        try:
            data_obj = json.loads(data)
        except:
            logger.error('Failed to load arguments as json')

        action_data = {
            'action': method.split('.')[1].upper(),
            'data': data_obj
        }
        self.action(action_data)