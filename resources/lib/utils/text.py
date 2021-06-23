# -*- coding: utf-8 -*-
#

import traceback
import string
import logging
import time
import random
import hashlib
import re

logger = logging.getLogger(__name__)

def createError(ex: Exception):
    template = (
        "EXCEPTION Thrown (PythonToCppException) : -->Python callback/script returned the following error<--\n"
        " - NOTE: IGNORING THIS CAN LEAD TO MEMORY LEAKS!\n"
        "Error Type: <type '{0}'>\n"
        "Error Contents: {1!r}\n"
        "{2}"
        "-->End of Python script error report<--"
    )
    return template.format(type(ex).__name__, ex.args, traceback.format_exc())

# -------------------------------------------------------------------------------------------------
# Strings and text
# -------------------------------------------------------------------------------------------------
# Limits the length of a string for printing. If max_length == -1 do nothing (string has no
# length limit). The string is trimmed by cutting it and adding three dots ... at the end.
# Including these three dots the length of the returned string is max_length or less.
# Example: 'asdfasdfdasf' -> 'asdfsda...'
#
# @param string: [str] String to be trimmed.
# @param max_length: [int] Integer maximum length of the string.
# @return [str] Trimmed string.
def limit_string(string, max_length):
    if max_length > 5 and len(string) > max_length:
        string = string[0:max_length-3] + '...'
    return string

# Some XML encoding of special characters:
#   {'\n': '&#10;', '\r': '&#13;', '\t':'&#9;'}
#
# See http://stackoverflow.com/questions/1091945/what-characters-do-i-need-to-escape-in-xml-documents
# See https://wiki.python.org/moin/EscapingXml
# See https://github.com/python/cpython/blob/master/Lib/xml/sax/saxutils.py
# See http://stackoverflow.com/questions/2265966/xml-carriage-return-encoding
#
def escape_XML(data_str):

    if not isinstance(data_str, str):
        data_str = str(data_str)

    # Ampersand MUST BE replaced FIRST
    data_str = data_str.replace('&', '&amp;')
    data_str = data_str.replace('>', '&gt;')
    data_str = data_str.replace('<', '&lt;')

    data_str = data_str.replace("'", '&apos;')
    data_str = data_str.replace('"', '&quot;')
    
    # --- Unprintable characters ---
    data_str = data_str.replace('\n', '&#10;')
    data_str = data_str.replace('\r', '&#13;')
    data_str = data_str.replace('\t', '&#9;')

    return data_str

def unescape_XML(data_str):
    data_str = data_str.replace('&quot;', '"')
    data_str = data_str.replace('&apos;', "'")

    data_str = data_str.replace('&lt;', '<')
    data_str = data_str.replace('&gt;', '>')
    # Ampersand MUST BE replaced LAST
    data_str = data_str.replace('&amp;', '&')
    
    # --- Unprintable characters ---
    data_str = data_str.replace('&#10;', '\n')
    data_str = data_str.replace('&#13;', '\r')
    data_str = data_str.replace('&#9;', '\t')
    
    return data_str

# See https://www.freeformatter.com/json-escape.html
# The following characters are reserved in JSON and must be properly escaped to be used in strings:
#   Backspace is replaced with \b
#   Form feed is replaced with \f
#   Newline is replaced with \n
#   Carriage return is replaced with \r
#   Tab is replaced with \t
#   Double quote is replaced with \"
#   Backslash is replaced with \\
#
def escape_JSON(s):
    s = s.replace('\\', '\\\\') # >> Must be done first
    #s = s.replace('"', '\\"')

    return s

# Given a text clean it so the cleaned string can be used as a filename.
# 1) Convert any non-printable character into '_'
# 2) Remove special chars
# 3) (DISABLED) Convert spaces ' ' into '_'
def str_to_filename_str(title_str):
    not_valid_chars = '"*/:<>?\\|'
    cleaned_str_1 = ''.join([i if i in string.printable else '_' for i in title_str])
    cleaned_str_2 = ''.join([i if i not in not_valid_chars else '' for i in cleaned_str_1])
    #cleaned_str_3 = cleaned_str_2.replace(' ', '_')
    return cleaned_str_2

#
# Writes a XML text tag line, indented 2 spaces by default.
# Both tag_name and tag_text must be Unicode strings.
# Returns an Unicode string.
#
def XML_line(tag_name, tag_text, num_spaces = 2):
    if tag_text:
        tag_text = escape_XML(tag_text)
        line = '{0}<{1}>{2}</{3}>\n'.format(' ' * num_spaces, tag_name, tag_text, tag_name)
    else:
        # >> Empty tag
        line = '{0}<{1} />\n'.format(' ' * num_spaces, tag_name)

    return line

def str_2_Uni(string):
    # print(type(string))
    if type(string).__name__ == 'unicode':
        unicode_str = string
    elif type(string).__name__ == 'str':
        unicode_str = string.decode('utf-8', errors = 'replace')
    else:
        print('TypeError: ' + type(string).__name__)
        raise TypeError
    # print(type(unicode_str))

    return unicode_str

def remove_Kodi_color_tags(s):
    s = re.sub('\[COLOR \S+?\]', '', s)
    s = re.sub('\[color \S+?\]', '', s)
    s = s.replace('[/color]', '')
    s = s.replace('[/COLOR]', '')

    return s

#
# Generates a random an unique MD5 hash and returns a string with the hash
#
def misc_generate_random_SID() -> str:
    t1 = time.time()
    t2 = t1 + random.getrandbits(32)
    base = hashlib.md5(str(t1 + t2).encode('utf-8'))
    sid = base.hexdigest()

    return sid

# -------------------------------------------------------------------------------------------------
# Multidisc ROM support
# -------------------------------------------------------------------------------------------------
def get_ROM_basename_tokens(basename_str):
    DEBUG_TOKEN_PARSER = False

    # --- Parse ROM base_noext/basename_str into tokens ---
    reg_exp = '\[.+?\]|\(.+?\)|\{.+?\}|[^\[\(\{]+'
    tokens_raw = re.findall(reg_exp, basename_str)
    if DEBUG_TOKEN_PARSER:
        logger.debug('text_get_ROM_basename_tokens() tokens_raw   {0}'.format(tokens_raw))

    # >> Strip tokens
    tokens_strip = list()
    for token in tokens_raw: tokens_strip.append(token.strip())
    if DEBUG_TOKEN_PARSER:
        logger.debug('text_get_ROM_basename_tokens() tokens_strip {0}'.format(tokens_strip))

    # >> Remove empty tokens ''
    tokens_clean = list()
    for token in tokens_strip: 
        if token: tokens_clean.append(token)
    if DEBUG_TOKEN_PARSER:        
        logger.debug('text_get_ROM_basename_tokens() tokens_clean {0}'.format(tokens_clean))

    # >> Remove '-' tokens from Trurip multidisc names
    tokens = list()
    for token in tokens_clean:
        if token == '-': continue
        tokens.append(token)
    if DEBUG_TOKEN_PARSER:
        logger.debug('text_get_ROM_basename_tokens() tokens       {0}'.format(tokens))

    return tokens
