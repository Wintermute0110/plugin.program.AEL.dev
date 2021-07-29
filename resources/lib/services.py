import threading
import logging
import sys
import json

import xbmc

from resources.lib import globals
from resources.lib.repositories import UnitOfWork
from resources.lib.commands.mediator import AppMediator
import resources.lib.commands

from ael.utils import io, kodi

logger = logging.getLogger(__name__)

class AppService(object):

    def __init__(self):
        
        threading.Thread.name = 'ael'

        globals.g_bootstrap_instances()
        
        self.queue = []
        self.monitor = AppMonitor(addon_id=globals.addon_id, action=self.queue.append)

    def _execute_service_actions(self, action_data):
        cmd = action_data['action']
        args = action_data['data']
        AppMediator.sync_cmd(cmd, args)

    def run(self):        
        # --- Some debug stuff for development ---
        logger.info('------------ Called Advanced Emulator Launcher : Service ------------')
        logger.debug('sys.platform   "{}"'.format(sys.platform))
        if io.is_android(): logger.debug('OS             "Android"')
        if io.is_windows(): logger.debug('OS             "Windows"')
        if io.is_osx():     logger.debug('OS             "OSX"')
        if io.is_linux():   logger.debug('OS             "Linux"')
        logger.debug('Python version "' + sys.version.replace('\n', '') + '"')
        logger.debug('addon.id         "{}"'.format(globals.addon_id))
        logger.debug('addon.version    "{}"'.format(globals.addon_version))
        logger.debug("Starting AEL service")

        uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
        if not uow.check_database():
            logger.info("No database present. Going to create database file.")
            kodi.notify('Creating new AEL database')
            uow.create_empty_database(globals.g_PATHS.DATABASE_SCHEMA_PATH)
            logger.info("Database created.")
        
        # SCAN FOR ADDONS
        self._execute_service_actions({'action': 'SCAN_FOR_ADDONS', 'data': None})
        # REBUILD VIEWS
        self._execute_service_actions({'action': 'RENDER_VIEWS', 'data': None})
        
        logger.debug("Processing service events")
        while not self.monitor.abortRequested():
            
            self.monitor.process_events()
            while len(self.queue) and (not self.monitor.abortRequested()):
                data = self.queue.pop(0)
                self._execute_service_actions(data)

            if self.monitor.waitForAbort(0.5):
                # abort requested, end service
                break

        logger.debug("Shutting down AEL service")
        del self.monitor

class AppMonitor(xbmc.Monitor):
    
    def __init__(self, *args, **kwargs):
        self.addon_id = kwargs['addon_id']
        self.action = kwargs['action']
        logger.debug("[AEL Monitor] Initalized.")

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