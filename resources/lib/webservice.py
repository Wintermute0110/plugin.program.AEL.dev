# -*- coding: utf-8 -*-
#
# Advanced Emulator Launcher: Webservice for API communication with plugins
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# Based on the webservice implementation by angelblue05 for plugin.video.emby.
#
# --- Python standard library ---
from __future__ import unicode_literals
from __future__ import division

import logging
import json
import threading
import socket

from urllib.parse import parse_qsl
from http.server import HTTPServer, BaseHTTPRequestHandler
from http.client import HTTPConnection

# AEL modules
from resources.lib import globals, apiqueries
from resources.lib.commands import api_commands

logger = logging.getLogger(__name__)

#################################################################################################
class WebService(threading.Thread):
    
    HOST = globals.WEBSERVER_HOST
    PORT = globals.WEBSERVER_PORT
    
    ''' Run a webservice for api communication.
    '''
    def __init__(self):
        self.server = None
        threading.Thread.__init__(self)

    def is_alive(self):

        ''' Called to see if the webservice is still responding.
        '''
        alive = True
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            s.connect((WebService.HOST, WebService.PORT))
            s.sendall("")
        except Exception as error:
            logger.fatal('Exception in webservice.is_alive {}'.format(str(error)))
            if 'Errno 61' in str(error) or 'WinError 10061' in str(error):
                alive = False
        finally:
            s.close()

        return alive

    def stop(self, check_alive = False):
        
        if check_alive and not self.is_alive():
            logger.info("Webservice not running, so stopping not needed.")
            return
        
        ''' Called when the thread needs to stop
        '''
        try:
            logger.info("Stopping AEL webservice({}:{})".format(WebService.HOST, WebService.PORT))
            conn = HTTPConnection("{}:{}".format(WebService.HOST, WebService.PORT))
            conn.request("QUIT", "/")
            conn.getresponse()
        except Exception as error:
            logger.error('Exception in webservice.stop(): {}'.format(str(error)))
        
        logger.info("Webservice stopped")

    def run(self):

        ''' Called to start the webservice.
        '''
        self.stop(check_alive=True)

        logger.info("Startup AEL webservice({}:{})".format(WebService.HOST, WebService.PORT))
        server = AelHttpServer((WebService.HOST, WebService.PORT), RequestHandler)
        
        try:
            server.serve_forever()
        except Exception as error:

            if '10053' not in error: # ignore host diconnected errors
                logger.fatal('Exception in webservice', exc_info=error)

        logger.debug("Webservice thread end")


class AelHttpServer(HTTPServer):
    ''' Http server that reacts to self.stop flag.
    '''
    def serve_forever(self):
        ''' Handle one request at a time until stopped.
        '''
        self.stop = False
        while not self.stop:
            self.handle_request()


class RequestHandler(BaseHTTPRequestHandler):

    ''' Http request handler. Do not use logger here,
        it will hang requests in Kodi > show information dialog.
    '''
    timeout = 0.5

    def log_message(self, format, *args):

        ''' Mute the webservice requests.
        '''
        pass

    def handle(self):

        ''' To quiet socket errors with 404.
        '''
        try:
            BaseHTTPRequestHandler.handle(self)
        except Exception as error:
            pass

    def do_QUIT(self):

        ''' send 200 OK response, and set server.stop to True
        '''
        self.send_response(200)
        self.end_headers()
        self.server.stop = True

    def get_params(self):

        ''' Get the params
        '''
        try:
            path = self.path[1:]

            if '?' in path:
                path = path.split('?', 1)[1]

            params = dict(parse_qsl(path))
        except Exception:
            params = {}

        return params

    def do_HEAD(self):

        ''' Called on HEAD requests
        '''
        self.handle_request(True)
        return

    def do_GET(self):

        ''' Called on GET requests
        '''
        self.handle_request()
        return
    
    def do_POST(self):

        ''' Called on POST requests
        '''
        self.handle_request()
        return
        
    def handle_request(self, headers_only=False):

        '''Send headers and reponse
        '''
        try:
            logger.debug('ael.webservice: Processing path "{}"'.format(self.path))
            api_path = self.path.lower()
            if headers_only:
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()

            elif 'query/' in api_path:
               self.handle_queries(api_path)
            elif 'store/' in api_path:
                if self.handle_posts(api_path):
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                else:
                    logger.warn('Not handeld: {}'.format(self.path))
                    raise Exception("UnknownRequest")
            else:
                logger.warn(self.path)
                raise Exception("UnknownRequest")

        except Exception as error:
            logger.fatal('ael.webservice exception processing path', exc_info=error)
            self.send_error(500, 'AEL.webservice - Exception occurred: {}'.format(str(error)))
            
        logger.debug('ael.webservice/{}/{}'.format(str(id(self)), int(not headers_only)))
        return

    def handle_queries(self, api_path):
        response_data = None
        obj = 'Not specified'
        
        if 'query/rom/' in api_path:
            obj = 'ROM'
            response_data = self.handle_rom_queries(api_path)
        elif 'query/romcollection/':
            obj = 'ROMCollection'
            response_data = self.handle_romcollection_queries(api_path)
                        
        if response_data is None: 
            self.send_response(404)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write('{} entity not found'.format(obj))
            return
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(response_data.encode(encoding='utf_8'))

    def handle_rom_queries(self, api_path):
        params = self.get_params()
        id = params.get('id')
        
        if 'rom/launcher/settings/' in api_path:
            return apiqueries.qry_get_rom_launcher_settings(id, params.get('launcher_id'))
        if 'rom/' in api_path:
            return apiqueries.qry_get_rom(id)
        
        return None
        
    def handle_romcollection_queries(self, api_path):
        params = self.get_params()
        id = params.get('id')
        
        if 'romcollection/launcher/settings/' in api_path:
            return apiqueries.qry_get_collection_launcher_settings(id, params.get('launcher_id'))
        if 'romcollection/scanner/settings/' in api_path:
            return apiqueries.qry_get_collection_scanner_settings(id, params.get('scanner_id'))
        if 'romcollection/launchers/' in api_path:
            return apiqueries.qry_get_launchers(id)
        if 'romcollection/roms/' in api_path:
            return apiqueries.qry_get_roms(id)
        if 'romcollection/' in api_path:
            return apiqueries.qry_get_rom_collection(id)
        
        return None
            
    def handle_posts(self, api_path) -> bool:
        params = self.get_params()
        
        data_string = self.rfile.read(int(self.headers['Content-Length']))
        data = json.loads(data_string)
        
        if 'store/launcher/' in api_path:
            return api_commands.cmd_set_launcher_args(data)
        if 'store/scanner/' in api_path:
            return api_commands.cmd_set_scanner_settings(data)
        if 'store/roms/' in api_path:
            return api_commands.cmd_store_scanned_roms(data)
        
        return False