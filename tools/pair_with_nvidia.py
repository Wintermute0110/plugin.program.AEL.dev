#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Pairing with Nvidia Gamestream Server
# OpenSSL needed
#

import os

from resources.gamestream import *
from resources.utils import *

test_dir = os.path.dirname(os.path.abspath(__file__))
addon_dir = FileName(test_dir)

host = "mediaserver"

print "Going to connect with '{}'".format(host)

server = GameStreamServer(host, addon_dir)
succeeded = server.connect()

if not succeeded:
    print 'Connection to {} failed'.format(host)
    exit

print 'Connection to {} succeeded'.format(host)

pincode = server.generatePincode()

print 'Start pairing process'
print 'Open up the Gamestream server and when asked insert the following PIN code: {}'.format(pincode)
paired = server.pairServer(pincode)

if not paired:
    print 'Pairing with {} failed'.format(host)
else:
    print 'Pairing with {} succeeded'.format(host)