from abc import ABCMeta, abstractmethod

from resources.launchers import *
from resources.romsets import *
from resources.executors import *
from resources.scrapers import *

#from ressources.utils import *
from resources.utils_kodi import *
from resources.filename import *

class FakeRomSetRepository(RomSetRepository):
    
    def __init__(self, roms):
        self.roms = roms
    
    def find_by_launcher(self, launcher):
        return self.roms
    
    def save_rom_set(self, launcher, roms):
        self.roms = roms

    def delete_by_launcher(self, launcher):
        self.roms = {}      

class FakeExecutor(Executor):
    
    def getActualApplication(self):
        return self.actualApplication

    def getActualArguments(self):
        return self.actualArgs

    def execute(self, application, arguments, non_blocking):
        self.actualApplication = application
        self.actualArgs = arguments
        pass    

class FakeClass():

    def FakeMethod(self, value, key, launcher):
        self.value = value

class FakeFile(KodiFileName):
    
    def __init__(self, pathString):
        self.fakeContent  = ''
        self.originalPath = pathString
        self.path         = pathString

    def setFakeContent(self, content):
        self.fakeContent = content

    def getFakeContent(self):
        return self.fakeContent
    
    def readAllUnicode(self, encoding='utf-8'):
        contents = self.fakeContent
        return unicode(contents, encoding)

    def write(self, bytes):
       self.fakeContent = self.fakeContent + bytes
      
    def writeAll(self, bytes, flags='w'):
       self.fakeContent = self.fakeContent + bytes
       
    def pjoin(self, *args):
        return self

class FakeScraper(Scraper):
    
    def __init__(self, rom_data_to_apply = None):
        self.rom_data_to_apply = rom_data_to_apply

    def getName(self):
        return 'FakeScraper'

    def _getCandidates(self, searchTerm, romPath, rom):
        return ['fake']

    def _loadCandidate(self, candidate, romPath):
        pass

    def _applyCandidate(self, romPath, rom):

        if self.rom_data_to_apply :
            rom.set_custom_attribute('m_name',      self.rom_data_to_apply['m_name'] if 'm_name' in self.rom_data_to_apply else '')
            rom.set_custom_attribute('m_year',      self.rom_data_to_apply['m_year'] if 'm_year' in self.rom_data_to_apply else '')    
            rom.set_custom_attribute('m_genre',     self.rom_data_to_apply['m_genre'] if 'm_genre' in self.rom_data_to_apply else '')  
            rom.set_custom_attribute('m_developer', self.rom_data_to_apply['m_developer']if 'm_developer' in self.rom_data_to_apply else '')
            rom.set_custom_attribute('m_plot',      self.rom_data_to_apply['m_plot'] if 'm_plot' in self.rom_data_to_apply else '')
        else:
            rom.set_name(romPath.getBase_noext())

        return True
