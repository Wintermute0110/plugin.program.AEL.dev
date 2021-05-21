# -*- coding: utf-8 -*-
#
import logging

from resources.lib.utils import kodilogging, text
from resources.lib.globals import addon_id, addon_version
from resources.app.services import AppService

kodilogging.config()
logger = logging.getLogger(__name__)

if __name__ == '__main__':    
    logger.debug("Loading '%s' version '%s'" % (addon_id, addon_version))
    
    try:
        AppService().run()
    except Exception as ex:
        message = text.createError(ex)
        logger.fatal(message)

    logger.debug("'%s' shutting down." % addon_id)