# --- Python compiler flags ---
from __future__ import unicode_literals

# --- Python standard library ---
from abc import ABCMeta, abstractmethod
from distutils.version import StrictVersion

migrations = [Migration_0_9_8()]

# Executes the migrations 
def execute_migrations():

    current_migrated_version = StrictVersion("0.0.0")

    for migration in migrations:
        migration_version = migration.get_migration_version()

        if migration_version < current_migrated_version:
            migration.execute()
            current_migrated_version = mig


class Migration():
    __metaclass__ = ABCMeta

    @abstractmethod
    def get_migration_version(self):
        return StrictVersion("0.0.0")
    
    @abstractmethod
    def execute(self):
        pass


class Migration_0_9_8(Migration):

    def get_migration_version(self):
        return StrictVersion("0.9.8")
    
    def execute(self):
        pass