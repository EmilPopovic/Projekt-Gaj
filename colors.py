from datetime import datetime

class Colors:
    """ ANSI color codes """
    BLACK = "\033[0;30m"
    RED = "\033[0;31m"
    GREEN = "\033[0;32m" # on login
    BROWN = "\033[0;33m"
    BLUE = "\033[0;34m"
    PURPLE = "\033[0;35m" # channel id
    CYAN = "\033[0;36m" # user id
    LIGHT_GRAY = "\033[0;37m"
    DARK_GRAY = "\033[1;30m" # timestamps
    LIGHT_RED = "\033[1;31m"
    LIGHT_GREEN = "\033[1;32m"
    YELLOW = "\033[1;33m"
    LIGHT_BLUE = "\033[1;34m"
    LIGHT_PURPLE = "\033[1;35m" # guild id
    LIGHT_CYAN = "\033[1;36m" # event
    LIGHT_WHITE = "\033[1;37m"
    BOLD = "\033[1m"
    FAINT = "\033[2m"
    ITALIC = "\033[3m"
    UNDERLINE = "\033[4m"
    BLINK = "\033[5m"
    NEGATIVE = "\033[7m"
    CROSSED = "\033[9m"
    END = "\033[0m"

def c_login():
    return f'{Colors.GREEN}LOGGED IN{Colors.END}'

def c_guild(guild: int):
    return f'{Colors.LIGHT_PURPLE}{guild}{Colors.END}'

def c_channel(channel: int):
    return f'{Colors.PURPLE}{channel}{Colors.END}'

def c_time():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f'{Colors.DARK_GRAY}{now}{Colors.END}'

def c_event(event: str):
    return f'{Colors.LIGHT_CYAN}{event}{Colors.END}'

def c_user(user: int):
    return f'{Colors.CYAN}{user}{Colors.END}'

def c_err():
    return f'{Colors.RED}{"ERROR"}{Colors.END}'