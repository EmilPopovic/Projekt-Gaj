# last changed 12/12/22
# moved timestamp print to colors.py

from colors import *
# todo: log file?


class FailedToConnectError(Exception):
    def __init__(self):
        print(f'{c_time()} {c_err()} Failed to connect to voice channel.')


class DifferentChannelsError(Exception):
    pass


class UserNotInVCError(Exception):
    pass


class BotNotInVCError(Exception):
    pass


class InteractionFailedError(Exception):
    pass


class YTDLError(Exception):
    def __init__(self, query):
        print(f'{c_err()} failed to extract info for: {query}')


class SpotifyExtractError(Exception):
    def __init__(self, err=None):
        if err:
            # todo: prints error wrong
            code = err['error'] if 'error' in err.keys() else err['status']
            print(f'{c_err()} Spotify API error code {code}')
