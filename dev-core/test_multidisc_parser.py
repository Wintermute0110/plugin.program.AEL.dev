#!/usr/bin/python3 -B
# -*- coding: utf-8 -*-

# Copyright (c) 2017-2021 Wintermute0110 <wintermute0110@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# Test the parser for multidisc support.


# --- Import AEL modules ---
import os, sys
if __name__ == "__main__" and __package__ is None:
    path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    print('Adding to sys.path {0}'.format(path))
    sys.path.append(path)
from resources.constants import *
from resources.utils import *

# --- Python standard library ---
import pprint
import re

# --- BEGIN code in dev-core/test_multidisc_parser.py --------------------------------------------
def get_ROM_basename_tokens(basename_str):
    DEBUG_TOKEN_PARSER = False

    # --- Parse ROM base_noext/basename_str into tokens ---
    reg_exp = '\[.+?\]|\(.+?\)|\{.+?\}|[^\[\(\{]+'
    tokens_raw = re.findall(reg_exp, basename_str)
    if DEBUG_TOKEN_PARSER:
        log_debug('get_ROM_basename_tokens() tokens_raw   {}'.format(tokens_raw))

    # Strip tokens
    tokens_strip = list()
    for token in tokens_raw: tokens_strip.append(token.strip())
    if DEBUG_TOKEN_PARSER:
        log_debug('get_ROM_basename_tokens() tokens_strip {}'.format(tokens_strip))

    # Remove empty tokens ''
    tokens_clean = list()
    for token in tokens_strip:
        if token: tokens_clean.append(token)
    if DEBUG_TOKEN_PARSER:
        log_debug('get_ROM_basename_tokens() tokens_clean {}'.format(tokens_clean))

    # Remove '-' tokens from Trurip multidisc names
    tokens = list()
    for token in tokens_clean:
        if token == '-': continue
        tokens.append(token)
    if DEBUG_TOKEN_PARSER:
        log_debug('get_ROM_basename_tokens() tokens       {}'.format(tokens))

    return tokens

class MultiDiscInfo:
    def __init__(self, ROM_FN):
        self.ROM_FN      = ROM_FN
        self.isMultiDisc = False
        self.setName     = ''
        self.discName    = ROM_FN.getBase()
        self.extension   = ROM_FN.getExt()
        self.order       = 0

def get_multidisc_info(ROM_FN):
    DEBUG_FUNCTION = False
    MDSet = MultiDiscInfo(ROM_FN)

    # --- Parse ROM basenoext into tokens ---
    tokens = get_ROM_basename_tokens(ROM_FN.getBaseNoExt())
    if DEBUG_FUNCTION: log_debug('tokens: {}'.format(text_type(tokens)))

    # --- Check if ROM belongs to a multidisc set and get set name and order ---
    # Algortihm:
    # 1) Iterate list of tokens
    # 2) If a token marks a multidisk ROM extract set order
    # 3) Define the set basename by removing the multidisk token
    MultDiscFound = False
    for index, token in enumerate(tokens):
        # --- Redump ---
        matchObj = re.match(r'\(Dis[ck] ([0-9]+)\)', token)
        if matchObj:
            log_debug('get_multidisc_info() ### Matched Redump multidisc ROM ###')
            tokens_nodisc_idx = list(range(0, len(tokens)))
            tokens_nodisc_idx.remove(index)
            tokens_mdisc = [tokens[x] for x in tokens_nodisc_idx]
            MultDiscFound = True
            break

        # --- TOSEC/Trurip ---
        matchObj = re.match(r'\(Dis[ck] ([0-9]+) of ([0-9]+)\)', token)
        if matchObj:
            log_debug('get_multidisc_info() ### Matched TOSEC/Trurip multidisc ROM ###')
            tokens_nodisc_idx = list(range(0, len(tokens)))
            tokens_nodisc_idx.remove(index)
            if DEBUG_FUNCTION:
                log_debug('get_multidisc_info() index              = {}'.format(index))
                log_debug('get_multidisc_info() tokens_nodisc_idx  = {}'.format(tokens_nodisc_idx))
            tokens_mdisc = [tokens[x] for x in tokens_nodisc_idx]
            MultDiscFound = True
            break

    if MultDiscFound:
        MDSet.isMultiDisc = True
        MDSet.setName = ' '.join(tokens_mdisc) + MDSet.extension
        MDSet.order = int(matchObj.group(1))
        log_debug('get_multidisc_info() base_noext   "{}"'.format(ROM_FN.getBaseNoExt()))
        log_debug('get_multidisc_info() tokens       "{}"'.format(tokens))
        log_debug('get_multidisc_info() tokens_mdisc "{}"'.format(tokens_mdisc))
        log_debug('get_multidisc_info() setName      "{}"'.format(MDSet.setName))
        log_debug('get_multidisc_info() discName     "{}"'.format(MDSet.discName))
        log_debug('get_multidisc_info() extension    "{}"'.format(MDSet.extension))
        log_debug('get_multidisc_info() order        "{}"'.format(MDSet.order))

    return MDSet
# --- END code in dev-core/test_multidisc_parser.py ----------------------------------------------

# --- Main ---------------------------------------------------------------------------------------
ROM_title_list = [
    # TOSEC
    'Final Fantasy I (USA) (Disc 1 of 2).iso',
    'Final Fantasy I (USA) (Disc 2 of 2).iso',
    # Trurip
    'Final Fantasy II (USA) - (Disc 1 of 2).iso',
    'Final Fantasy II (USA) - (Disc 2 of 2).iso',
    # Redump
    'Final Fantasy VII (USA) (Disc 1).iso',
    'Final Fantasy VII (USA) (Disc 2).iso',
    # No tags
    'Tomb Raider (EU).iso',
    '[BIOS] PSX bios (EU).iso',
    # Cornestone cases
    'Final Fantasy I    (Disc 1 of 2)    (USA).iso',
    'Final Fantasy I    (Disc 2 of 2)    (USA).iso',
]
set_log_level(LOG_DEBUG)
for ROM_filename in ROM_title_list:
    print('--> Processing "{}"'.format(ROM_filename))
    MDSet = get_multidisc_info(FileName(ROM_filename))
    print('')
