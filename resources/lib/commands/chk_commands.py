# -*- coding: utf-8 -*-
#
# Advanced Emulator Launcher: Commands (check data)
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
import typing

from ael.utils import kodi, io
from ael import constants

from resources.lib.commands.mediator import AppMediator

from resources.lib.repositories import ROMsRepository, UnitOfWork, AelAddonRepository, CategoryRepository, ROMCollectionRepository, XmlConfigurationRepository
from resources.lib.domain import Category, ROMCollection, AelAddon

logger = logging.getLogger(__name__)

@AppMediator.register('CHECK_ROM_ARTWORK_INTEGRITY')
def cmd_check_ROM_artwork_integrity(args):
    logger.debug('cmd_check_ROM_artwork_integrity() Beginning...')
    
    uow = UnitOfWork(globals.g_PATHS.DATABASE_FILE_PATH)
    with uow:
        romcollections_repository = ROMCollectionRepository(uow)
        rom_repository            = ROMsRepository(uow)
        
        
        romcollections              = [*romcollections_repository.find_all_romcollections()]

        main_slist = []
        detailed_slist = []
        sum_table_slist = [
            ['left', 'right', 'right', 'right', 'right'],
            ['Launcher', 'ROMs', 'Images', 'Missing', 'Problematic'],
        ]
        pdialog = kodi.ProgressDialog()
        d_msg = 'Checking ROM artwork integrity...'
        pdialog.startProgress(d_msg, len(romcollections))
        total_images = 0
        missing_images = 0
        processed_images = 0
        problematic_images = 0
        for collection in romcollections:
            pdialog.incrementStep(d_msg)

            # Skip non-ROM launcher.
            if not launcher['rompath']: continue
            logger.debug(f'Checking ROM Launcher "{collection.get_name()}"...')
            detailed_slist.append(KC_ORANGE + 'Launcher "{}"'.format(launcher['m_name']) + KC_END)
            # Load ROMs.
            pdialog.updateMessage('{}\n{}'.format(d_msg, 'Loading ROMs'))
            roms = fs_load_ROMs_JSON(g_PATHS.ROMS_DIR, launcher)
            num_roms = len(roms)
            R_str = 'ROM' if num_roms == 1 else 'ROMs'
            logger.debug('Launcher has {} DB {}'.format(num_roms, R_str))
            detailed_slist.append('Launcher has {} DB {}'.format(num_roms, R_str))
            # If Launcher is empty there is nothing to do.
            if num_roms < 1:
                logger.debug('Launcher is empty')
                detailed_slist.append('Launcher is empty')
                detailed_slist.append(KC_YELLOW + 'Skipping launcher' + KC_END)
                continue

        # Traverse all ROMs in Launcher.
        # For every asset check the artwork file.
        # First check if the image has the correct extension.
        problems_detected = False
        launcher_images = 0
        launcher_missing_images = 0
        launcher_problematic_images = 0
        pdialog.updateMessage('{}\n{}'.format(d_msg, 'Checking image files'))
        for rom_id in roms:
            rom = roms[rom_id]
            # detailed_slist.append('\nProcessing ROM {}'.format(rom['filename']))
            for asset_id in ROM_ASSET_ID_LIST:
                A = assets_get_info_scheme(asset_id)
                asset_fname = rom[A.key]
                # detailed_slist.append('\nProcessing asset {}'.format(A.name))
                # Skip empty assets
                if not asset_fname: continue
                # Skip manuals and trailers
                if asset_id == ASSET_MANUAL_ID: continue
                if asset_id == ASSET_TRAILER_ID: continue
                launcher_images += 1
                total_images += 1
                # If asset file does not exits that's an error.
                if not os.path.exists(asset_fname):
                    detailed_slist.append('Not found {}'.format(asset_fname))
                    launcher_missing_images += 1
                    missing_images += 1
                    problems_detected = True
                    continue
                # Process asset
                processed_images += 1
                asset_root, asset_ext = os.path.splitext(asset_fname)
                asset_ext = asset_ext[1:] # Remove leading dot '.png' -> 'png'
                img_id_ext = misc_identify_image_id_by_ext(asset_fname)
                img_id_real = misc_identify_image_id_by_contents(asset_fname)
                # detailed_slist.append('img_id_ext "{}" | img_id_real "{}"'.format(img_id_ext, img_id_real))
                # Unrecognised or corrupted image.
                if img_id_ext == IMAGE_UKNOWN_ID:
                    detailed_slist.append('Unrecognised extension {}'.format(asset_fname))
                    problems_detected = True
                    problematic_images += 1
                    launcher_problematic_images += 1
                    continue
                # Corrupted image.
                if img_id_real == IMAGE_CORRUPT_ID:
                    detailed_slist.append('Corrupted {}'.format(asset_fname))
                    problems_detected = True
                    problematic_images += 1
                    launcher_problematic_images += 1
                    continue
                # Unrecognised or corrupted image.
                if img_id_real == IMAGE_UKNOWN_ID:
                    detailed_slist.append('Bin unrecog or corrupted {}'.format(asset_fname))
                    problems_detected = True
                    problematic_images += 1
                    launcher_problematic_images += 1
                    continue
                # At this point the image is recognised but has wrong extension
                if img_id_ext != img_id_real:
                    detailed_slist.append('Wrong extension ({}) {}'.format(
                        IMAGE_EXTENSIONS[img_id_real][0], asset_fname))
                    problems_detected = True
                    problematic_images += 1
                    launcher_problematic_images += 1
                    continue
            # On big setups this can take forever. Allow the user to cancel.
            if pdialog.isCanceled(): break
        else:
            # only executed if the inner loop did NOT break
            sum_table_slist.append([
                launcher['m_name'], '{:,d}'.format(num_roms), '{:,d}'.format(launcher_images),
                '{:,d}'.format(launcher_missing_images), '{:,d}'.format(launcher_problematic_images),
            ])
            detailed_slist.append('Number of images    {:6,d}'.format(launcher_images))
            detailed_slist.append('Missing images      {:6,d}'.format(launcher_missing_images))
            detailed_slist.append('Problematic images  {:6,d}'.format(launcher_problematic_images))
            if problems_detected:
                detailed_slist.append(KC_RED + 'Launcher should be updated' + KC_END)
            else:
                detailed_slist.append(KC_GREEN + 'Launcher OK' + KC_END)
            detailed_slist.append('')
            continue
        # only executed if the inner loop DID break
        detailed_slist.append('Interrupted by user (pDialog cancelled).')
        break
    pdialog.endProgress()

    # Generate, save and display report.
    logger.info('Writing report file "{}"'.format(g_PATHS.ROM_ART_INTEGRITY_REPORT_FILE_PATH.getPath()))
    pdialog.startProgress('Saving report')
    main_slist.append('*** Summary ***')
    main_slist.append('There are {:,} ROM launchers.'.format(len(self.launchers)))
    main_slist.append('Total images        {:7,d}'.format(total_images))
    main_slist.append('Missing images      {:7,d}'.format(missing_images))
    main_slist.append('Processed images    {:7,d}'.format(processed_images))
    main_slist.append('Problematic images  {:7,d}'.format(problematic_images))
    main_slist.append('')
    main_slist.extend(text_render_table(sum_table_slist))
    main_slist.append('')
    main_slist.append('*** Detailed report ***')
    main_slist.extend(detailed_slist)
    utils_write_slist_to_file(g_PATHS.ROM_ART_INTEGRITY_REPORT_FILE_PATH.getPath(), main_slist)
    pdialog.endProgress()
    full_string = '\n'.join(main_slist)
    kodi_display_text_window_mono('ROM artwork integrity report', full_string)

@AppMediator.register('DELETE_REDUNDANT_ROM_ARTWORK')
def cmd_delete_redundant_rom_artwork(args):
    kodi.dialog_OK('DELETE_REDUNDANT_ROM_ARTWORK not implemented yet.')
    return

    # logger.info('cmd_delete_redundant_rom_artwork() Beginning...')
    # main_slist = []
    # detailed_slist = []
    # pdialog = KodiProgressDialog()
    # pdialog.startProgress('Checking ROM sync status', len(self.launchers))
    # for launcher_id in sorted(self.launchers, key = lambda x : self.launchers[x]['m_name']):
    #     pdialog.updateProgressInc()
    #     launcher = self.launchers[launcher_id]
    #     # Skip non-ROM launcher.
    #     if not launcher['rompath']: continue
    #     logger.debug('Checking ROM Launcher "{}"'.format(launcher['m_name']))
    #     detailed_slist.append('[COLOR orange]Launcher "{}"[/COLOR]'.format(launcher['m_name']))
    #     # Load ROMs.
    #     roms = fs_load_ROMs_JSON(g_PATHS.ROMS_DIR, launcher)
    #     num_roms = len(roms)
    #     R_str = 'ROM' if num_roms == 1 else 'ROMs'
    #     logger.debug('Launcher has {} DB {}'.format(num_roms, R_str))
    #     detailed_slist.append('Launcher has {} DB {}'.format(num_roms, R_str))
    #     # For now skip multidisc ROMs until multidisc support is fixed. I think for
    #     # every ROM in the multidisc set there should be a normal ROM not displayed
    #     # in listings, and then the special multidisc ROM that points to the ROMs
    #     # in the set.
    #     has_multidisc_ROMs = False
    #     for rom_id in roms:
    #         if roms[rom_id]['disks']:
    #             has_multidisc_ROMs = True
    #             break
    #     if has_multidisc_ROMs:
    #         logger.debug('Launcher has multidisc ROMs. Skipping launcher')
    #         detailed_slist.append('Launcher has multidisc ROMs.')
    #         detailed_slist.append('[COLOR yellow]Skipping launcher[/COLOR]')
    #         continue
    #     # Get real ROMs (remove Missing, Multidisc, etc., ROMs).
    #     # Remove ROM Audit Missing ROMs (fake ROMs).
    #     real_roms = {}
    #     for rom_id in roms:
    #         if roms[rom_id]['nointro_status'] == AUDIT_STATUS_MISS: continue
    #         real_roms[rom_id] = roms[rom_id]
    #     num_real_roms = len(real_roms)
    #     R_str = 'ROM' if num_real_roms == 1 else 'ROMs'
    #     logger.debug('Launcher has {} real {}'.format(num_real_roms, R_str))
    #     detailed_slist.append('Launcher has {} real {}'.format(num_real_roms, R_str))
    #     # If Launcher is empty there is nothing to do.
    #     if num_real_roms < 1:
    #         logger.debug('Launcher is empty')
    #         detailed_slist.append('Launcher is empty')
    #         detailed_slist.append('[COLOR yellow]Skipping launcher[/COLOR]')
    #         continue
    #     # Make a dictionary for fast indexing.
    #     # romfiles_dic = {real_roms[rom_id]['filename'] : rom_id for rom_id in real_roms}

    #     # Process all asset directories one by one.


    #     # Complete detailed report.
    #     detailed_slist.append('')
    # pdialog.endProgress()

    # Generate, save and display report.
    logger.info('Writing report file "{}"'.format(g_PATHS.ROM_SYNC_REPORT_FILE_PATH.getPath()))
    pdialog.startProgress('Saving report')
    main_slist.append('*** Summary ***')
    main_slist.append('There are {} ROM launchers.'.format(len(self.launchers)))
    main_slist.append('')
    # main_slist.extend(text_render_table_NO_HEADER(short_slist, trim_Kodi_colours = True))
    # main_slist.append('')
    main_slist.append('*** Detailed report ***')
    main_slist.extend(detailed_slist)
    utils_write_str_to_file(g_PATHS.ROM_SYNC_REPORT_FILE_PATH.getPath(), main_slist)
    pdialog.endProgress()
    full_string = '\n'.join(main_slist)
    kodi_display_text_window_mono('ROM redundant artwork report', full_string)
