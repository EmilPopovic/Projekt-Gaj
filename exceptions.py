from colors import *
# TODO: log file?


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


class SpotifyExtractError(Exception):
    def __init__(self, err=None):
        if err:
            code = err['error'] if 'error' in err.keys() else err['status']
            print(f'{c_time()} {c_err()} Spotify API error code {code}')