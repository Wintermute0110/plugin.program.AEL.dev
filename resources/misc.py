# -*- coding: utf-8 -*-

# Copyright (c) 2016-2020 Wintermute0110 <wintermute0110@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.

# Advanced Emulator/MAME Launcher miscellaneous functions.
#
# The idea if this module is to share it between AEL and AML.
# Functions in this module only depend on the Python standard library.
# This module can be loaded anywhere without creating circular dependencies.
# Optionally this module can include utils.py to use the log_*() functions but better avoid it.

# --- Be prepared for the future ---
from __future__ import unicode_literals
from __future__ import division

# --- Addon modules ---
from .constants import *

# --- Python standard library ---
import re
import time

# -------------------------------------------------------------------------------------------------
# Strings and text functions.
# -------------------------------------------------------------------------------------------------
# Limits the length of a string for printing. If max_length == -1 do nothing (string has no
# length limit). The string is trimmed by cutting it and adding three dots ... at the end.
# Including these three dots the length of the returned string is max_length or less.
# Example: 'asdfasdfdasf' -> 'asdfsda...'
def text_limit_string(string, max_length):
    if max_length > 5 and len(string) > max_length:
        string = string[0:max_length-3] + '...'
    return string

# Given a Category/Launcher name clean it so the cleaned srt can be used as a filename.
#  1) Convert any non-printable character into '_'
#  2) Convert spaces ' ' into '_'
def text_title_to_filename_str(title_str):
    cleaned_str_1 = ''.join([i if i in string.printable else '_' for i in title_str])
    cleaned_str_2 = cleaned_str_1.replace(' ', '_')
    return cleaned_str_2

# Writes a XML text tag line, indented 2 spaces by default.
# Both tag_name and tag_text must be Unicode strings.
# Returns an Unicode string.
def text_XML(tag_name, tag_text, num_spaces = 2):
    if tag_text:
        tag_text = text_escape_XML(tag_text)
        line = '{}<{}>{}</{}>\n'.format(' ' * num_spaces, tag_name, tag_text, tag_name)
    else:
        # Empty tag.
        line = '{}<{} />\n'.format(' ' * num_spaces, tag_name)

    return line

# This function is Python 2. Should I remove it?
def text_str_2_Uni(mystring):
    # print(type(mystring))
    if type(mystring).__name__ == 'unicode':
        unicode_str = mystring
    elif type(mystring).__name__ == 'str':
        unicode_str = mystring.decode('utf-8', errors = 'replace')
    else:
        print('TypeError: ' + type(mystring).__name__)
        raise TypeError
    # print(type(unicode_str))

    return unicode_str

def text_remove_Kodi_color_tags(s):
    s = re.sub('\[COLOR \S+?\]', '', s)
    s = re.sub('\[color \S+?\]', '', s)
    s = s.replace('[/color]', '')
    s = s.replace('[/COLOR]', '')

    return s

# Renders a list of list of strings table into a CSV list of strings.
# The list of strings must be joined with '\n'.join()
def text_render_table_CSV(table_str):
    rows = len(table_str)
    cols = len(table_str[0])
    table_str_list = []
    for i in range(1, rows):
        row_str = ''
        for j in range(cols):
            if j < cols - 1:
                row_str += '{},'.format(table_str[i][j])
            else:
                row_str += '{}'.format(table_str[i][j])
        table_str_list.append(row_str)

    return table_str_list

# Returns a list of strings that must be joined with '\n'.join()
#
# First row            column aligment 'right' or 'left'
# Second row           column titles
# Third and next rows  table data
#
# Input:
# table_str = [
#     ['left', 'left', 'left'],
#     ['Platform', 'Parents', 'Clones'],
#     ['a', 'b', 'c'],
# ]
#
# Output:
#
def text_render_table(table_str, trim_Kodi_colours = False):
    rows = len(table_str)
    cols = len(table_str[0])

    # Remove Kodi tags [COLOR string] and [/COLOR]
    if trim_Kodi_colours:
        new_table_str = []
        for i in range(rows):
            new_table_str.append([])
            for j in range(cols):
                s = text_remove_Kodi_color_tags(table_str[i][j])
                new_table_str[i].append(s)
        table_str = new_table_str

    # Determine sizes and padding.
    # Ignore row 0 when computing sizes.
    table_str_list = []
    col_sizes = text_get_table_str_col_sizes(table_str, rows, cols)
    col_padding = table_str[0]

    # --- Table header ---
    row_str = ''
    for j in range(cols):
        if j < cols - 1:
            row_str += text_print_padded_left(table_str[1][j], col_sizes[j]) + '  '
        else:
            row_str += text_print_padded_left(table_str[1][j], col_sizes[j])
    table_str_list.append(row_str)
    # Table line -----
    total_size = sum(col_sizes) + 2*(cols-1)
    table_str_list.append('{}'.format('-' * total_size))

    # --- Data rows ---
    for i in range(2, rows):
        row_str = ''
        for j in range(cols):
            if j < cols - 1:
                if col_padding[j] == 'right':
                    row_str += text_print_padded_right(table_str[i][j], col_sizes[j]) + '  '
                else:
                    row_str += text_print_padded_left(table_str[i][j], col_sizes[j]) + '  '
            else:
                if col_padding[j] == 'right':
                    row_str += text_print_padded_right(table_str[i][j], col_sizes[j])
                else:
                    row_str += text_print_padded_left(table_str[i][j], col_sizes[j])
        table_str_list.append(row_str)

    return table_str_list

# First row             column aligment 'right' or 'left'
# Second and next rows  table data
# Input:
# table_str = [
#     ['left', 'left', 'left'],
#     ['Platform', 'Parents', 'Clones'],
#     ['', '', ''],
# ]
#
# Output:
#
def text_render_table_NO_HEADER(table_str, trim_Kodi_colours = False):
    rows = len(table_str)
    cols = len(table_str[0])

    # Remove Kodi tags [COLOR string] and [/COLOR]
    # BUG Currently this code removes all the colour tags so the table is rendered
    #     with no colours.
    # NOTE To render tables with colours is more difficult than this...
    #      All the paddings changed. I will left this for the future.
    if trim_Kodi_colours:
        new_table_str = []
        for i in range(rows):
            new_table_str.append([])
            for j in range(cols):
                s = text_remove_Kodi_color_tags(table_str[i][j])
                new_table_str[i].append(s)
        table_str = new_table_str

    # Ignore row 0 when computing sizes.
    table_str_list = []
    col_sizes = text_get_table_str_col_sizes(table_str, rows, cols)
    col_padding = table_str[0]

    # --- Data rows ---
    for i in range(1, rows):
        row_str = ''
        for j in range(cols):
            if j < cols - 1:
                if col_padding[j] == 'right':
                    row_str += text_print_padded_right(table_str[i][j], col_sizes[j]) + '  '
                else:
                    row_str += text_print_padded_left(table_str[i][j], col_sizes[j]) + '  '
            else:
                if col_padding[j] == 'right':
                    row_str += text_print_padded_right(table_str[i][j], col_sizes[j])
                else:
                    row_str += text_print_padded_left(table_str[i][j], col_sizes[j])
        table_str_list.append(row_str)

    return table_str_list

# Removed Kodi colour tags before computing size (substitute by ''):
#   A) [COLOR skyblue]
#   B) [/COLOR]
def text_get_table_str_col_sizes(table_str, rows, cols):
    col_sizes = [0] * cols
    for j in range(cols):
        col_max_size = 0
        for i in range(1, rows):
            cell_str = re.sub(r'\[COLOR \w+?\]', '', table_str[i][j])
            cell_str = re.sub(r'\[/COLOR\]', '', cell_str)
            str_size = len('{}'.format(cell_str))
            if str_size > col_max_size: col_max_size = str_size
        col_sizes[j] = col_max_size

    return col_sizes

def text_str_list_size(str_list):
    max_str_size = 0
    for str_item in str_list:
        str_size = len('{}'.format(str_item))
        if str_size > max_str_size: max_str_size = str_size

    return max_str_size

def text_str_dic_max_size(dictionary_list, dic_key, title_str = ''):
    max_str_size = 0
    for item in dictionary_list:
        str_size = len('{}'.format(item[dic_key]))
        if str_size > max_str_size: max_str_size = str_size
    if title_str:
        str_size = len(title_str)
        if str_size > max_str_size: max_str_size = str_size

    return max_str_size

def text_print_padded_left(text_line, text_max_size):
    formatted_str = '{}'.format(text_line)
    padded_str =  formatted_str + ' ' * (text_max_size - len(formatted_str))

    return padded_str

def text_print_padded_right(text_line, text_max_size):
    formatted_str = '{}'.format(text_line)
    padded_str = ' ' * (text_max_size - len(formatted_str)) + formatted_str

    return padded_str

# --- BEGIN code in dev-misc/test_color_tag_remove.py ---------------------------------------------
def text_remove_color_tags_slist(slist):
    # Iterate list of strings and remove the following tags
    # 1) [COLOR colorname]
    # 2) [/COLOR]
    #
    # Modifying a list is OK when iterating the list. However, do not change the size of the
    # list when iterating.
    for i, s in enumerate(slist):
        s_temp, modified = s, False

        # Remove all [COLOR colorname] tags.
        fa_list = re.findall('(\[COLOR \w+?\])', s_temp)
        fa_set = set(fa_list)
        if len(fa_set) > 0:
            modified = True
            for m in fa_set:
                s_temp = s_temp.replace(m, '')

        # Remove all [/COLOR]
        if s_temp.find('[/COLOR]') >= 0:
            s_temp = s_temp.replace('[/COLOR]', '')
            modified = True

        # Update list
        if modified:
            slist[i] = s_temp
# --- END code in dev-misc/test_color_tag_remove.py -----------------------------------------------

# Some XML encoding of special characters:
#   {'\n': '&#10;', '\r': '&#13;', '\t':'&#9;'}
#
# See http://stackoverflow.com/questions/1091945/what-characters-do-i-need-to-escape-in-xml-documents
# See https://wiki.python.org/moin/EscapingXml
# See https://github.com/python/cpython/blob/master/Lib/xml/sax/saxutils.py
# See http://stackoverflow.com/questions/2265966/xml-carriage-return-encoding
def text_escape_XML(data_str):
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

def text_unescape_XML(data_str):
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

# Unquote an HTML string. Replaces %xx with Unicode characters.
# http://www.w3schools.com/tags/ref_urlencode.asp
def text_decode_HTML(s):
    s = s.replace('%25', '%') # Must be done first
    s = s.replace('%20', ' ')
    s = s.replace('%23', '#')
    s = s.replace('%26', '&')
    s = s.replace('%28', '(')
    s = s.replace('%29', ')')
    s = s.replace('%2C', ',')
    s = s.replace('%2F', '/')
    s = s.replace('%3B', ';')
    s = s.replace('%3A', ':')
    s = s.replace('%3D', '=')
    s = s.replace('%3F', '?')

    return s

# Decodes HTML <br> tags and HTML entities (&xxx;) into Unicode characters.
# See https://stackoverflow.com/questions/2087370/decode-html-entities-in-python-string
def text_unescape_HTML(s):
    __debug_text_unescape_HTML = False
    if __debug_text_unescape_HTML:
        log_debug('text_unescape_HTML() input  "{}"'.format(s))

    # --- Replace HTML tag characters by their Unicode equivalent ---
    s = s.replace('<br>',   '\n')
    s = s.replace('<br/>',  '\n')
    s = s.replace('<br />', '\n')

    # --- HTML entities ---
    # s = s.replace('&lt;',   '<')
    # s = s.replace('&gt;',   '>')
    # s = s.replace('&quot;', '"')
    # s = s.replace('&nbsp;', ' ')
    # s = s.replace('&copy;', '©')
    # s = s.replace('&amp;',  '&') # >> Must be done last

    # --- HTML Unicode entities ---
    # s = s.replace('&#039;', "'")
    # s = s.replace('&#149;', "•")
    # s = s.replace('&#x22;', '"')
    # s = s.replace('&#x26;', '&')
    # s = s.replace('&#x27;', "'")

    # s = s.replace('&#x101;', "ā")
    # s = s.replace('&#x113;', "ē")
    # s = s.replace('&#x12b;', "ī")
    # s = s.replace('&#x12B;', "ī")
    # s = s.replace('&#x14d;', "ō")
    # s = s.replace('&#x14D;', "ō")
    # s = s.replace('&#x16b;', "ū")
    # s = s.replace('&#x16B;', "ū")

    # Use HTMLParser module to decode HTML entities.
    s = HTMLParser.HTMLParser().unescape(s)

    if __debug_text_unescape_HTML:
        log_debug('text_unescape_HTML() output "{}"'.format(s))

    return s

# Remove HTML tags from string.
def text_remove_HTML_tags(s):
    p = re.compile('<.*?>')
    s = p.sub('', s)

    return s

def text_unescape_and_untag_HTML(s):
    s = text_unescape_HTML(s)
    s = text_remove_HTML_tags(s)

    return s

def text_dump_str_to_file(filename, full_string):
    log_debug('Dumping file "{}"'.format(filename))
    file_obj = open(filename, 'w')
    file_obj.write(full_string.encode('utf-8'))
    file_obj.close()

# -------------------------------------------------------------------------------------------------
# ROM name cleaning and formatting
# -------------------------------------------------------------------------------------------------
# This function is used to clean the ROM name to be used as search string for the scraper.
#
# 1) Cleans ROM tags: [BIOS], (Europe), (Rev A), ...
# 2) Substitutes some characters by spaces
def text_format_ROM_name_for_scraping(title):
    title = re.sub('\[.*?\]', '', title)
    title = re.sub('\(.*?\)', '', title)
    title = re.sub('\{.*?\}', '', title)
    
    title = title.replace('_', '')
    title = title.replace('-', '')
    title = title.replace(':', '')
    title = title.replace('.', '')
    title = title.strip()

    return title

# Format ROM file name when scraping is disabled.
# 1) Remove No-Intro/TOSEC tags (), [], {} at the end of the file
#
# title      -> Unicode string
# clean_tags -> bool
#
# Returns a Unicode string.
def text_format_ROM_title(title, clean_tags):
    #
    # Regexp to decompose a string in tokens
    #
    if clean_tags:
        reg_exp = '\[.+?\]\s?|\(.+?\)\s?|\{.+?\}|[^\[\(\{]+'
        tokens = re.findall(reg_exp, title)
        str_list = []
        for token in tokens:
            stripped_token = token.strip()
            if (stripped_token[0] == '[' or stripped_token[0] == '(' or stripped_token[0] == '{') and \
               stripped_token != '[BIOS]':
                continue
            str_list.append(stripped_token)
        cleaned_title = ' '.join(str_list)
    else:
        cleaned_title = title

    # if format_title:
    #     if (title.startswith("The ")): new_title = title.replace("The ","", 1)+", The"
    #     if (title.startswith("A ")): new_title = title.replace("A ","", 1)+", A"
    #     if (title.startswith("An ")): new_title = title.replace("An ","", 1)+", An"
    # else:
    #     if (title.endswith(", The")): new_title = "The "+"".join(title.rsplit(", The", 1))
    #     if (title.endswith(", A")): new_title = "A "+"".join(title.rsplit(", A", 1))
    #     if (title.endswith(", An")): new_title = "An "+"".join(title.rsplit(", An", 1))

    return cleaned_title

# -------------------------------------------------------------------------------------------------
# URLs
# -------------------------------------------------------------------------------------------------
# Get extension of URL. Returns '' if not found. Examples: 'png', 'jpg', 'gif'.
def text_get_URL_extension(url):
    path = urlparse.urlparse(url).path
    ext = os.path.splitext(path)[1]
    if ext[0] == '.': ext = ext[1:] # Remove initial dot

    return ext

# Defaults to 'jpg' if URL extension cannot be determined
def text_get_image_URL_extension(url):
    path = urlparse.urlparse(url).path
    ext = os.path.splitext(path)[1]
    if ext[0] == '.': ext = ext[1:] # Remove initial dot
    ret = 'jpg' if ext == '' else ext

    return ret

# -------------------------------------------------------------------------------------------------
# Misc stuff
# -------------------------------------------------------------------------------------------------
# Given the image path, image filename with no extension and a list of file extensions search for
# a file.
#
# rootPath       -> FileName object
# filename_noext -> Unicode string
# file_exts      -> list of extenstions with no dot [ 'zip', 'rar' ]
#
# Returns a FileName object if a valid filename is found.
# Returns None if no file was found.
def misc_look_for_file(rootPath, filename_noext, file_exts):
    for ext in file_exts:
        file_path = rootPath.pjoin(filename_noext + '.' + ext)
        if file_path.exists():
            return file_path

    return None

# Generates a random an unique MD5 hash and returns a string with the hash
def misc_generate_random_SID():
    t1 = time.time()
    t2 = t1 + random.getrandbits(32)
    base = hashlib.md5(text_type(t1 + t2))
    sid = base.hexdigest()

    return sid

# See https://docs.python.org/3.8/library/time.html#time.gmtime
def misc_time_to_str(secs):
    return time.strftime('%a %d %b %Y %H:%M:%S', time.localtime(secs))

def misc_escape_regex_special_chars(s):
    s = s.replace('(', '\(')
    s = s.replace(')', '\)')
    s = s.replace('+', '\+')

    return s

# Search for a No-Intro DAT filename.
def misc_look_for_NoIntro_DAT(platform, DAT_list):
    # log_debug('Testing No-Intro platform "{}"'.format(platform.long_name))
    if not platform.DAT_prefix:
        # log_debug('Empty DAT_prefix. Return empty string.')
        return ''
    # Traverse all files and make a list of DAT matches.
    DAT_str = misc_escape_regex_special_chars(platform.DAT_prefix)
    patt = '.*' + DAT_str + ' \(Parent-Clone\) \((\d\d\d\d\d\d\d\d)-(\d\d\d\d\d\d)\)\.dat'
    # log_variable('patt', patt)
    fname_list = []
    for fname in DAT_list:
        m = re.match(patt, fname)
        if m: fname_list.append(fname)
    # log_variable('fname_list', fname_list)
    if fname_list:
        # If more than one DAT found sort alphabetically and pick the first.
        # Because the fname include the date the most recent must be first.
        return sorted(fname_list, reverse = True)[0]
    else:
        return ''

# Atari - Jaguar CD Interactive Multimedia System - Datfile (10) (2019-08-27 00-06-32)
# Commodore - Amiga CD - Datfile (350) (2019-06-28 13-05-34)
# Commodore - Amiga CD32 - Datfile (157) (2019-09-24 21-03-02)
def misc_look_for_Redump_DAT(platform, DAT_list):
    # log_debug('Testing Redump platform "{}"'.format(platform.long_name))
    if not platform.DAT_prefix:
        # log_debug('Empty DAT_prefix. Return empty string.')
        return ''
    DAT_str = misc_escape_regex_special_chars(platform.DAT_prefix)
    patt = '.*' + DAT_str + ' \(\d+\) \((\d\d\d\d-\d\d-\d\d) (\d\d-\d\d-\d\d)\)\.dat'
    # log_variable('patt', patt)
    fname_list = []
    for fname in DAT_list:
        m = re.match(patt, fname)
        if m: fname_list.append(fname)
    # log_variable('fname_list', fname_list)
    if fname_list:
        return sorted(fname_list, reverse = True)[0]
    else:
        return ''

# Lazy function (generator) to read a file piece by piece. Default chunk size: 8k.
# Usage example:
#  f = open()
#  for chunk in misc_read_file_in_chunks(f):
#     do_something()
def misc_read_file_in_chunks(file_object, chunk_size = 8192):
    while True:
        data = file_object.read(chunk_size)
        if not data: break
        yield data

# Calculates CRC, MD5 and SHA1 of a file in an efficient way.
# Returns a dictionary with the checksums or None in case of error.
#
# https://stackoverflow.com/questions/519633/lazy-method-for-reading-big-file-in-python
# https://stackoverflow.com/questions/1742866/compute-crc-of-file-in-python
def misc_calculate_file_checksums(full_file_path):
    log_debug('Computing checksums "{}"'.format(full_file_path))
    try:
        f = open(full_file_path, 'rb')
        crc_prev = 0
        md5 = hashlib.md5()
        sha1 = hashlib.sha1()
        for piece in misc_read_file_in_chunks(f):
            crc_prev = zlib.crc32(piece, crc_prev)
            md5.update(piece)
            sha1.update(piece)
        crc_digest = '{:08X}'.format(crc_prev & 0xFFFFFFFF)
        md5_digest = md5.hexdigest()
        sha1_digest = sha1.hexdigest()
        size = os.path.getsize(full_file_path)
    except:
        log_debug('(Exception) In misc_calculate_file_checksums()')
        log_debug('Returning None')
        return None
    checksums = {
        'crc'  : crc_digest.upper(),
        'md5'  : md5_digest.upper(),
        'sha1' : sha1_digest.upper(),
        'size' : size,
    }

    return checksums

# This function not finished yet.
def misc_read_bytes_in_chunks(file_bytes, chunk_size = 8192):
    file_length = len(file_bytes)
    block_number = 0
    while True:
        start_index = None
        end_index = None
        data = file_bytes[start_index:end_index]
        yield data

def misc_calculate_stream_checksums(file_bytes):
    log_debug('Computing checksums of bytes stream...'.format(len(file_bytes)))
    crc_prev = 0
    md5 = hashlib.md5()
    sha1 = hashlib.sha1()
    # Process bytes stream block by block
    # for piece in misc_read_bytes_in_chunks(file_bytes):
    #     crc_prev = zlib.crc32(piece, crc_prev)
    #     md5.update(piece)
    #     sha1.update(piece)
    # Process bytes in one go
    crc_prev = zlib.crc32(file_bytes, crc_prev)
    md5.update(file_bytes)
    sha1.update(file_bytes)
    crc_digest = '{:08X}'.format(crc_prev & 0xFFFFFFFF)
    md5_digest = md5.hexdigest()
    sha1_digest = sha1.hexdigest()
    size = len(file_bytes)

    checksums = {
        'crc'  : crc_digest.upper(),
        'md5'  : md5_digest.upper(),
        'sha1' : sha1_digest.upper(),
        'size' : size,
    }

    return checksums

# Replace an item in dictionary. If dict_in is an OrderedDict then keep original order.
# Returns a dict or OrderedDict
def misc_replace_fav(dict_in, old_item_key, new_item_key, new_value):
    if type(dict_in) is dict:
        dict_in.pop(old_item_key)
        dict_in[new_item_key] = new_value
        return dict_in
    elif type(dict_in) is collections.OrderedDict:
        # In this case create a new OrderedDict to respect original order.
        # This implementation is slow and naive but I don't care, OrderedDict are only use
        # when editing ROM Collections.
        dict_out = collections.OrderedDict()
        for key in dict_in:
            if key == old_item_key:
                dict_out[new_item_key] = new_value
            else:
                dict_out[key] = dict_in[key]
        return dict_out
    else:
        raise TypeError

# Image file magic numbers. All at file offset 0.
# See https://en.wikipedia.org/wiki/List_of_file_signatures
IMAGE_MAGIC_DIC = {
    IMAGE_PNG_ID  : [ b'\x89\x50\x4E\x47\x0D\x0A\x1A\x0A' ],
    IMAGE_JPEG_ID : [
        b'\xFF\xD8\xFF\xDB',
        b'\xFF\xD8\xFF\xE0\x00\x10\x4A\x46\x49\x46\x00\x01',
        b'\xFF\xD8\xFF\xEE',
        b'\xFF\xD8\xFF\xE1',
    ],
    IMAGE_GIF_ID  : [
        b'\x47\x49\x46\x38\x37\x61',
        b'\x47\x49\x46\x38\x39\x61',
    ],
    IMAGE_BMP_ID  : [ b'\x42\x4D' ],
    IMAGE_TIFF_ID : [
        b'\x49\x49\x2A\x00',
        b'\x4D\x4D\x00\x2A',
    ]
}

# Inspects an image file and determine its type by using the magic numbers,
# Returns an image id defined in list IMAGE_IDS or IMAGE_UKNOWN_ID.
def misc_identify_image_id_by_contents(asset_fname):
    # If file size is 0 or less than 64 bytes it is corrupt.
    statinfo = os.stat(asset_fname)
    if statinfo.st_size < 64: return IMAGE_CORRUPT_ID

    # Read first 64 bytes of file.
    # Search for the magic number of the beginning of the file.
    with open(asset_fname, "rb") as f:
        file_bytes = f.read(64)
    for img_id in IMAGE_MAGIC_DIC:
        for magic_bytes in IMAGE_MAGIC_DIC[img_id]:
            magic_bytes_len = len(magic_bytes)
            file_chunk = file_bytes[0:magic_bytes_len]
            if len(file_chunk) != magic_bytes_len: raise TypeError
            if file_chunk == magic_bytes: return img_id

    return IMAGE_UKNOWN_ID

# Returns an image id defined in list IMAGE_IDS or IMAGE_UKNOWN_ID.
def misc_identify_image_id_by_ext(asset_fname):
    asset_root, asset_ext = os.path.splitext(asset_fname)
    # log_debug('asset_ext {}'.format(asset_ext))
    if not asset_ext: return IMAGE_UKNOWN_ID
    asset_ext = asset_ext[1:] # Remove leading dot '.png' -> 'png'
    for img_id in IMAGE_EXTENSIONS:
        for img_ext in IMAGE_EXTENSIONS[img_id]:
            if asset_ext.lower() == img_ext: return img_id

    return IMAGE_UKNOWN_ID

# All version numbers must be less than 100, except the major version.
# AML version is like this: aa.bb.cc[-|~][alpha[dd]|beta[dd]]
# It gets converted to: aa.bb.cc Rdd -> int aab,bcc,Rdd
# The number 2,147,483,647 is the maximum positive value for a 32-bit signed binary integer.
#
# aa.bb.cc.Xdd    formatted aab,bcc,Xdd
#  |  |  | | |--> Beta/Alpha flag 0, 1, ..., 99
#  |  |  | |----> Release kind flag 
#  |  |  |        5 for non-beta, non-alpha, non RC versions.
#  |  |  |        2 for RC versions
#  |  |  |        1 for beta versions
#  |  |  |        0 for alpha versions
#  |  |  |------> Build version 0, 1, ..., 99
#  |  |---------> Minor version 0, 1, ..., 99
#  |------------> Major version 0, ..., infinity
def misc_addon_version_str_to_int(AML_version_str):
    # log_debug('misc_addon_version_str_to_int() AML_version_str = "{}"'.format(AML_version_str))
    version_int = 0
    # Parse versions like "0.9.8[-|~]alpha[jj]"
    m_obj_alpha_n = re.search('^(\d+?)\.(\d+?)\.(\d+?)[\-\~](alpha|beta)(\d+?)$', AML_version_str)
    # Parse versions like "0.9.8[-|~]alpha"
    m_obj_alpha = re.search('^(\d+?)\.(\d+?)\.(\d+?)[\-\~](alpha|beta)$', AML_version_str)
    # Parse versions like "0.9.8"
    m_obj_standard = re.search('^(\d+?)\.(\d+?)\.(\d+?)$', AML_version_str)

    if m_obj_alpha_n:
        major    = int(m_obj_alpha_n.group(1))
        minor    = int(m_obj_alpha_n.group(2))
        build    = int(m_obj_alpha_n.group(3))
        kind_str = m_obj_alpha_n.group(4)
        beta     = int(m_obj_alpha_n.group(5))
        if kind_str == 'alpha':
            release_flag = 0
        elif kind_str == 'beta':
            release_flag = 1
        # log_debug('misc_addon_version_str_to_int() major        {}'.format(major))
        # log_debug('misc_addon_version_str_to_int() minor        {}'.format(minor))
        # log_debug('misc_addon_version_str_to_int() build        {}'.format(build))
        # log_debug('misc_addon_version_str_to_int() kind_str     {}'.format(kind_str))
        # log_debug('misc_addon_version_str_to_int() release_flag {}'.format(release_flag))
        # log_debug('misc_addon_version_str_to_int() beta         {}'.format(beta))
        version_int = major * 10000000 + minor * 100000 + build * 1000 + release_flag * 100 + beta
    elif m_obj_alpha:
        major    = int(m_obj_alpha.group(1))
        minor    = int(m_obj_alpha.group(2))
        build    = int(m_obj_alpha.group(3))
        kind_str = m_obj_alpha.group(4)
        if kind_str == 'alpha':
            release_flag = 0
        elif kind_str == 'beta':
            release_flag = 1
        # log_debug('misc_addon_version_str_to_int() major        {}'.format(major))
        # log_debug('misc_addon_version_str_to_int() minor        {}'.format(minor))
        # log_debug('misc_addon_version_str_to_int() build        {}'.format(build))
        # log_debug('misc_addon_version_str_to_int() kind_str     {}'.format(kind_str))
        # log_debug('misc_addon_version_str_to_int() release_flag {}'.format(release_flag))
        version_int = major * 10000000 + minor * 100000 + build * 1000 + release_flag * 100
    elif m_obj_standard:
        major = int(m_obj_standard.group(1))
        minor = int(m_obj_standard.group(2))
        build = int(m_obj_standard.group(3))
        release_flag = 5
        # log_debug('misc_addon_version_str_to_int() major {}'.format(major))
        # log_debug('misc_addon_version_str_to_int() minor {}'.format(minor))
        # log_debug('misc_addon_version_str_to_int() build {}'.format(build))
        version_int = major * 10000000 + minor * 100000 + build * 1000 + release_flag * 100
    else:
        # log_debug('AML addon version "{}" cannot be parsed.'.format(AML_version_str))
        raise TypeError('misc_addon_version_str_to_int() failure')
    # log_debug('misc_addon_version_str_to_int() version_int = {}'.format(version_int))

    return version_int

# -------------------------------------------------------------------------------------------------
# Utilities to test scrapers
# -------------------------------------------------------------------------------------------------
# These must be replaced with the table-making functions.

# Candidates
NAME_L      = 65
SCORE_L     = 5
ID_L        = 55
PLATFORM_L  = 20
SPLATFORM_L = 20
URL_L       = 70

# Metadata
TITLE_L     = 50
YEAR_L      = 4
GENRE_L     = 20
DEVELOPER_L = 10
NPLAYERS_L  = 10
ESRB_L      = 20
PLOT_L      = 70

# Assets
ASSET_ID_L        = 10
ASSET_NAME_L      = 60
ASSET_URL_THUMB_L = 100

# PUT functions to print things returned by Scraper object (which are common to all scrapers)
# into util.py, to be resused by all scraper tests.
def print_candidate_list(results):
    p_str = "{0} {1} {2} {3} {4}"
    print('Found {} candidate/s'.format(len(results)))
    print(p_str.format(
        'Display name'.ljust(NAME_L), 'Score'.ljust(SCORE_L),
        'Id'.ljust(ID_L), 'Platform'.ljust(PLATFORM_L), 'SPlatform'.ljust(SPLATFORM_L)))
    print(p_str.format(
        '-'*NAME_L, '-'*SCORE_L, '-'*ID_L, '-'*PLATFORM_L, '-'*SPLATFORM_L))
    for game in results:
        display_name = text_limit_string(game['display_name'], NAME_L)
        score = text_limit_string(str(game['order']), SCORE_L)
        id = text_limit_string(str(game['id']), ID_L)
        platform = text_limit_string(str(game['platform']), PLATFORM_L)
        splatform = text_limit_string(str(game['scraper_platform']), SPLATFORM_L)
        print(p_str.format(
            display_name.ljust(NAME_L), score.ljust(SCORE_L), id.ljust(ID_L),
            platform.ljust(PLATFORM_L), splatform.ljust(SPLATFORM_L)))
    print('')

def print_game_metadata(metadata):
    title     = text_limit_string(metadata['title'], TITLE_L)
    year      = metadata['year']
    genre     = text_limit_string(metadata['genre'], GENRE_L)
    developer = text_limit_string(metadata['developer'], DEVELOPER_L)
    nplayers  = text_limit_string(metadata['nplayers'], NPLAYERS_L)
    esrb      = text_limit_string(metadata['esrb'], ESRB_L)
    plot      = text_limit_string(metadata['plot'], PLOT_L)

    p_str = "{0} {1} {2} {3} {4} {5} {6}"
    print('Displaying metadata for title "{}"'.format(title))
    print(p_str.format(
        'Title'.ljust(TITLE_L), 'Year'.ljust(YEAR_L), 'Genre'.ljust(GENRE_L),
        'Developer'.ljust(DEVELOPER_L), 'NPlayers'.ljust(NPLAYERS_L), 'ESRB'.ljust(ESRB_L),
        'Plot'.ljust(PLOT_L)))
    print(p_str.format(
        '-'*TITLE_L, '-'*YEAR_L, '-'*GENRE_L, '-'*DEVELOPER_L, '-'*NPLAYERS_L, '-'*ESRB_L, '-'*PLOT_L))
    print(p_str.format(
        title.ljust(TITLE_L), year.ljust(YEAR_L), genre.ljust(GENRE_L), developer.ljust(DEVELOPER_L),
        nplayers.ljust(NPLAYERS_L), esrb.ljust(ESRB_L), plot.ljust(PLOT_L) ))
    print('')

def print_game_assets(image_list):
    # print('Found {} image/s'.format(len(image_list)))
    p_str = "{0} {1} {2}"
    print(p_str.format(
        'Asset ID'.ljust(ASSET_ID_L), 'Name'.ljust(ASSET_NAME_L),
        'URL thumb'.ljust(ASSET_URL_THUMB_L)))
    print(p_str.format('-'*ASSET_ID_L, '-'*ASSET_NAME_L, '-'*ASSET_URL_THUMB_L))
    for image in image_list:
        id           = text_limit_string(str(image['asset_ID']), ASSET_ID_L)
        display_name = text_limit_string(image['display_name'], ASSET_NAME_L)
        url_thumb    = text_limit_string(image['url_thumb'], ASSET_URL_THUMB_L)
        print(p_str.format(
            id.ljust(ASSET_ID_L), display_name.ljust(ASSET_NAME_L),
            url_thumb.ljust(ASSET_URL_THUMB_L)))
    print('')
