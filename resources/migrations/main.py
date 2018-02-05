# --- Python compiler flags ---
from __future__ import unicode_literals

# --- Python standard library ---
from abc import ABCMeta, abstractmethod

#
# Migration scripts should consist of a class that implements
# the 'Migration' base class seen below. 
# Furthermore it should have a field called 'MIGRATION_CLASS_NAME' 
# where the value is set to the name of the class. 
# 
# Like:
# MIGRATION_CLASS_NAME = 'Migration_0_9_8'
#
class Migration():
    __metaclass__ = ABCMeta
    
    @abstractmethod
    def execute(self, addon_path, addon_data_path):
        pass