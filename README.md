# Shteff - a Discord Music Bot

Shteff is a Discord bot that allows users to play music in a voice channel and manage playlist straight from Discord using various commands. The bot use the Discord.py library to interact with the Discord API, the yt-dlp library to stream audio from YouTube and the lyricsgenius library to get the lyrics of songs. The database is handled by MySQL.

## Getting Started

Invite Shteff using [this link](https://discord.com/api/oauth2/authorize?client_id=1074271481674080296&permissions=8&scope=bot), select a server and approve all permissions. Enjoy!

## Self Hosting

### Installing requirements

To use this bot, you'll need to install all of the requirements from requirements.txt. You can use `pip` to install requirements.

```
pip install library-name
```

You will also need ffmpeg. You can get ffmpeg [here](https://www.gyan.dev/ffmpeg/builds/).

### Creating a Discord bot client

### Setting up a Spotify app

A step by step guide is provided below, but you can always use the Spotify for Developers Web API [documentation](https://developer.spotify.com/documentation/web-api/tutorials/getting-started) for more information or clarification.

#### Step 1: Generate your Spotify `client_id` and `client_secret`

- Go to [Spotify developers dashboard](https://developer.spotify.com/dashboard).
- Then select or create your app.
- Note down your Client ID and Client Secret in a convenient lacation to use in the next steps.

#### Step 2: Add `Redirect URIs` to your Spotify app

- Open settings for your app.
- Add `https://example.com` as your `Redirect URIs`
- Click on save.

#### Step 3: Create URI for access code

- In the URL below, replace `$CLIENT_ID`, `$SCOPE` and `$REDIRECT_URI` with the information you noted in Step 1. Make sure the `$REDIRECT_URI` is [URL encoded](https://meyerweb.com/eric/tools/dencoder/).

```
https://accounts.spotify.com/authorize?response_type=code&client_id=$CLIENT_ID&scope=$SCOPE&redirect_uri=$REDIRECT_URI
```

#### Step 4: Get acces code from the redirect URI
- You will be redirected to your redirect URI.
- In the address bar you will find a huge URL string similar to the one below. In place of `$ACCESSCODE` there will be a long string of characters. Note down that string for the next step.

```
https://example.com/?code=$ACCESSCODE
```

#### Step 5: Get the refresh token

- Type the following CURL command in your terminal and replaces all the variables with the information you noted in Step 1 and Step 4: `$CILENT_ID`, `$CLIENT_SECRET`, `$CODE`, and `$REDIRECT_URI`.

```
curl -d client_id=$CLIENT_ID -d client_secret=$CLIENT_SECRET -d grant_type=authorization_code -d code=$CODE -d redirect_uri=$REDIRECT_URI https://accounts.spotify.com/api/token
```
- The resulting JSON string will look something like this. Note down the `refresh_token`. This token will last for a very long time and can be used to generate a fresh `access_token` whenever it is needed.

```
{
  "access_token": "ACCESS_TOKEN",
  "token_type": "Bearer",
  "expires_in": 3600,
  "refresh_token": "REFRESH_TOKEN",
  "scope": "playlist-modify-private"
}
```

#### Step 6:

- Go to the [Base64 Encoder](https://www.base64encode.org/) and set the Destination character set to `ISO-8859-1`.
- In the encode field enter your `$CLIENT_ID` and `$CLIENT_SECRET` and note down the result.

```
$CLIENT_ID:$CLIENT_SECRET
```
- Note down the Base64 encoded string as you will need it later.

### Setting up the Genius API

### Setting up the `.env` file

After all that, you will need to make a file from which Shteff can access your new accounts.

In the `src` directory create a `.env`  and fill out the the needed info:

```
DISCORD_TOKEN='your-bot-token-here'

HOST_NAME='host-name-of-your-database-here'
USER_NAME='database-username'
USER_PASSWORD='database-password'
DB_NAME='database-name'
PORT_NUMBER=database-port-number

REFRESH_TOKEN='your-spotify-refresh-token'
BASE_64='your-spotify-base64-string'

GENIUS_CLIENT_ACCESS_TOKEN='your-genius-api-token'
```

Finally, run the bot by running the `main.py` file.

The bot should now be online and ready to use!

# Usage

You can interact with Shteff in two ways:
- Slash commands
- Interactive buttons

## The Commands

Envoke a slash command by typing `/` into the Message field of any channel in your Discord server. You can use `Tab` to autocomplete the names of commands, playlists and saved songs. You will understand it the moment you see it.

Optional parameter are marked as `parameter_name`*.

Only server Administrators and users with a role named `dj` can execute commands marked with `command_name`**.

| Command | Description | Parameters | Parameter descriptions |
| --- | --- | --- | --- |
| `/help` | Shows you a help message similar to this table |||
| `/ping` | Pings Shteff and displays the latency. |||
| `/join` | Makes the bot join to your voice channel. |||
|`/play` | The command you will be using most often. Connects the bot to your voice channel and starts playing whatever you asked it to. Shteff currently supports directly searching for songs by name, any Spotify link, and youtube.com links. | `song`, `place`* | `song` is the search parameter by which Shteff will find the song(s) you are looking for. `place` will insert the song(s) at that place in the queue. You can see the queue in the command message located in the shteffs-disco text channel. `place` has to be in queue and grater than 0. |
| `/file-play` | You can add your own files to add to your queue. The supported file formats are: `mp4` , `mp3`, `flac`, `m4a`, `wav`, `wma`, `aac` | `file`, `place`* | Insert your file into the `file` parameter. `place` works the same as in `/play` |
| `/skip` | Skips the currently playing song. If a single song is looped, the next song is played and loop is set to loop the entire queue. |||
| `/loop` | Cycles the loop state in the following order: no looping, looping the entire queue, looping a single song. |||
| `/clear` | Empties the queue of songs. |||
| `/dc` | Disconnects the bot from your voice channels and resets all bot states. |||
| `/back` | Goes to the previous song. If a single song is looped, the next song is played and loop is set to loop the entire queue. |||
| `/lyrics` | Shows the lyrics of the currently playing song below the command message. |||
| `/shuffle` | Toggles the shuffling of the list. Songs skipped while shuffled will not appear in the queue after unshuffling. |||
| `/swap` | Swaps the songs with the specified places in the queue. | `first`, `second` | Places of the songs you want to swap places. `first` does not have to be less than `second`. Both parameters have to be grater than 0. |
| `/pause` | Toggles the pausing of the player. |||
| `/remove` | Removes the song in the specified place from the queue. | `place` | `place` is the place of the song you want removed from the queue. The parameter has to be grater than 0. |
| `/goto` | Moves the player to the specified place in the queue. All the skipped songs will still appear in the history. | `place` | `place` is the place of the song you want to go to. The parameter has to be grater than 0. |
| `/create` | Creates a new personal playlist which only you will be able to access. | `playlist` | The parameter describes the name of your new playlist. |
| `/server-create`** | Creates a new server playlist which everyone on the server will be able to access. | `playlist` | The parameter describes the name of your new playlist. |
| `/delete` | Deletes the playlist from your list of playlists. | `playlist` | The parameter describes the name of the playlist being deleted. |
| `/server-delete`** | Deletes the playlist from the server's list of playlists. | `playlist` | The parameter describes the name of the playlist being deleted. |
| `/add` | Adds a song to the specified playlist. | `playlist`, `song`* | The parameter describes the name of the playlist where the song(s) will be added to. If `song` is not given, the currently playling song is added to the playlist. `song` supports all formats as in the `/play` command. |
| `/server-add`** | Works the same as `/add` but for server playlists. | `playlist`, `song`* | The parameters work the same as in `/add`. |
| `/obliterate` | Removes the specified song from a personal playlist. | `playlist`, `song` | Names of the song and the playlist wanted. |
| `/server-obliterate`** | Removes the specified song from a server playlist. | `playlist`, `song` | Names of the song and the playlist wanted. |
| `/catalogue` | Lists out all your personal playlists. |||
| `/server-catalogue` | Lists out all playlists in a server. |||
| `/manifest` | Lists out all songs on a personal playlist. | `playlist` | The name of the playlist. |
| `/server-manifest` | Lists out all songs on a server playlist. | `playlist` | The name of the playlist. |
| `/playlist` | Adds your personal playlist to the queue. | `playlist`, `song`\*, `place`\* | `playlist` is the name of the playlist. If `song` is not given, the entire playlist will be added to the queue. If `song` is given, only the selected song will be added to the queue. `place` works the same as in `/play`. |
| `/server-playlist` | Works the same as `/playlist` but for server playlists. | `playlist`, `song`\*, `place`\* | The parameters work the same as in `/playlist`. |


