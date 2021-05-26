# -*- coding: utf-8 -*-
#
# Advanced Emulator Launcher main script file.
#

# Copyright (c) 2016-2018 Wintermute0110 <wintermute0110@gmail.com>
# Portions (c) 2010-2015 Angelscry
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# Viewqueries.py contains all methods that collect items to be shown
# in the UI containers. It combines custom data from repositories
# with static/predefined data.
# All methods have the prefix 'qry_'.

# --- Python standard library ---
from __future__ import unicode_literals
from __future__ import division

import logging
from resources.lib.domain import MetaDataItemABC

from resources.lib.utils import kodi

logger = logging.getLogger(__name__)

# Edits an object field which is a Unicode string.
#
# Example call:
#   edit_field_by_str(collection, 'Title', collection.get_title, collection.set_title)
#
def edit_field_by_str(obj_instance: MetaDataItemABC, metadata_name, get_method, set_method) -> bool:
    object_name = obj_instance.get_object_name()
    old_value = get_method()
    s = 'Edit {0} "{1}" {2}'.format(object_name, old_value, metadata_name)
    new_value = kodi.dialog_keyboard(s, old_value)
    if new_value is None: return False

    if old_value == new_value:
        kodi.notify('{0} {1} not changed'.format(object_name, metadata_name))
        return False
    set_method(new_value)
    kodi.notify('{0} {1} is now {2}'.format(object_name, metadata_name, new_value))
    return True

#
# Rating 'Not set' is stored as an empty string.
# Rating from 0 to 10 is stored as a string, '0', '1', ..., '10'
# Returns True if the rating value was changed.
# Returns Flase if the rating value was NOT changed.
# Example call:
#   edit_rating('ROM Collection', collection.get_rating, collection.set_rating)
#
def edit_rating(obj_instance: MetaDataItemABC, get_method, set_method):
    options_list = [
        'Not set',
        'Rating 0', 'Rating 1', 'Rating 2', 'Rating 3', 'Rating 4', 'Rating 5',
        'Rating 6', 'Rating 7', 'Rating 8', 'Rating 9', 'Rating 10'
    ]
    object_name = obj_instance.get_object_name()
    current_rating_str = get_method()
    if not current_rating_str:
        preselected_value = 0
    else:
        preselected_value = int(current_rating_str) + 1
    sel_value = kodi.ListDialog().select('Select the {0} Rating'.format(object_name),
                                        options_list, preselect_idx = preselected_value)
    if sel_value is None: return
    if sel_value == preselected_value:
        kodi.notify('{0} Rating not changed'.format(object_name))
        return False

    if sel_value == 0:
        current_rating_str = ''
    elif sel_value >= 1 and sel_value <= 11:
        current_rating_str = '{0}'.format(sel_value - 1)
    elif sel_value < 0:
        kodi.notify('{0} Rating not changed'.format(object_name))
        return False

    set_method(current_rating_str)
    obj_instance.save_to_disk()
    kodi.notify('{0} rating is now {1}'.format(object_name, current_rating_str))
    return True

