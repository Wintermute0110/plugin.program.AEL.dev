
# --- Modules/packages in this plugin ---
from constants import *
from romsets import *
from disk_IO import *
from utils import *
from utils_kodi import *

class RomStatisticsStrategy():

    def __init__(self, romsetFactory, launchers):
        
        self.MAX_RECENT_PLAYED_ROMS = 100

        self.romsetFactory = romsetFactory
        self.launchers = launchers

    def updateRecentlyPlayedRom(self, recent_rom):

        ## --- Compute ROM recently played list ---
        recentlyPlayedRomSet = self.romsetFactory.create(VCATEGORY_RECENT_ID, VLAUNCHER_RECENT_ID, self.launchers)

        recent_roms_list = recentlyPlayedRomSet.loadRomsAsList()
        recent_roms_list = [rom for rom in recent_roms_list if rom['id'] != recent_rom['id']]
        recent_roms_list.insert(0, recent_rom)

        if len(recent_roms_list) > self.MAX_RECENT_PLAYED_ROMS:
            log_debug('RomStatisticsStrategy() len(recent_roms_list) = {0}'.format(len(recent_roms_list)))
            log_debug('RomStatisticsStrategy() Trimming list to {0} ROMs'.format(self.MAX_RECENT_PLAYED_ROMS))
            temp_list        = recent_roms_list[:self.MAX_RECENT_PLAYED_ROMS]
            recent_roms_list = temp_list

        recentlyPlayedRomSet.saveRoms(recent_roms_list)
        
        # --- Compute most played ROM statistics ---
        mostPlayedRomSet = self.romsetFactory.create(VCATEGORY_MOST_PLAYED_ID, VLAUNCHER_MOST_PLAYED_ID, self.launchers)
        
        most_played_roms = mostPlayedRomSet.loadRoms()
        if recent_rom['id'] in most_played_roms:
            rom_id = recent_rom['id']
            most_played_roms[rom_id]['launch_count'] += 1
        else:
            # >> Add field launch_count to recent_rom to count how many times have been launched.
            recent_rom['launch_count'] = 1
            most_played_roms[recent_rom['id']] = recent_rom

        mostPlayedRomSet.saveRoms(most_played_roms)

    