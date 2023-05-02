import os

from akl.utils import io
class FakeFile(io.FileName):

    def __init__(self, pathString):
        self.fakeContent  = ''
        self.path_str     = pathString
        self.path_tr      = pathString       

        self.exists = self.exists_fake
        self.write = self.write_fake

    def setFakeContent(self, content):
        self.fakeContent = content
        
    def getFakeContent(self):
        return self.fakeContent   

    def loadFileToStr(self, encoding = 'utf-8'):
        return self.fakeContent     

    def readAllUnicode(self, encoding='utf-8'):
        contents = self.fakeContent
        return contents

    def saveStrToFile(self, data_str, encoding = 'utf-8'):
        self.fakeContent = data_str       

    def write_fake(self, bytes):
        self.fakeContent = self.fakeContent + bytes

    def open(self, mode):pass
    def close(self): pass
    
    def makedirs(self): pass
    
    def getDirAsFileName(self):
        return FakeFile(self.getDir())
    
    def writeAll(self, bytes, flags='w'):
        self.fakeContent = self.fakeContent + bytes

    def pjoin(self, *args):
        child = FakeFile(self.path_str)
        child.setFakeContent(self.fakeContent)
        for arg in args:
            child.path_str = os.path.join(child.path_str, arg)
            child.path_tr = os.path.join(child.path_tr, arg)
            
        return child      

    def changeExtension(self, targetExt):
        switched_fake = super(FakeFile, self).changeExtension(targetExt)
        switched_fake = FakeFile(switched_fake.getPath())
        
        switched_fake.setFakeContent(self.fakeContent)
        return switched_fake

    def exists_fake(self):
        return True

    def scanFilesInPathAsFileNameObjects(self, mask = '*.*'):
        return []
    
class FakeAddon(object):

    def __init__(self, data: dict):
        self.data = data
        
    def getAddonInfo(self, field):
        return self.data[field]
    
    def getSetting(self, key):
        return self.data[key]

    def getSettingString(self, key):
        return str(self.getSetting(key))
    
class FakeUnitOfWork():
    
    def __init__(self):
        self.executed_files = []
    
    def migrate_database(self, migration_files, new_db_version):
        for f in migration_files:
            self.executed_files.append(f.getPath())