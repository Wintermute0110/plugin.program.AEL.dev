# -*- coding: utf-8 -*-
#
# Advanced Kodi Launcher 
# (Build Tool)
#
# This tool publishes the local dev folder as a proper
# addon to your kodi test environment.
# 

# --- Python standard library ---
from __future__ import unicode_literals
from __future__ import division

import sys
import glob
import shutil
import json
import logging

logger = logging.getLogger(__name__)

def publish():
    
    with open('data.txt') as json_file:
        data = json.load(json_file)

    for file in glob.glob(r'C:/*.txt'):
        print(file)
        shutil.copy(file, dest_dir)

try:
    publish()
except Exception as ex:
    logger.fatal('Exception in tool', exc_info=ex)