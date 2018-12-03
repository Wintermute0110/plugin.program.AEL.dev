from abc import ABCMeta, abstractmethod

from resources.objects import *
from resources.utils import *
from resources.scrap import *

class FakeRomSetRepository(ROMSetRepository):
    
    def __init__(self, roms):
        self.roms = roms
    
    def find_by_launcher(self, launcher):
        return self.roms
    
    def save_rom_set(self, launcher, roms):
        self.roms = roms

    def delete_all_by_launcher(self, launcher):
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

    def switchExtension(self, targetExt):
        switched_fake = super(FakeFile, self).switchExtension(targetExt)
        switched_fake.setFakeContent(self.fakeContent)
        return switched_fake

    #backwards compatiblity
    def __create__(self, path):
        return FakeFile(path)

class FakeScraper(Scraper):
    
    def __init__(self, settings, launcher, rom_data_to_apply = None):
        self.rom_data_to_apply = rom_data_to_apply
        scraper_settings = ScraperSettings(1,1,False,True)
        super(FakeScraper, self).__init__(scraper_settings, launcher, True, []) 

    def getName(self):
        return 'FakeScraper'

    def _get_candidates(self, searchTerm, romPath, rom):
        return ['fake']

    def _load_metadata(self, candidate, romPath, rom):
        if self.rom_data_to_apply :
            self.gamedata['title']      = self.rom_data_to_apply['m_name'] if 'm_name' in self.rom_data_to_apply else ''
            self.gamedata['year']      = self.rom_data_to_apply['m_year'] if 'm_year' in self.rom_data_to_apply else ''   
            self.gamedata['genre']     = self.rom_data_to_apply['m_genre'] if 'm_genre' in self.rom_data_to_apply else ''
            self.gamedata['developer'] = self.rom_data_to_apply['m_developer']if 'm_developer' in self.rom_data_to_apply else ''
            self.gamedata['plot']      = self.rom_data_to_apply['m_plot'] if 'm_plot' in self.rom_data_to_apply else ''
        else:
            self.gamedata['title'] = romPath.getBase_noext()

    
    def _load_assets(self, candidate, romPath, rom):
        pass
        