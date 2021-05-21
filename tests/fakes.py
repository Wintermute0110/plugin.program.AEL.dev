# from resources.objects import *
# from resources.utils import *
# from resources.scrap import *

class FakeAddon(object):

    def __init__(self, data: dict):
        self.data = data
        
    def getAddonInfo(self, field):
        return self.data[field]
    
    def getSetting(self, key):
        return self.data[key]

# class FakeRomSetRepository(ROMSetRepository):
    
#     def __init__(self, roms):
#         self.roms = roms
    
#     def find_by_launcher(self, launcher):
#         return self.roms
    
#     def save_rom_set(self, launcher, roms):
#         self.roms = roms

#     def delete_all_by_launcher(self, launcher):
#         self.roms = {}      

# class FakeExecutor(ExecutorABC):
    
#     def __init__(self):
#         self.actualApplication = None
#         self.actualArgs = None
#         super(FakeExecutor, self).__init__(None)
    
#     def getActualApplication(self):
#         return self.actualApplication

#     def getActualArguments(self):
#         return self.actualArgs

#     def execute(self, application, arguments, non_blocking):
#         self.actualApplication = application
#         self.actualArgs = arguments
#         pass    

# class FakeClass():

#     def FakeMethod(self, value, key, launcher):
#         self.value = value

# class FakeFile(FileName):
    
#     def __init__(self, pathString):
#         self.fakeContent  = ''
#         self.path_str     = pathString
#         self.path_tr      = pathString
        
#         self.exists = self.exists_fake
#         self.write = self.write_fake

#     def setFakeContent(self, content):
#         self.fakeContent = content

#     def getFakeContent(self):
#         return self.fakeContent
    
#     def loadFileToStr(self, encoding = 'utf-8'):
#         return self.fakeContent
        
#     def readAllUnicode(self, encoding='utf-8'):
#         contents = self.fakeContent
#         return contents

#     def saveStrToFile(self, data_str, encoding = 'utf-8'):
#         self.fakeContent = data_str
        
#     def write_fake(self, bytes):
#        self.fakeContent = self.fakeContent + bytes

#     def open(self, mode):
#         pass
    
#     def close(self):
#         pass
      
#     def writeAll(self, bytes, flags='w'):
#        self.fakeContent = self.fakeContent + bytes
       
#     def pjoin(self, *args):
#         child = FakeFile(self.path_str)
#         child.setFakeContent(self.fakeContent)
#         for arg in args:
#             child.path_str = os.path.join(child.path_str, arg)
#             child.path_tr = os.path.join(child.path_tr, arg)

#         return child    
    
#     def switchExtension(self, targetExt):
#         switched_fake = super(FakeFile, self).switchExtension(targetExt)
#         #switched_fake = FakeFile(switched_type.getPath())
#         switched_fake.setFakeContent(self.fakeContent)
#         return switched_fake

#     def exists_fake(self):
#         return True
    
#     def scanFilesInPathAsFileNameObjects(self, mask = '*.*'):
#         return []
    
#     #backwards compatiblity
#     def __create__(self, path):
#         return FakeFile(path)
# class FakeScraper(Scraper):
    
#     def __init__(self, settings, launcher, rom_data_to_apply = None):
#         self.rom_data_to_apply = rom_data_to_apply
#         scraper_settings = ScraperSettings(1,1,False,True)
#         super(FakeScraper, self).__init__(scraper_settings, launcher, True, []) 

#     def getName(self):
#         return 'FakeScraper'

#     def supports_asset_type(self, asset_info):
#         return True

#     def _get_candidates(self, searchTerm, romPath, rom):
#         return ['fake']
            
#     def _load_metadata(self, candidate, romPath, rom):
#         gamedata = self._new_gamedata_dic()

#         if self.rom_data_to_apply :
#             gamedata['title']     = self.rom_data_to_apply['m_name'] if 'm_name' in self.rom_data_to_apply else ''
#             gamedata['year']      = self.rom_data_to_apply['m_year'] if 'm_year' in self.rom_data_to_apply else ''   
#             gamedata['genre']     = self.rom_data_to_apply['m_genre'] if 'm_genre' in self.rom_data_to_apply else ''
#             gamedata['developer'] = self.rom_data_to_apply['m_developer']if 'm_developer' in self.rom_data_to_apply else ''
#             gamedata['plot']      = self.rom_data_to_apply['m_plot'] if 'm_plot' in self.rom_data_to_apply else ''
#         else:
#             gamedata['title'] = romPath.getBase_noext()
    
#     def _load_assets(self, candidate, romPath, rom):
#         pass
        