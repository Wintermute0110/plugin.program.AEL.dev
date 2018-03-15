#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Pairing with Nvidia Gamestream Server
# OpenSSL needed
#
# This tool must be called with two parameters, host and path where to store certificates.
# Example: >python pair_with_nvidia.py 192.168.1.99 c:\games\gamestream\
#
# When started this tool will show a unique pincode which you need to enter in a dialog
# on your computer which is running Nvidia Geforce Experience. When done correctly it will
# pair up with that computer and generate certificates needed to keep on communicating with
# the geforce experience computer. These certificates can be used in a Gamestream Launcher.
#
#from __future__ import unicode_literals
import sys, os

if __name__ == "__main__":
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    sys.path.append(os.path.join(root, 'resources'))

host = sys.argv[1]
path = sys.argv[2]
    
from gamestream import *
from utils import *
from utils_kodi import *

set_use_print(True)
set_log_level(LOG_INFO)

certs_path = StandardFileName(path)
print "Going to connect with '{}'".format(host)

server = GameStreamServer(host, certs_path)
succeeded = server.connect()

if not succeeded:
    print 'Connection to {} failed'.format(host)
    exit

print 'Connection to {} succeeded'.format(host)

if server.is_paired():
    print 'Already paired with host {}. Stopping pairing process'.format(host)
    exit

pincode = server.generatePincode()

print 'Start pairing process'
print 'Open up the Gamestream server and when asked insert the following PIN code: {}'.format(pincode)
paired = server.pairServer(pincode)

if not paired:
    print 'Pairing with {} failed'.format(host)
else:
    print 'Pairing with {} succeeded'.format(host)
