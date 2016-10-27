
import sys, os, fnmatch, string

class Path:

    def __init__(self, pathString):

        self.originalPath = pathString
        self.path = pathString

        self.__parseCurrentPath()

    def __parseCurrentPath(self):

        if self.originalPath.lower().startswith('smb:'):
            self.path = self.path.replace('smb:', '')
            self.path = self.path.replace('SMB:', '')
            self.path = self.path.replace('//', '\\\\')
            self.path = self.path.replace('/', '\\')

    def join(self, subPath):
        self.path = os.path.join(self.path, subPath)
        self.originalPath = os.path(self.originalPath, subPath)

    def getSubPath(self, subPath):
        actualSubPath = os.path.join(self.originalPath, subPath)
        child = Path(actualSubPath)
        return child

    def scanFilesInPath(self, mask):
        files = []
        filenames = os.listdir(self.path)
        for filename in fnmatch.filter(filenames, mask):
            files.append(os.path.join(self.path, filename))

        return files

    def recursiveScanFilesInPath(self, mask):
        files = []
        for root, dirs, foundfiles in os.walk(self.path):
            for filename in fnmatch.filter(foundfiles, mask):
                files.append(os.path.join(root, filename))

        return files

    def fileExists(self):
        return os.path.isfile(self.path)

    def create(self):
        if not os.path.exists(self.path): 
            os.makedirs(self.path)

    def getCurrentPath(self):
        return self.path.decode('utf-8')

    def getOriginalPath(self):
        return self.originalPath.decode('utf-8')