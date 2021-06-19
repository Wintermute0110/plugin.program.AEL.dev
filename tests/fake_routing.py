# TEST MOCK LIBRARY OF routing.py

class Plugin(object):

    def __init__(self, base_url=None):
        self.base_url = "plugin://mock.plugin"
        
    def route_for(self, path):
        return '{}/{}'.format(self.base_url, path)

    def url_for(self, func, *args, **kwargs):
        return '{}/{}'.format(self.base_url, func.__name__)

    def url_for_path(self, path):
        return '{}/{}'.format(self.base_url, path)

    def route(self, pattern):
        pass

    def add_route(self, func, pattern):
        pass

    def run(self, argv=None):
        pass

    def redirect(self, path):
        pass