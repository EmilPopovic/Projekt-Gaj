import json

with open('secrets.json', 'r') as f:
    data = json.load(f)

# discord
token = data['discord']['discord_token']

# database
host_name = data['database']['host_name']
user_name = data['database']['user_name']
user_password = data['database']['user_password']
db_name = data['database']['db_name']
port_number = data['database']['port_number']

# spotify
refresh_token = data['spotify']['refresh_token']
base_64 = data['spotify']['base_64']

# genius
api_key = data['genius']['genius_client_access_token']
