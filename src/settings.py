import os
from dotenv import load_dotenv


VERSION = 'v1.4.8.-beta'


# command types, commands and descriptions

COMMANDS = {
    'player': {
        'join': {
            'short_description': 'Conjures the bot in your auditory dimension.',
            'long_description': '',
        },
        'play': {
            'short_description': 'Adds a song/list to queue.',
            'long_description': '',
        },
        'file-play': {
            'short_description': 'Add a song from a file to queue.',
            'long_description': '',
        },
        'pause': {
            'short_description': 'Pauses or unpauses playing.',
            'long_description': '',
        },
        'skip': {
            'short_description': 'Skips to the next queued song.',
            'long_description': '',
        },
        'back': {
            'short_description': 'Skips current song and plays previous.',
            'long_description': '',
        },
        'loop': {
            'short_description': 'Loops queue or single song.',
            'long_description': '',
        },
        'clear': {
            'short_description': 'Clears queue and history, stops playing.',
            'long_description': '',
        },
        'dc': {
            'short_description': 'Disconnects bot from voice channel.',
            'long_description': '',
        },
        'lyrics': {
            'short_description': 'Toggles lyrics display (show/hide).',
            'long_description': '',
        },
        'shuffle': {
            'short_description': 'Toggles queue shuffle.',
            'long_description': '',
        },
        'swap': {
            'short_description': 'Swap places of queued songs.',
            'long_description': '',
        },
        'remove': {
            'short_description': 'Removes song with given index from the queue.',
            'long_description': '',
        },
        'goto': {
            'short_description': 'Jumps to the song with given index, removes skipped songs.',
            'long_description': '',
        },
    },

    'playlist': {
        'create': {
            'short_description': 'Create a personal playlist.',
            'long_description': '',
        },
        'server-create': {
            'short_description': 'Create a server playlist.',
            'long_description': '',
        },
        'delete': {
            'short_description': 'Deletes a personal playlist.',
            'long_description': '',
        },
        'server-delete': {
            'short_description': 'Deletes a server playlist.',
            'long_description': '',
        },
        'add': {
            'short_description': 'Add currently playing song to personal playlist.',
            'long_description': '',
        },
        'server-add': {
            'short_description': 'Add currently playing song to server playlist.',
            'long_description': '',
        },
        'obliterate': {
            'short_description': 'Obliterates a song, removing it completely from existence (or the playlist at least).',
            'long_description': '',
        },
        'server-obliterate': {
            'short_description': 'Obliterates a song, removing it completely from existence (or the playlist at least).',
            'long_description': '',
        },
        'catalogue': {
            'short_description': 'Lists out your vast catalogue of playlists.',
            'long_description': '',
        },
        'server-catalogue': {
            'short_description': 'Lists out your server\'s vast catalogue of playlists.',
            'long_description': '',
        },
        'manifest': {
            'short_description': 'Forces the songs from your list to take a corporeal form and appear before your eyes.',
            'long_description': '',
        },
        'server-manifest': {
            'short_description': 'Forces the songs from your server list to take a corporeal form and appear before your eyes.',
            'long_description': '',
        },
        'playlist': {
            'short_description': 'Adds songs from selected playlist to the queue.',
            'long_description': '',
        },
        'server-playlist': {
            'short_description': 'Adds songs from selected playlist to the queue.',
            'long_description': '',
        },
    },

    'debug': {
        'reset': {
            'short_description': 'This is a debug command, use it only if you broke something.',
            'long_description': '',
        },
        'refresh': {
            'short_description': 'This is a debug command that refreshes the command message.',
            'long_description': '',
        },
        'help': {
            'short_description': 'Get help using the bot.',
            'long_description': '',
        },
        'ping': {
            'short_description': 'Pings Shteff.',
            'long_description': '',
        },
    }
}

cmds1, cmds2, cmds3 = list(COMMANDS['player'].keys()), list(COMMANDS['playlist'].keys()), list(COMMANDS['debug'].keys())
COMMAND_NAMES: list[str] = cmds1 + cmds2 + cmds3


load_dotenv()

# discord
TOKEN = os.getenv('DISCORD_TOKEN')

# database
HOST_NAME = os.getenv('HOST_NAME')
USER_NAME = os.getenv('USER_NAME')
USER_PASSWORD = os.getenv('USER_PASSWORD')
DB_NAME = os.getenv('DB_NAME')
PORT_NUMBER = os.getenv('PORT_NUMBER')

# spotify
REFRESH_TOKEN = os.getenv('REFRESH_TOKEN')
BASE_64 = os.getenv('BASE_64')

# genius
GENIUS_API_KEY = os.getenv('GENIUS_CLIENT_ACCESS_TOKEN')
