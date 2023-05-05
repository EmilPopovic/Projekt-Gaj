import os
from dotenv import load_dotenv

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
