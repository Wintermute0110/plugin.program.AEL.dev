# -*- coding: utf-8 -*-
#
import logging

from ael.utils import kodilogging, kodi
from resources.lib.globals import addon_id, addon_version
from resources.lib.services import AppService

kodilogging.config()
logger = logging.getLogger(__name__)

if __name__ == '__main__':    
    logger.debug("Loading '%s' version '%s'" % (addon_id, addon_version))
    
    try:
        AppService().run()
    except Exception as ex:
        logger.fatal('Exception in plugin', exc_info=ex)
        kodi.notify_error("General failure")

    logger.debug("'%s' shutting down." % addon_id)