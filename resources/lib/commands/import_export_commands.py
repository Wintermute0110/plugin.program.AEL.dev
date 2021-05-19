# -*- coding: utf-8 -*-
#
# Advanced Emulator Launcher: Commands (import & export of configurations)
#
# Copyright (c) 2016-2018 Wintermute0110 <wintermute0110@gmail.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# --- Python standard library ---
from __future__ import unicode_literals
from __future__ import division

import logging

from resources.lib.repositories import *
from resources.lib.commands.mediator import AppMediator

from resources.lib.settings import *
from resources.lib import globals
from resources.lib.utils import kodi
from resources.lib.utils import io

logger = logging.getLogger(__name__)

@AppMediator.register('IMPORT_LAUNCHERS')
def cmd_execute_import_launchers(args):
    file_list = kodi.browse(1, 'Select XML category/launcher configuration file',
                                'files', '.xml', True)

    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        categories_repository = CategoryRepository(uow)
        existing_categories   = [*categories_repository.find_all_categories()]

        romsets_repository    = ROMSetRepository(uow)
        existing_romsets      = [*romsets_repository.find_all_romsets()]

        existing_category_ids = map(lambda c: c.get_id(), existing_categories)
        existing_romset_ids   = map(lambda r: r.get_id(), existing_romsets)

        categories_to_insert:typing.List[Category]  = []
        categories_to_update:typing.List[Category]  = []
        romsets_to_insert:typing.List[ROMSet]       = []
        romsets_to_update:typing.List[ROMSet]       = []

        # >> Process file by file
        for xml_file in file_list:
            logger.debug('cmd_execute_import_launchers() Importing "{0}"'.format(xml_file))
            import_FN = io.FileName(xml_file)
            if not import_FN.exists(): continue

            xml_file_repository  = XmlConfigurationRepository(import_FN)
            categories_to_import = xml_file_repository.get_categories()
            launchers_to_import  = xml_file_repository.get_launchers()

            for category_to_import in categories_to_import:
                if category_to_import.get_id() in existing_category_ids:
                     # >> Category exists (by name). Overwrite?
                    logger.debug('Category found. Edit existing category.')
                    if kodi.dialog_yesno('Category "{}" found in AEL database. Overwrite?'.format(category_to_import.get_name())):
                        categories_to_update.append(category_to_import)
                else:
                    categories_to_insert.append(category_to_import)

            for launcher_to_import in launchers_to_import:
                if launcher_to_import.get_id() in existing_romset_ids:
                     # >> Romset exists (by name). Overwrite?
                    logger.debug('ROMSet found. Edit existing ROMSet.')
                    if kodi.dialog_yesno('ROMSet "{}" found in AEL database. Overwrite?'.format(launcher_to_import.get_name())):
                        romsets_to_update.append(launcher_to_import)
                else:
                    romsets_to_insert.append(launcher_to_import)

        for category_to_insert in categories_to_insert:
            categories_repository.save_category(category_to_insert)
            existing_categories.append(category_to_insert)

        for category_to_update in categories_to_update:
            categories_repository.update_category(category_to_update)
            
        for romset_to_insert in romsets_to_insert:
            parent_id = romset_to_insert.get_custom_attribute('parent_id')
            parent_obj = next((c for c in existing_categories if c.get_id() == parent_id), None)
            romsets_repository.save_romset(romset_to_insert, parent_obj)
            existing_romsets.append(romset_to_insert)

        for romset_to_update in romsets_to_update:
            romsets_repository.update_romset(romset_to_update)

        uow.commit()

    kodi.event(method='RENDER_VIEWS')
    kodi.notify('Finished importing Categories/Launchers')
