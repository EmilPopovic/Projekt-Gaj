from time import time
import discord, random, asyncio, os
from datetime import datetime
from discord.ext import commands
from discord import app_commands
#from discord_components import Button, DiscordComponents, ButtonStyle, Select, SelectOption
from youtube_dl import YoutubeDL
from spotify import GetSpotifySongs
from colors import *
from tempfile import mkstemp
from shutil import move, copymode
from os import fdopen, remove


async def create_music_cog(bot, guild):
    m_cog = MusicCog(bot, guild)
    await m_cog._init()
    return m_cog


def replace(file_path: str, pattern: str, subst: str) -> None:
    """
    In a text file, replaces pattern with subst.
    """
    #Create temp file
    fh, abs_path = mkstemp()
    with fdopen(fh,'w') as new_file:
        with open(file_path) as old_file:
            for line in old_file:
                new_file.write(line.replace(pattern, subst))
    #Copy the file permissions from the old file to the new file
    copymode(file_path, abs_path)
    #Remove original file
    remove(file_path)
    #Move new file
    move(abs_path, file_path)


async def replace_command_channel(guild, id) -> dict:
    channel = await guild.create_text_channel('song-requests')
    channel_id = channel.id

    print(f'{c_time()} Command channel deleted, {c_event("CREATED CHANNEL")} {c_channel(channel_id)}')

    pattern = f'{id}'
    subst = f'{channel_id}'

    return {'pattern': pattern, 'subst': subst, 'id': channel_id}


async def get_id(guild):
    replaced = False
    guild_id = guild.id
    with open('channel_ids.txt') as f:
        for line in f:
            # every line is a pair of {guild id} {channel id}
            r = line.split()
            if int(r[0]) == guild_id:
                id = int(r[1])

                # check if channel still exists
                guild_channels = [channel.id for channel in guild.text_channels]

                if id not in guild_channels:
                    replaced_info = await replace_command_channel(guild, id)
                    # info to replace old channel id
                    pattern = replaced_info['pattern']
                    subst = replaced_info['subst']
                    # new id
                    id = replaced_info['id']

                    replaced = True
                    created = True
                
                else:
                    created = False

                break
        
        else:
            ## existing channel was not found
            ## has to create new channel
            channel = await guild.create_text_channel('song-requests')
            id = channel.id
            created = True

            with open('channel_ids.txt', 'a') as f:
                f.write(f'{guild_id} {id}\n')

            print(f'{c_time()} {c_event("CREATED CHANNEL")} {c_channel(id)}')

        f.close()

        if replaced:
            replace("channel_ids.txt", pattern, subst)

        return {'channel_id': id, 'created': created}


def create_server_playlist(id):
    # get directory with server playlists
    server_list_dir = f'{os.getcwd()}/server_lists'
    # list all already created server playlist files
    server_list_files = [os.path.join(server_list_dir, f) for f in os.listdir(server_list_dir) if os.path.isfile(os.path.join(server_list_dir, f))]
    # list all server IDs of servers that have files created
    server_list_ids = [int(file.split('\\')[-1].split('.')[0]) for file in server_list_files]
    
    if id not in server_list_ids:
        path = f'{os.getcwd()}\\server_lists\\{id}.txt'
        with open(path, 'w'):
            pass


class Buttons(discord.ui.View):
    def __init__(self, *, timeout=180):
        super().__init__(timeout=timeout)

    ## first row

    @discord.ui.button(label="shuffle", style=discord.ButtonStyle.blurple, row=0) # or .primary
    async def shuffle_btn(self, interaction:discord.Interaction, button:discord.ui.Button):
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="previous", style=discord.ButtonStyle.blurple, row=0) # or .secondary/.grey
    async def previous_btn(self, interaction:discord.Interaction, button:discord.ui.Button):
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="pause", style=discord.ButtonStyle.blurple, row=0) # or .success
    async def pause_btn(self, interaction:discord.Interaction, button:discord.ui.Button):
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="skip", style=discord.ButtonStyle.blurple, row=0) # or .danger
    async def skip_btn(self, interaction:discord.Interaction, button:discord.ui.Button):
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="loop", style=discord.ButtonStyle.blurple, row=0) # or .danger
    async def loop_btn(self, interaction:discord.Interaction, button:discord.ui.Button):
        await interaction.response.edit_message(view=self)

    ## second row
    
    @discord.ui.button(label="clear", style=discord.ButtonStyle.blurple, row=1) # or .primary
    async def clear_btn(self, interaction:discord.Interaction, button:discord.ui.Button):
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="dc", style=discord.ButtonStyle.blurple, row=1) # or .secondary/.grey
    async def dc_btn(self, interaction:discord.Interaction, button:discord.ui.Button):
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="list", style=discord.ButtonStyle.blurple, row=1) # or .success
    async def list_btn(self, interaction:discord.Interaction, button:discord.ui.Button):
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="queue", style=discord.ButtonStyle.blurple, row=1) # or .danger
    async def queue_btn(self, interaction:discord.Interaction, button:discord.ui.Button):
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label="history", style=discord.ButtonStyle.blurple, row=1) # or .danger
    async def history_btn(self, interaction:discord.Interaction, button:discord.ui.Button):
        await interaction.response.edit_message(view=self)

    #@discord.ui.button(label="loop",style=discord.ButtonStyle.success)
    #async def loop_btn(self, child:discord.ui.Button, interaction:discord.Interaction):
    #    await interaction.response.edit_message(view=self)


class MusicCog(commands.Cog):
    ## function runs on bot start
    def __init__(self, bot, guild):
        self.bot = bot

        self.guild = guild
        
        ## defauld bot states
        self.is_playing = False
        self.is_paused = False
        self.is_looped = False
        self.is_looped_single = False
        self.is_shuffled = False
        self.is_downloading = False
        self.short_queue = False
        self.show_history = False
        self.was_long_queue = False
        
        ## song lists
        self.music_queue = []
        self.music_queue_no_shuffle = []
        self.music_history = []
        self.currently_playing = []
        
        ## id of command message
        self.on_ready_message = []

        ## time of last button press
        self.time_of_last_press = False

        ## youtube download options
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
        
        ## encoder options
        self.FFMPEG_OPTIONS = {
            'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
            'options': '-vn'
            }

        self.spotify_links = ['https://open.spotify.com/playlist/', 'https://open.spotify.com/album/']

        self.add_limit = 30

        ## initiate voice
        self.vc = None

        #create_server_playlist()

    ## async part of __init__
    async def _init(self):
        guild_obj = self.bot.get_guild(self.guild)
        bot_channel_id_return = await get_id(guild_obj)
        self.bot_channel_id = bot_channel_id_return['channel_id']

        #clear command channel on start
        await self.bot.get_channel(self.bot_channel_id).purge(limit=1)

        # start and update new live message
        embed = discord.Embed(title='Welcome to Štef!', description='Use !p to add more songs to queue.', color=0xf1c40f)
        self.on_ready_message = await self.bot.get_channel(self.bot_channel_id).send(embed=embed)

        await self.update_msg()
    

    async def update_msg(self):
        edit_msg = self.on_ready_message
        
        # message content
        content = ''

        new_history = self.music_history[:-1] if self.is_playing else self.music_history

        if new_history and self.show_history:
            content += '**History:**\n'

            for i in range(len(new_history)):
                content += f'{i+1} {new_history[i][0]["title"]}\n'

            if self.music_queue:
                content += '\n'


        if self.music_queue:
            content += '**Queue:**\n'

            for i in range(len(self.music_queue) - 1, -1, -1):
                if self.short_queue and i < 5 or not self.short_queue:
                    content += f'{i+1} {self.music_queue[i][0]["title"]}\n'
                    

        await edit_msg.edit(content='Pozdrav Brate', view=Buttons())


    #async def update_msg(self):
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


    def get_vc(self, user):
        '''
        The function takes a Discord user object and returns the id of the voice channel the user is in.
        If the user is not in a voice channel, function returns False.
        '''
        try:
            user_vc = user.voice.channel
        except AttributeError:
            user_vc = False
        return user_vc


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


    @commands.Cog.listener()
    async def on_button_click(self, interaction):
        '''
        > Function is called every time a command button is pressed.
        > Buttons are defined in self.update_message()
        > Custom id of button interaction is in format '{button name}_{id of guild where button was pressed}'.
        > Button interactions are ignored if user is not in the same voice channel as the bot.
        > Button press updates live message.
        '''
        
        # fix of double click bug
        # button clicks within 0.1 seconds of each other will be ignored
        
        time_of_press = datetime.now()

        if not self.time_of_last_press:
            self.time_of_last_press = time_of_press
        else:
            time_since_last_press = (time_of_press - self.time_of_last_press).total_seconds()
            self.time_of_last_press = time_of_press

            if time_since_last_press < 0.1:
                return

        # checking if user that pressed the button is in the same voice channel as the bot

        custom_id = interaction.component.custom_id.split('_')

        interaction_id = custom_id[0]        # id of pressed button

        guild_id = int(custom_id[1])         # id of guild where button was pressed
        user_id = interaction.user.id        # id of user who pressed the button

        bot_id = self.bot.user.id            # id of bot

        guild = self.bot.get_guild(guild_id) # guild object from guild_id
        user = guild.get_member(user_id)     # user object from user_id
        bot_user = guild.get_member(bot_id)  # user object from bot_id

        user_vc = self.get_vc(user)
        bot_vc = self.get_vc(bot_user)


        if (not user_vc) or (bot_vc != user_vc): # ignore button press if bot is not in voice channel or in a different channel than the user
            pass


        elif interaction_id == 'shuffle':
            await self.shuffle()
       
        elif interaction_id == 'previous':
            if len(self.music_history) >= 2 or (not self.is_playing and not self.is_paused and len(self.music_history) == 1):
                if not self.is_playing and not self.is_paused:
                    previous = self.music_history[-1]
                    current = None
                    self.music_history = self.music_history[:-1]
                else:
                    previous = self.music_history[-2]
                    current = self.currently_playing
                    self.music_history = self.music_history[:-2]

                self.music_queue = [previous] + [current] + self.music_queue

                if self.vc != None and self.vc:
                    self.vc.stop()
                    await self.play_next()

        elif interaction_id == 'pause':
            await self.pause()

        elif interaction_id == 'skip':
            await self.skip()

        elif interaction_id == 'loop':
            await self.loop()

        elif interaction_id == 'clear':
            await self.clear()

        elif interaction_id == 'dc':
            await self.dc()
        
        elif interaction_id == 'list':
            ctx = self.bot.get_channel(self.bot_channel_id)

            # privately responds with a select menu with options of 'Private list' and 'Server list'
            await interaction.respond(content='Select an option.',
                components=[Select(
                    placeholder='Select something!',
                    options=[
                        #SelectOption(label='Private list', value='1'),
                        SelectOption(label='Server list', value='2'),
                        SelectOption(label='Cancel', value='-1')
                        ],
                        custom_id='select_location'
                    )])
            list_interaction = await self.bot.wait_for('select_option', check=lambda inter: inter.custom_id == 'select_location')
            
            # id of wanted list source
            res_id = list_interaction.values[0]

            # if Private list option selected
            if res_id == '1':
                pass
            
            # if Server list option selected
            elif res_id == '2':
                r = self.get_playlists(guild_id)
                interaction_options = list(r.keys())
                
                await list_interaction.respond(content='Select an option.',
                        components=[Select(placeholder='Select something!',
                            options=[
                                SelectOption(label=interaction_options[i], value=i) for i in range(len(interaction_options))
                            ],
                            custom_id='select_playlist'
                        )])
                list_interaction2 = await self.bot.wait_for('select_option', check=lambda inter: inter.custom_id == 'select_playlist')
                
                # id of wanted playlist
                res_id2 = list_interaction2.values[0]

                playlist_name = interaction_options[int(res_id2)]
                await list_interaction2.send(f'Adding playlist `{playlist_name}` to queue!\n**Please dismiss the previous messages.**')

                songs = [i for i in r[playlist_name] if i] # names of all songs in playlist

                self.is_downloading = True
                await self.edit_live_msg()

                # add all songs to queue
                for i in range(len(songs)):
                    song = songs[i]
                    song = self.search_yt(song)
                    
                    if type(song) == type(True):
                        pass
                    else:
                        self.music_queue.append([song, bot_vc])

                        if self.is_shuffled:
                            self.music_queue_no_shuffle.append([song, bot_vc])

                        if not self.is_playing:
                            await self.play_music(ctx)
                    
                    await self.edit_live_msg()

                self.is_downloading = False
                await self.edit_live_msg()
                    

            # if Cancel option selected
            else:
                pass

            
            await list_interaction.send(res_id)
        
        elif interaction_id == 'queue':
            await self.queue()

        elif interaction_id == 'history':
            await self.history()


        await self.edit_live_msg()
        
        try:
            await interaction.respond()
        except:
            pass

    
    def get_playlists(self, id):
        path = f'{os.getcwd()}\\server_lists\\{id}.txt'
        
        with open(path, 'r') as f:
            server_lists = f.read().split('>>>')[1:]

        r = {}
        for s_list in server_lists:
            list_name, list_songs = map(str, s_list.split('<<<'))
            list_songs = list_songs.split('\n')
            
            r[list_name] = list_songs

        return r


    #searching the item on youtube
    def search_yt(self, item):
        with YoutubeDL(self.YDL_OPTIONS) as ydl:
            try: 
                info = ydl.extract_info("ytsearch:%s" % item, download=False)['entries'][0]
            except Exception:
                return False

        return {'source': info['formats'][0]['url'], 'title': info['title'], 'id': info['id']}


    async def done_playing(self):
        await self.play_next()


    async def play_next(self):
        loop = asyncio.get_event_loop()
        if len(self.music_queue) > 0:
            self.is_playing = True

            m_url = self.music_queue[0][0]['source']

            self.music_history.append(self.music_queue[0])
            self.currently_playing = self.music_queue[0]

            if self.is_looped:
                self.music_queue.append(self.currently_playing)
            elif self.is_looped_single:
                self.music_queue = [self.currently_playing] + self.music_queue

            self.music_queue.pop(0)
            
            _msg_update = await self.edit_live_msg()

            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: loop.create_task(self.done_playing()))

        else:
            self.currently_playing = []
            self.is_playing = False
            _msg_update = await self.edit_live_msg()
            return


    async def play_music(self):
        loop = asyncio.get_event_loop()
        if len(self.music_queue) > 0:
            self.is_playing = True

            m_url = self.music_queue[0][0]['source']
            
            #try to connect to voice channel if you are not already connected
            if self.vc == None or not self.vc.is_connected():
                self.vc = await self.music_queue[0][1].connect()

                #in case we fail to connect
                if self.vc == None:
                    return
            else:
                await self.vc.move_to(self.music_queue[0][1])
            
            self.music_history.append(self.music_queue[0])
            self.currently_playing = self.music_queue[-1]

            if self.is_looped:
                self.music_queue.append(self.currently_playing)

            self.music_queue.pop(0)

            _msg_update = await self.update_msg()

            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: loop.create_task(self.done_playing()))

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
            get_songs = GetSpotifySongs(link=query)
            added_songs = get_songs.call_refresh()[:self.add_limit]

            for i in range(len(added_songs)):
                song = self.search_yt(added_songs[i])
                if type(song) == type(True):
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
            if type(song) == type(True):
                print(f'{c_time()} {c_err()} failed to add song {query}')
            else:
                self.music_queue.append([song, vc])
                if self.is_shuffled:
                    self.music_queue_no_shuffle.append([song, vc])
                if self.is_playing == False:
                    await self.play_music()

        self.is_downloading = False
        self.update_msg()


    @commands.command(name='swap', aliases=['s'], help='swaps songs in queue with selected numbers')
    async def swap(self, ctx, *args):
        query = " ".join(args)
        await ctx.channel.purge(limit=1)
        
        # message has to consist of two numbers only
        for i in query:
            if i not in (' 1234567890'):
                return

        list = query.split()

        if len(list) != 2:
            return

        i, j = map(int, query.split())

        # both numbers can't be 0
        if i <= len(self.music_queue) and j < len(self.music_queue):
            if not (i == 0 or j == 0):
                self.music_queue[i-1], self.music_queue[j-1] = self.music_queue[j-1], self.music_queue[i-1]

            elif i == 0 and j == 0:
                return

            else:
                x = i if j == 0 else j
                swapped = self.music_queue.pop(x - 1)
                self.music_queue = [swapped] + self.music_queue
                self.music_queue = self.music_queue[:x+1] + self.currently_playing + self.music_queue[x+1:]
                self.vc.stop()
                await self.play_next()

        else:
            return


        await self.update_msg()
