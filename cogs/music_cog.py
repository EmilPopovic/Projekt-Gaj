from os import fdopen, remove
from shutil import move, copymode
from tempfile import mkstemp

import asyncio
import discord
import os
import random
from discord.ext import commands
from youtube_dl import YoutubeDL

from colors import *
from spotify import GetSpotifySongs

# a music cog (instance of MusicCog class) is created for every guild the bot is in
# the music cog executes slash commands defined in main.py
# MusicCog objects control their own Buttons and handle interactions from them
# MusicCog objects manipulate their configuration files
# > channel_ids.txt
#     > stores [guild_id, command_channel_id] pairs
#     > the command message is displayed in the command channel of every guild
#     > the MusicCog can recover a deleted command channel on bot start or guild reset
# > server_lists/{guild_id}.txt
#     > server_lists directory contains a file for every guild
#     > a guild can have a virtually unlimited number of lists associated with it
#     > start of a new list is defined with ">>>{list_name}<<<"
#     > every line under a specific list name is considered a song name on the list
#     > TODO: store links to songs instead of songs
#     > TODO: use sql database with [song_name, url] pair if url becomes unavailable


class MusicCog(commands.Cog):
    def __init__(self, bot, guild):
        self.bot = bot
        self.guild: discord.guild.Guild = guild

        # default bot states
        self.is_playing = False
        self.is_paused = False
        self.is_looped = False
        self.is_looped_single = False
        self.is_shuffled = False
        self.is_downloading = False
        self.short_queue = False
        self.show_history = True
        self.was_long_queue = False

        self.p_index = 0  # Index which operates all aspects of the music queue

        # song lists
        self.music_queue = []
        #self.music_queue_no_shuffle = []
        #self.music_history = []
        self.currently_playing = []

        # id of command message
        self.on_ready_message = None

        # YouTube download options
        self.YDL_OPTIONS = {
            'format': 'bestaudio',
            'audioquality': '9',
            'audioformat': 'mp3',
            'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
            'restrictfilenames': True,
            'noplaylist': True,
            'nocheckcertificate': True,
            'ignoreerrors': False,
            'logtostderr': False,
            'quiet': True,
            'no_warnings': True,
            'default_search': 'auto',
            'source_address': '0.0.0.0'
        }

        # encoder options
        self.FFMPEG_OPTIONS = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn'
        }

        # get from spotify if open.spotify.com url in /play command
        self.spotify_links = ['https://open.spotify.com/playlist/',
                              'https://open.spotify.com/album/',
                              'https://open.spotify.com/artist/']

        # TODO: remove limit and download songs dynamically, when needed
        self.add_limit = 30

        # initiate voice
        self.vc = None

        # create_server_playlist()

    # async part of __init__
    async def __init_async__(self):
        """
        Is part of __init__ function.
        Initiates command channel and command message.
        Clears existing command channel on bot start or cog reset.
        """
        self.bot_channel_id = await get_id(self.guild)

        # clear command channel on start
        await self.bot.get_channel(self.bot_channel_id).purge(limit = 1)

        # start and update new live message
        embed = discord.Embed(title = 'Welcome to Štef!',
                              description = 'Use !p to add more songs to queue.',
                              color = 0xf1c40f)

        self.on_ready_message = await self.bot.get_channel(self.bot_channel_id).send(embed = embed)

    async def update_msg(self):
        # TODO: finish docstring
        """
        Refreshes command message according to current bot states, lists and playing status.
        """
        edit_msg = self.on_ready_message

        # message content
        content = ''

        new_history = self.music_queue[:self.p_index]
        new_history.reverse()

        if self.show_history:
            content += '**History:**\n'

            for i in range(len(new_history)):
                content += f'{i + 1} {new_history[i][0]["title"]}\n'

            if self.music_queue[self.p_index + 1:]:
                content += '\n'

        if self.music_queue[self.p_index + 1:]:
            content += '**Queue:**\n'

            for i in range(len(self.music_queue[self.p_index + 1:]) - 1, -1, -1):
                if self.short_queue and i < 5 or not self.short_queue:
                    content += f'{i + 1} {self.music_queue[i][0]["title"]}\n'

        await edit_msg.edit(content = content, view = Buttons(cog = self))

    # async def update_msg(self):
    #    edit_msg = self.on_ready_message
    #    guild_id = edit_msg.guild.id
    #
    #    ########## BUTTONS ##########
    #
    #    if not self.is_downloading:
    #        previous_button = Button(label='⯬', custom_id=f'previous_{guild_id}')
    #        skip_button = Button(label='⯮', custom_id=f'skip_{guild_id}')
    #
    #        clear_button = Button(label='✖', custom_id=f'clear_{guild_id}', style=ButtonStyle.red)
    #        dc_button = Button(label='#', custom_id=f'dc_{guild_id}', style=ButtonStyle.red)
    #        list_button = Button(label='≡', custom_id=f'list_{guild_id}')
    #
    #        if not self.is_paused:
    #            pause_button = Button(label='▉', custom_id=f'pause_{guild_id}')
    #        else:
    #            pause_button = Button(label='▶', custom_id=f'pause_{guild_id}', style=ButtonStyle.green)
    #
    #        if not self.is_shuffled:
    #            shuffle_button = Button(label='⎇', custom_id=f'shuffle_{guild_id}')
    #        else:
    #            shuffle_button = Button(label='⎇', custom_id=f'shuffle_{guild_id}', style=ButtonStyle.green)
    #
    #        if self.is_looped:
    #            loop_button = Button(label='⭯', custom_id=f'loop_{guild_id}', style=ButtonStyle.green)
    #        elif self.is_looped_single:
    #            loop_button = Button(label='⭯', custom_id=f'loop_{guild_id}', style=ButtonStyle.blue)
    #        else:
    #            loop_button = Button(label='⭯', custom_id=f'loop_{guild_id}')
    #
    #        if not self.short_queue:
    #            queue_button = Button(label='⯆', custom_id=f'queue_{guild_id}')
    #        else:
    #            queue_button = Button(label='⯆', custom_id=f'queue_{guild_id}', style=ButtonStyle.green)
    #
    #        if self.show_history:
    #            history_button = Button(label='⯅', custom_id=f'history_{guild_id}', style=ButtonStyle.green)
    #            queue_button = Button(label='⯆', custom_id=f'queue_{guild_id}', style=ButtonStyle.green, disabled=True)
    #        else:
    #            history_button = Button(label='⯅', custom_id=f'history_{guild_id}')
    #
    #        
    #    else:
    #        shuffle_button = Button(label='⎇', custom_id=f'shuffle_{guild_id}', disabled=True)
    #        previous_button = Button(label='⯬', custom_id=f'previous_{guild_id}', disabled=True)
    #        pause_button = Button(label='▉', custom_id=f'pause_{guild_id}', disabled=True)
    #        skip_button = Button(label='⯮', custom_id=f'skip_{guild_id}', disabled=True)
    #        loop_button = Button(label='⭯', custom_id=f'loop_{guild_id}', disabled=True)
    #
    #        clear_button = Button(label='✖', custom_id=f'clear_{guild_id}', disabled=True)
    #        dc_button = Button(label='#', custom_id=f'dc_{guild_id}', disabled=True)
    #        list_button = Button(label='≡', custom_id=f'list_{guild_id}', disabled=True)
    #        queue_button = Button(label='⯆', custom_id=f'queue_{guild_id}', disabled=True)
    #        history_button = Button(label='⯅', custom_id=f'history_{guild_id}', disabled=True)
    #
    #
    #    buttons1 = [shuffle_button, previous_button, pause_button, skip_button, loop_button]
    #    buttons2 = [clear_button, dc_button, list_button, queue_button, history_button]
    #
    #    ########## MESSAGE CONTENT ##########
    #
    #    content = ''
    #
    #    new_history = self.music_history[:-1] if self.is_playing else self.music_history
    #
    #    if new_history and self.show_history:
    #        content += '**History:**\n'
    #
    #        for i in range(len(new_history)):
    #            content += f'{i+1} {new_history[i][0]["title"]}\n'
    #
    #        if self.music_queue:
    #            content += '\n'
    #
    #
    #    if self.music_queue:
    #        content += '**Queue:**\n'
    #
    #        for i in range(len(self.music_queue) - 1, -1, -1):
    #            if self.short_queue and i < 5 or not self.short_queue:
    #                content += f'{i+1} {self.music_queue[i][0]["title"]}\n'
    #
    #    ########## EMBED ##########
    #
    #    embed = discord.Embed(title='Welcome to Štef!', description='Use !p to add more songs to queue.', color=0xf1c40f)
    #
    #    if self.currently_playing:
    #        title = self.currently_playing[0]["title"]
    #        
    #        id = self.currently_playing[0]["id"]
    #        url = f'https://www.youtube.com/watch?v={id}'
    #
    #        thumbnail_source = f'https://img.youtube.com/vi/{id}/0.jpg'
    #        
    #        embed.add_field(name='Currently playing:', value=f'[{title}]({url})', inline=False)     
    #        embed.set_thumbnail(url=thumbnail_source)
    #
    #    ########## UPDATE ##########
    #    
    #    await edit_msg.edit(content=content,  embed=embed, view=Buttons())

    async def shuffle(self):
        if self.music_queue:
            if not self.is_shuffled:
                self.music_queue_no_shuffle = self.music_queue[:]
                random.shuffle(self.music_queue)
                self.is_shuffled = True

            else:
                self.music_queue = [i for i in self.music_queue_no_shuffle if i in self.music_queue]
                self.is_shuffled = False

    async def previous(self):
        return

    async def pause(self):
        if self.is_playing:
            self.is_playing = False
            self.is_paused = True
            self.vc.pause()

        elif self.is_paused:
            self.is_playing = True
            self.is_paused = False
            self.vc.resume()

    async def skip(self):
        self.vc.stop()
        await self.play_next()

    async def loop(self):
        if self.vc is None:
            pass

        elif not self.is_looped and not self.is_looped_single:
            self.is_looped = True

        elif not self.is_looped and self.is_looped_single:
            self.is_looped_single = False

        elif self.is_looped and not self.is_looped_single:
            self.is_looped = False
            self.is_looped_single = True

    async def clear(self):
        self.music_queue = []

    async def dc(self):
        self.is_playing = False
        self.is_paused = False
        self.is_looped = False
        self.is_shuffled = False
        self.is_downloading = False

        self.music_queue = []
        self.music_queue_no_shuffle = []
        self.music_history = []
        self.currently_playing = []

        await self.vc.disconnect()

    async def queue(self):
        if self.short_queue:
            self.short_queue = False
        else:
            self.short_queue = True

    async def history(self):
        if self.show_history:
            self.show_history = False

            if self.was_long_queue:
                self.short_queue = False

        else:
            self.show_history = True

            if not self.short_queue:
                self.was_long_queue = True
                self.short_queue = True

    # searching the item on YouTube
    def search_yt(self, item):
        with YoutubeDL(self.YDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info("ytsearch:%s" % item, download = False)['entries'][0]
            # TODO: test exception handling
            except ydl.utils.DownloadError:
                return False

        return {'source': info['formats'][0]['url'], 'title': info['title'], 'id': info['id']}

    async def done_playing(self):
        await self.play_next()

    async def play_next(self):
        loop = asyncio.get_event_loop()
        if len(self.music_queue) > self.p_index:
            self.is_playing = True

            #self.music_history.append(self.music_queue[0])

            if self.is_looped:
                if self.p_index == len(self.music_queue) - 1:
                    self.p_index = 0
            
            elif self.is_looped_single:     # The Index doesn't change, remaining in the same position
                pass
            
            else:
                self.p_index += 1
            
            m_url = self.music_queue[self.p_index][0]['source']
            self.currently_playing = self.music_queue[self.p_index]


            _msg_update = await self.update_msg()

            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS),
                         after = lambda e: loop.create_task(self.done_playing()))

        else:
            self.currently_playing = []
            self.is_playing = False
            _msg_update = await self.update_msg()
            return

    async def play_music(self):
        loop = asyncio.get_event_loop()
        if len(self.music_queue) > self.p_index:
            self.is_playing = True

            m_url = self.music_queue[self.p_index][0]['source']  #music_queue[index][vc]

            # try to connect to voice channel if you are not already connected
            if self.vc is None or not self.vc.is_connected():
                self.vc = await self.music_queue[self.p_index][1].connect()

                # in case we fail to connect
                if self.vc is None:
                    return
            else:
                await self.vc.move_to(self.music_queue[0][1])

            #self.music_history.append(self.music_queue[0])
            self.currently_playing = self.music_queue[self.p_index]

            if self.is_looped:
                if self.p_index == len(self.music_queue) - 1:
                    self.p_index = 0


            _msg_update = await self.update_msg()

            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS),
                         after = lambda e: loop.create_task(self.done_playing()))

        else:
            self.currently_playing = []
            self.is_playing = False
            _msg_update = await self.update_msg()
            return

    async def add_to_queue(self, query, vc):
        self.is_downloading = True
        await self.update_msg()
        # if query contains a spotify link
        if any(link in query for link in self.spotify_links):
            get_songs = GetSpotifySongs(link = query)
            added_songs = get_songs.call_refresh()[:self.add_limit]

            for i in range(len(added_songs)):
                # TODO: add single song to queue function
                song = self.search_yt(added_songs[i])
                if isinstance(song, bool):
                    # if we fail to find the song
                    print(f'{c_time()} {c_err()} failed to add song {added_songs[i]}')
                else:
                    self.music_queue.append([song, vc])
                    if self.is_shuffled:
                        self.music_queue_no_shuffle.append([song, vc])
                    if not self.is_playing:
                        await self.play_music()

        else:
            song = self.search_yt(query)
            if isinstance(song, bool):
                print(f'{c_time()} {c_err()} failed to add song {query}')
            else:
                self.music_queue.append([song, vc])
                if self.is_shuffled:
                    self.music_queue_no_shuffle.append([song, vc])
                if not self.is_playing:
                    await self.play_music()

        self.is_downloading = False
        await self.update_msg()

    async def swap(self, i: int, j: int) -> None:
        """
        Swaps songs on indexes i and j in self.music_queue.
        Skips to next song if -1 passed as argument.
        Updates message.
        """
        # if -1 not requested index => swap places in list
        if not (i == -1 or j == -1):
            self.music_queue[i], self.music_queue[j] = self.music_queue[j], self.music_queue[i]
            await self.update_msg()
        # if -1 is requested index => skip to song with requested index
        else:
            x = i if j == 0 else j
            swapped = self.music_queue.pop(x)
            self.music_queue = [swapped] + self.music_queue
            self.music_queue = self.music_queue[:x + 1] + self.currently_playing + self.music_queue[x + 1:]
            self.vc.stop()
            await self.play_next()

    def get_queue_len(self) -> int:
        """
        Returns number of songs in queue.
        """
        return len(self.music_queue[self.p_index:])


class Buttons(discord.ui.View):
    def __init__(self, cog, timeout=180):
        super().__init__(timeout = timeout)

    # first row

    @discord.ui.button(label = '⎇', style = discord.ButtonStyle.secondary, row = 0)
    async def shuffle_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(view = self)

    @discord.ui.button(label = '⯬', style = discord.ButtonStyle.secondary, row = 0)
    async def previous_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(view = self)

    @discord.ui.button(label = '▉', style = discord.ButtonStyle.secondary, row = 0)
    async def pause_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(view = self)

    @discord.ui.button(label = '⯮', style = discord.ButtonStyle.secondary, row = 0)
    async def skip_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(view = self)

    @discord.ui.button(label = '⭯', style = discord.ButtonStyle.secondary, row = 0)
    async def loop_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(view = self)

    # second row

    @discord.ui.button(label = '✖', style = discord.ButtonStyle.secondary, row = 1)
    async def clear_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(view = self)

    @discord.ui.button(label = '#', style = discord.ButtonStyle.secondary, row = 1)
    async def dc_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(view = self)

    @discord.ui.button(label = '≡', style = discord.ButtonStyle.secondary, row = 1)
    async def list_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(view = self)

    @discord.ui.button(label = '⯆', style = discord.ButtonStyle.secondary, row = 1)
    async def queue_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(view = self)

    @discord.ui.button(label = '⯅', style = discord.ButtonStyle.secondary, row = 1)
    async def history_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(view = self)

    # @discord.ui.button(label="loop",style=discord.ButtonStyle.success)
    # async def loop_btn(self, child:discord.ui.Button, interaction:discord.Interaction):
    #    await interaction.response.edit_message(view=self)


# TODO: add -> MusicCog typehint
async def create_music_cog(bot, guild: discord.guild.Guild) -> MusicCog:
    """
    Creates a MusicCog object for guild with id guild_id.
    A MusicCog is only created by calling this function, not by directly declaring an instance.
    After creating the instance, __init_async__() is called, which contains async commands needed for initialization.
    """
    m_cog = MusicCog(bot, guild)
    await m_cog.__init_async__()
    return m_cog


def replace(file_path: str, pattern: str, subst: str) -> None:
    """
    In a text file, replaces pattern with subst.
    """
    # create temp file
    fh, abs_path = mkstemp()
    with fdopen(fh, 'w') as new_file:
        with open(file_path) as old_file:
            for line in old_file:
                new_file.write(line.replace(pattern, subst))
    # copy the file permissions from the old file to the new file
    copymode(file_path, abs_path)
    # remove original file
    remove(file_path)
    # move new file
    move(abs_path, file_path)


async def replace_command_channel(guild: discord.guild.Guild, new_id: int) -> dict:
    """
    For a specified guild, replaces existing command channel id with new_id in channel_ids.txt.
    """
    channel = await guild.create_text_channel('song-requests')
    channel_id = channel.id

    print(f'{c_time()} Command channel deleted, {c_event("CREATED CHANNEL")} {c_channel(channel_id)}')

    return {'pattern': f'{new_id}', 'subst': f'{channel_id}', 'id': channel_id}


async def get_id(guild: discord.guild.Guild) -> int:
    replaced = False
    guild_id = guild.id
    with open('channel_ids.txt') as f:
        for line in f:
            # every line is a pair of {guild id} {channel id}
            r = line.split()
            if int(r[0]) == guild_id:
                channel_id = int(r[1])

                # check if channel still exists
                guild_channels = [channel.id for channel in guild.text_channels]

                if channel_id not in guild_channels:
                    replaced_info = await replace_command_channel(guild, channel_id)
                    # info to replace old channel id
                    pattern = replaced_info['pattern']
                    subst = replaced_info['subst']
                    # new id
                    channel_id = replaced_info['id']

                    replaced = True

                break

        else:
            # existing channel was not found
            # has to create new channel
            channel = await guild.create_text_channel('song-requests')
            channel_id = channel.id

            with open('channel_ids.txt', 'a') as g:
                g.write(f'{guild_id} {channel_id}\n')

            print(f'{c_time()} {c_event("CREATED CHANNEL")} {c_channel(channel_id)}')

        f.close()

        if replaced:
            replace("channel_ids.txt", pattern, subst)

        return channel_id


def create_server_playlist(guild_id):
    # get directory with server playlists
    server_list_dir = f'{os.getcwd()}/server_lists'
    # list all already created server playlist files
    server_list_files = [os.path.join(server_list_dir, f) for f in os.listdir(server_list_dir) if
                         os.path.isfile(os.path.join(server_list_dir, f))]
    # list all server IDs of servers that have files created
    server_list_ids = [int(file.split('\\')[-1].split('.')[0]) for file in server_list_files]

    if guild_id not in server_list_ids:
        path = f'{os.getcwd()}\\server_lists\\{guild_id}.txt'
        with open(path, 'w'):
            pass


def get_vc(user):
    """
    The function takes a Discord user object and returns the id of the voice channel the user is in.
    If the user is not in a voice channel, function returns False.
    """
    try:
        user_vc = user.voice.channel
    except AttributeError:
        user_vc = False
    return user_vc


def get_playlists(guild_id):
    path = f'{os.getcwd()}\\server_lists\\{guild_id}.txt'

    with open(path, 'r') as f:
        server_lists = f.read().split('>>>')[1:]

    r = {}
    for s_list in server_lists:
        list_name, list_songs = map(str, s_list.split('<<<'))
        list_songs = list_songs.split('\n')

        r[list_name] = list_songs

    return r


