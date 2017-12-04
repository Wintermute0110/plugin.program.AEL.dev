from abc import ABCMeta, abstractmethod

from resources.launchers import *
from resources.romsets import *
from resources.executors import *
from resources.scrapers import *

from resources.utils import *
from resources.utils_kodi import *

class FakeRomSet(RomSet):

    def __init__(self, rom, roms = None):
        self.rom = rom
        self.roms = roms

    def romSetFileExists(self):
        return True
            
    def loadRoms(self):
        if self.roms is None:
            return {}

        return self.roms

    def loadRomsAsList(self):
        if self.roms is None:
            return []

        return self.roms

    def loadRom(self, romId):
        return self.rom

    def saveRoms(self, roms):
        pass

class FakeExecutor(Executor):
    
    def execute(self, application, arguments, non_blocking):
        self.actualApplication = application
        self.actualArgs = arguments
        pass    

class FakeClass():

    def FakeMethod(self, value, launcher):
        self.value = value

class FakeFile(FileName):
    
    def __init__(self, pathString):
        self.fakeContent  = ''
        self.originalPath = pathString
        self.path         = pathString

    def setFakeContent(self, content):
        self.fakeContent = content

    def getFakeContent(self):
        return self.fakeContent

    def write(self, bytes):
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
            rom['m_name']      = self.rom_data_to_apply['m_name'] if 'm_name' in self.rom_data_to_apply else ''
            rom['m_year']      = self.rom_data_to_apply['m_year'] if 'm_year' in self.rom_data_to_apply else ''     
            rom['m_genre']     = self.rom_data_to_apply['m_genre'] if 'm_genre' in self.rom_data_to_apply else ''  
            rom['m_developer'] = self.rom_data_to_apply['m_developer']if 'm_developer' in self.rom_data_to_apply else ''
            rom['m_plot']      = self.rom_data_to_apply['m_plot'] if 'm_plot' in self.rom_data_to_apply else ''     
        else:
            rom['m_name'] = romPath.getBase_noext()

        return True
