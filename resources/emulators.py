# -*- coding: UTF-8 -*-

def emudata_get_program_arguments( app ):
    # Based on the app. name, retrieve the default arguments for the app.
    app = app.lower()
    applications = {
        'bsnes': '"%rom%"',
        'chromium': '-kiosk "%rom%"',
        'dosbox': '"%rom%" -fullscreen',
        'epsxe': '-nogui -loadiso "%rom%"',
        'fbas': '-g %romname%',
        'fceux': '"%rom%"',
        'fusion': '"%rom%"',
        'gens': '--fs --quickexit "%rom%"',
        'lxdream': '-f "%rom%"',
        'mame': '"%rom%"',
        'mednafen': '-fs 1 "%rom%"',
        'mess': '-cart "%rom%" -skip_gameinfo -nowindow -nonewui',
        'mupen64plus': '--nogui --noask --noosd --fullscreen "%rom%"',
        'nestopia': '"%rom%"',
        'nullDC': '-config ImageReader:defaultImage="%rom%"',
        'osmose': '-fs "%rom%"',
        'project64': '%rom%',
        'vbam': '--opengl=MODE --fullscreen -f 15 --no-show-speed "%rom%"',
        'visualboyadvance': '"%rom%"',
        'x64': '-fullscreen -autostart "%rom%"',
        'xbmc': 'PlayMedia(%rom%)',
        'yabause': '-a -f -i "%rom%"',
        'zsnes': '-m -s -v 22 "%rom%"',
        'zsnesw': '-m -s -v 41 "%rom%"',
        'explorer.exe': '%rom%',
    }
    for application, arguments in applications.iteritems():
        if (app.find(application) >= 0):
            return arguments

    return '"%rom%"'


def emudata_get_program_extensions( app ):
    # Based on the app. name, retrieve the recognized extension of the app.
    app = app.lower()
    applications = {
        'bsnes': 'zip|smc|sfc',
        'chromium': 'swf',
        'dosbox': 'bat',
        'epsxe': 'iso|bin|cue',
        'fbas': 'zip',
        'fceux': 'nes|zip',
        'fusion': 'zip|bin|sms|gg',
        'gens': 'zip|bin',
        'lxdream': 'cdi|iso|bin',
        'mame': 'zip',
        'mednafen': 'zip|pce|gba|gb|gbc|lnx|ngc|ngp|wsc|ws',
        'mess': 'zip|nes|sms|gg|rom|a78|a52|a26|gb|gbc|gba|int|bin|sg|pce|smc',
        'mupen64plus': 'z64|zip|n64',
        'nestopia': 'nes|zip',
        'nullDC': 'gdi|cdi',
        'osmose': 'zip|sms|gg',
        'project64': 'z64|zip|n64',
        'vbam': 'gba|gb|gbc|zip',
        'visualboyadvance': 'gba|gb|gbc|zip',
        'x64': 'zip|d64|c64',
        'yabause': 'cue',
        'zsnes': 'zip|smc|sfc',
        'explorer.exe': 'lnk',
    }
    for application, extensions in applications.iteritems():
        if (app.find(application) >= 0):
            return extensions

    return ""

def emudata_game_system_list():
    game_list = [
        "MAME", 
        "DOS",
        "Game Boy",
        "Game Boy Advance",
        "Game Boy Color",
        "Nintendo 64",
        "Nintendo DS",
        "Sega CD",
        "Sega Game Gear",
        "Sega Genesis",
        "Sega 32X",
    ]

    return game_list
