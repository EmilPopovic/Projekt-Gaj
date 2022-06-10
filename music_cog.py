import discord, random, asyncio
from discord.ext import commands
from discord_components import *

from youtube_dl import YoutubeDL
from spotify import GetSongs


class music_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        DiscordComponents(self.bot)
    
        #all the music related stuff
        self.is_playing = False
        self.is_paused = False
        self.is_looped = False
        self.is_looped_single = False
        self.is_shuffled = False
        self.is_downloading = False
        self.short_queue = False
        self.show_history = False

        # liste [pjesma, kanal]
        self.music_queue = []
        self.music_queue_no_shuffle = []
        self.music_history = []
        self.currently_playing = []

        # popis poruka koje treba obrisati
        self.music_queue_messages = []
        self.music_history_messages = []
        self.on_ready_messages = []

        
        self.YDL_OPTIONS = {'format': 'bestaudio', 'noplaylist':'True'}
        self.FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}

        self.vc = None

    
    async def edit_live_msg(self):
        if not self.is_downloading:
            previous_button = Button(label='⯬', custom_id='previous')
            skip_button = Button(label='⯮', custom_id='skip')

            clear_button = Button(label='✖', custom_id='clear', style=ButtonStyle.red)
            dc_button = Button(label='#', custom_id='dc', style=ButtonStyle.red)
            help_button = Button(label='?', custom_id='help')
            history_button = Button(label='⯅', custom_id='history')

            if not self.is_paused:
                pause_button = Button(label='▉', custom_id='pause')
            else:
                pause_button = Button(label='▶', custom_id='pause', style=ButtonStyle.green)

            if not self.is_shuffled:
                shuffle_button = Button(label='⎇', custom_id='shuffle')
            else:
                shuffle_button = Button(label='⎇', custom_id='shuffle', style=ButtonStyle.green)

            if self.is_looped:
                loop_button = Button(label='⭯', custom_id='loop', style=ButtonStyle.green)
            elif self.is_looped_single:
                loop_button = Button(label='⭯', custom_id='loop', style=ButtonStyle.blue)
            else:
                loop_button = Button(label='⭯', custom_id='loop')

            if not self.short_queue:
                queue_button = Button(label='⯆', custom_id='queue')
            else:
                queue_button = Button(label='⯆', custom_id='queue', style=ButtonStyle.green)

            
        else:
            shuffle_button = Button(label='⎇', custom_id='shuffle', disabled=True)
            previous_button = Button(label='⯬', custom_id='previous', disabled=True)
            pause_button = Button(label='▉', custom_id='pause', disabled=True)
            skip_button = Button(label='⯮', custom_id='skip', disabled=True)
            loop_button = Button(label='⭯', custom_id='loop', disabled=True)

            clear_button = Button(label='✖', custom_id='clear', disabled=True)
            dc_button = Button(label='#', custom_id='dc', disabled=True)
            help_button = Button(label='?', custom_id='help', disabled=True)
            queue_button = Button(label='⯆', custom_id='queue', disabled=True)
            history_button = Button(label='⯅', custom_id='history', disabled=True)

        buttons1 = [shuffle_button, previous_button, pause_button, skip_button, loop_button]
        buttons2 = [clear_button, dc_button, help_button, queue_button, history_button]

        msg = 'Welcome to Štef! Use !p to add more songs to queue.\n'

        #if self.music_queue:
        #    msg += '\nQueue:\n'

        #    for i in range(len(self.music_queue) - 1, -1, -1):
        #        if self.short_queue and i < 5 or not self.short_queue:
        #            msg += f'{i+1} {self.music_queue[i][0]["title"]}\n'

        #if self.currently_playing:
        #    msg += '\n'
        #    msg += f'Currently playing:\n{self.currently_playing[0]["title"]}'

        #msg = f'```{msg}```'

        embed = discord.Embed(title='Welcome to Štef!', description='Use !p to add more songs to queue.', color=0xf1c40f)

        if self.music_queue:
            len_queue = len(self.music_queue)
            n_of_10 = len_queue // 10

            queue_strings = [self.music_queue[i][0]["title"] for i in range(len_queue)]

            print(list(range(len_queue - 1, n_of_10 * 10 - 1, -1)))
            print(len_queue)

            msg = ''
            for i in range(len_queue - 1, len_queue % 10 - 1, -1):
                msg += f'{i+1} {self.music_queue[i][0]["title"]}\n'
            
            if msg:
                embed.add_field(name='Queue:', value=msg, inline=False)

            for i in range(n_of_10 - 1, -1, -1):
                msg = ''
                for j in range(9, -1, -1):
                    index = n_of_10 * i + j
                    msg += f'{index+1} {self.music_queue[index][0]["title"]}\n'
                embed.add_field(name=None, value=msg, inline=False)
    
            #queue_value = ''

            #for i in range(len(self.music_queue) - 1, -1, -1):
            #    if self.short_queue and i < 5 or not self.short_queue:
            #        queue_value += f'{i+1} {self.music_queue[i][0]["title"]}\n'

            #embed.add_field(name='Queue:', value=queue_value, inline=False)

        if self.currently_playing:
            embed.add_field(name='Currently playing:', value=f'{self.currently_playing[0]["title"]}', inline=False)
        
        await self.on_ready_messages[0].edit(embed=embed, components=[buttons1, buttons2])


    @commands.Cog.listener()
    async def on_ready(self):
        #buttons = [Button(label='⎇', custom_id='shuffle'), Button(label='⯬', custom_id='previous', disabled=True), Button(label='▉', custom_id='pause'), Button(label='⯮', custom_id='skip'), Button(label='⭯', custom_id='loop')]
        test_channel_id = 972589111980458054
        await self.bot.get_channel(test_channel_id).purge(limit=100)

        embed = discord.Embed(title='Welcome to Štef!', description='Use !p to add more songs to queue.', color=0xf1c40f)

        msg = await self.bot.get_channel(test_channel_id).send(embed=embed)
        self.on_ready_messages.append(msg)
        await self.edit_live_msg()


    @commands.Cog.listener()
    async def on_button_click(self, interaction):
        interaction_id = interaction.component.custom_id
        
        if interaction_id == 'shuffle':
            if self.music_queue:
                if not self.is_shuffled:
                    self.music_queue_no_shuffle = self.music_queue[:]
                    random.shuffle(self.music_queue)
                    self.is_shuffled = True

                else:
                    self.music_queue = [i for i in self.music_queue_no_shuffle if i in self.music_queue]
                    self.is_shuffled = False
        
        
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
            if self.is_playing:
                self.is_playing = False
                self.is_paused = True
                self.vc.pause()
            
            elif self.is_paused:
                self.is_playing = True
                self.is_paused = False
                self.vc.resume()


        elif interaction_id == 'skip':
            if self.vc != None and self.vc:
                self.vc.stop()
                await self.play_next()


        elif interaction_id == 'loop':
            if self.vc is None:
                pass

            elif not self.is_looped and not self.is_looped_single:
                self.is_looped = True

            elif not self.is_looped and self.is_looped_single:
                self.is_looped_single = False

            elif self.is_looped and not self.is_looped_single:
                self.is_looped = False
                self.is_looped_single = True

        
        elif interaction_id == 'clear':
            self.music_queue = []


        elif interaction_id == 'dc':
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
        

        elif interaction_id == 'queue':
            if self.short_queue:
                self.short_queue = False
            else:
                self.short_queue = True

        await self.edit_live_msg()
        
        try:
            await interaction.respond()
        except:
            pass


     #searching the item on youtube
    def search_yt(self, item):
        with YoutubeDL(self.YDL_OPTIONS) as ydl:
            try: 
                info = ydl.extract_info("ytsearch:%s" % item, download=False)['entries'][0]
            except Exception: 
                return False

        return {'source': info['formats'][0]['url'], 'title': info['title']}


    async def play_next(self):
        if len(self.music_queue) > 0:
            self.is_playing = True

            # uzmi url na yt
            m_url = self.music_queue[0][0]['source']

            # dodaj pjesmu na listu povijesti
            self.music_history.append(self.music_queue[0])
            self.currently_playing = self.music_history[-1]

            if self.is_looped:
                self.music_queue.append(self.currently_playing)
            elif self.is_looped_single:
                self.music_queue = [self.currently_playing] + self.music_queue

            # makni pjesmu s popisa budućih
            self.music_queue.pop(0)

            #await self.edit_live_msg()

            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next())
        else:
            #self.is_playing = False
            #self.currently_playing = []
            #await self.edit_live_msg()
            return


    # infinite loop checking 
    async def play_music(self, ctx):
        if len(self.music_queue) > 0:
            self.is_playing = True

            m_url = self.music_queue[0][0]['source']
            
            #try to connect to voice channel if you are not already connected
            if self.vc == None or not self.vc.is_connected():
                self.vc = await self.music_queue[0][1].connect()

                #in case we fail to connect
                if self.vc == None:
                    await ctx.send("Ne mogu se spojiti u kanal")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=1)
                    return
            else:
                await self.vc.move_to(self.music_queue[0][1])
            
            
            self.music_history.append(self.music_queue[0])
            self.currently_playing = self.music_queue[-1]

            if self.is_looped:
                self.music_queue.append(self.currently_playing)

            #remove the first element as you are currently playing it
            self.music_queue.pop(0)

            #await self.edit_live_msg()

            self.vc.play(discord.FFmpegPCMAudio(m_url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next())
        else:
            #self.is_playing = False
            #self.currently_playing = []
            #await self.edit_live_msg()
            return

        
    def loading_bar(self, current, total):
        percentage = current / total * 100
        n_of_tiles = int(percentage // 10)
        loading_bar_str = ('▮' * n_of_tiles) + ('▯' * (10 - n_of_tiles))
        return loading_bar_str


    @commands.command(name="play", aliases=["p","playing"], help="Plays a selected song from youtube")
    async def play(self, ctx, *args):
        query = " ".join(args)

        if 'https://open.spotify.com/playlist/' in query or 'https://open.spotify.com/album/' in query:
            print(f'Podijeljena je playlista/album:\nlink: {query}')
            await ctx.channel.purge(limit=1)
            
            get_songs = GetSongs(link=query)
            lista = get_songs.call_refresh()
            random.shuffle(lista)
            lista = lista[:30]

            voice_channel = ctx.author.voice.channel

            if voice_channel is None:
                #you need to be connected so that the bot knows where to go
                await ctx.send("Spoji se u kanal!")
                await asyncio.sleep(1)
                await ctx.channel.purge(limit=1)

            elif self.is_paused:
                        self.is_playing = True
                        self.is_paused = False
                        self.vc.resume()

            else:
                msg = await ctx.send(f"```Dodajem pjesme: ▯▯▯▯▯▯▯▯▯▯ 0 / {len(lista)}```")

                self.is_downloading = True
                await self.edit_live_msg()

                for i in range(len(lista)):
                    
                    await msg.edit(content=f"```Dodajem pjesme: {self.loading_bar(i+1, len(lista))} {i+1} / {len(lista)}```")

                    pjesma = lista[i]
                    song = self.search_yt(pjesma)
                    if type(song) == type(True):
                        await ctx.send("Ne mogu skinuti pjesmu.")
                        await asyncio.sleep(1)
                        await ctx.channel.purge(limit=1)
                    else:
                        self.music_queue.append([song, voice_channel])
                        if not self.is_playing:
                            await self.play_music(ctx)
                    await self.edit_live_msg()

                self.is_downloading = False
                await self.edit_live_msg()

            await msg.edit(content='Pjesme dodane!')
            await asyncio.sleep(1)
            await ctx.channel.purge(limit=1)

        else:
            voice_channel = ctx.author.voice.channel
            if voice_channel is None:
                #you need to be connected so that the bot knows where to go
                await ctx.send("Spoji se u kanal!")
                await asyncio.sleep(1)
                await ctx.channel.purge(limit=2)
            elif self.is_paused:
                self.is_playing = True
                self.is_paused = False
                self.vc.resume()
            else:
                song = self.search_yt(query)
                if type(song) == type(True):
                    await ctx.send("Ne mogu skinuti pjesmu.")
                    await asyncio.sleep(1)
                    await ctx.channel.purge(limit=2)
                else:
                    await ctx.channel.purge(limit=1)
                    
                    self.music_queue.append([song, voice_channel])
                    
                    await self.edit_live_msg()
                    
                    if self.is_playing == False:
                        await self.play_music(ctx)


    @commands.command(name='history', aliases=['h', 'played', 'past'], help='prikazuje puštene pjesme')
    async def history(self, ctx):
        await ctx.channel.purge(limit=1)
        retval = ''
        for i in range(len(self.music_history)):
            retval += self.music_history[i][0]['title'] + '\n'

        if retval != '':
            msg = await ctx.send(retval)
            self.music_history_messages.append(msg.id)
        else:
            await ctx.send('Nema pjesama!')
            await asyncio.sleep(1)
            await ctx.channel.purge(limit=2)
    
    
    #@commands.command(name="queue", aliases=["q"], help="Displays the current songs in queue")
    #async def queue(self, ctx):
    #    await ctx.channel.purge(limit=1)
    #    retval = ""
    #    for i in range(len(self.music_queue)):
    #        retval += f'{i+1} {self.music_queue[i][0]["title"]}\n'

    #    if retval != "":
    #        msg = await ctx.send('```' + retval + '```')
    #        self.music_queue_messages.append(msg.id)
    #    else:
    #        await ctx.send("Nema pjesama!")
    #        await asyncio.sleep(1)
    #        await ctx.channel.purge(limit=1)


    #@commands.command(name="clear", aliases=["c", "bin"], help="Stops the music and clears the queue")
    #async def clear(self, ctx):
    #    self.music_queue = []
    #    self.music_history = self.music_history.pop(-1)
    #    
    #    self.delh(ctx)
    #    await asyncio.sleep(1)
    #    self.delq(ctx)
    #    await asyncio.sleep(1)

    #    await ctx.send("Sve čisto!")
    #    await asyncio.sleep(1)
    #    await ctx.channel.purge(limit=2)


    #@commands.command(name="leave", aliases=["disconnect", "l", "d"], help="Kick the bot from VC")
    #async def dc(self, ctx):
    #    self.is_playing = False
    #    self.is_paused = False
    #    await self.vc.disconnect()
    #    await ctx.channel.purge(limit=1)


    #@commands.command(name='delete_queue', aliases=['delq', 'dq'], help='briše sve odgovore na !q poruke')
    #async def delq(self, ctx):
    #    await ctx.channel.purge(limit=1)
    #    if len(self.music_queue_messages) != 0:
    #        for message_id in self.music_queue_messages:
    #            try:
    #                msg = await ctx.fetch_message(message_id)
    #                await msg.delete()
    #            except:
    #                pass
    #        self.music_history_messages.clear()


    #@commands.command(name='delete_history', aliases=['delh', 'dh'], help='briše sve odgovore na !h poruke')
    #async def delh(self, ctx):
    #    await ctx.channel.purge(limit=1)
    #    if len(self.music_history_messages) != 0:
    #        for message_id in self.music_history_messages:
    #            try:
    #                msg = await ctx.fetch_message(message_id)
    #                await msg.delete()
    #            except:
    #                pass
    #        self.music_history_messages.clear()


    #@commands.command(name='loop', aliases=['repeat'], help='puštena pjesma stavlja se na kraj liste')
    #async def loop(self, ctx):
    #    await ctx.channel.purge(limit=1)
    #    voice_channel = ctx.author.voice.channel

    #    if voice_channel is None:
    #        await ctx.send("Spoji se u kanal!")
    #        await asyncio.sleep(1)
    #        await ctx.channel.purge(limit=1)
    #    
    #    elif self.is_looped:
    #        await ctx.send("Već se ponavlja!")
    #        await asyncio.sleep(1)
    #        await ctx.channel.purge(limit=1)

    #    else:
    #        self.is_looped = True
    #        await ctx.send("Počinjem ponavljati!")
    #        await asyncio.sleep(1)
    #        await ctx.channel.purge(limit=1)


    #@commands.command(name='shuffle', aliases=['shuf'], help='šafluje kju')
    #async def shuffle(self, ctx):
    #    await ctx.channel.purge(limit=1)
    #    if self.music_queue:
    #        if not self.is_shuffled:
    #            self.music_queue_no_shuffle = self.music_queue
    #            random.shuffle(self.music_queue)
    #            self.is_shuffled = True
    #        else:
    #            new_queue = []
    #            for i in self.music_queue_no_shuffle:
    #                if i in self.music_queue:
    #                    new_queue.append(i)
    #            self.music_queue = new_queue
    #            self.is_shuffled = False


    #@commands.command(name='stoploop', aliases=['sloop', 'sl', 'stop_loop'], help='prestaje ponavljanje')
    #async def stop_loop(self, ctx):
    #    await ctx.channel.purge(limit=1)
    #    voice_channel = ctx.author.voice.channel

    #    if voice_channel is None:
    #        await ctx.send("Spoji se u kanal!")
    #        await asyncio.sleep(1)
    #        await ctx.channel.purge(limit=1)

    #    else:
    #        self.is_looped = False
    #        await ctx.send("Prestajem ponavljati!")
    #        await asyncio.sleep(1)
    #        await ctx.channel.purge(limit=1)


    #@commands.command(name="clear", aliases=["c", "bin"], help="Stops the music and clears the queue")
    #async def clear(self, ctx):
    #    if self.vc != None and self.is_playing:
    #        self.vc.stop()
    #    self.music_queue = []
    #    
    #    music_cog.delh(self, ctx)
    #    await asyncio.sleep(1)
    #    music_cog.delq(self, ctx)
    #    await asyncio.sleep(1)
    #
    #    await ctx.send("Sve čisto!")
    #    await asyncio.sleep(1)
    #    await ctx.channel.purge(limit=2)


    #@commands.command(name='pause', help='pauzira pjesmu')
    #async def pause(self, ctx, *args):
    #    if self.is_playing:
    #        self.is_playing = False
    #        self.is_paused = True
    #        self.vc.pause()
    #        await ctx.send("Pauzirano!")
    #        await asyncio.sleep(1)
    #        await ctx.channel.purge(limit=2)
    #    elif self.is_paused:
    #        self.is_playing = True
    #        self.is_paused = False
    #        self.vc.resume()
    #        await asyncio.sleep(1)
    #        await ctx.channel.purge(limit=1)
    

    #@commands.command(name='resume', help='nastavlja pjesmu')
    #async def resume(self, ctx, *args):
    #    if self.is_paused:
    #        self.is_playing = True
    #        self.is_paused = False
    #        self.vc.resume()
    #        await asyncio.sleep(1)
    #        await ctx.channel.purge(limit=1)


    #@commands.command(name="skip", aliases=["s"], help="Skips the current song being played")
    #async def skip(self, ctx):
    #    if self.vc != None and self.vc:
    #        self.vc.stop()
    #        await ctx.channel.purge(limit=1)
    #        await self.play_next(ctx)