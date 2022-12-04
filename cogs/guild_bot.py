"""
This file is part of Shteff which is released under the GNU General Public License v3.0.
See file LICENSE or go to <https://www.gnu.org/licenses/gpl-3.0.html> for full license details.
"""

# last changed 05/12/22

from os import fdopen, remove
from shutil import move, copymode
from tempfile import mkstemp

import discord

from colors import *
from cogs.player import Player


class GuildBot(Player):
    # TODO: rewrite docstring
    """
    a music cog (instance of GuildBot class) is created for every guild the bot is in

    the music cog executes slash commands defined in main.py
    GuildBot objects control their own Buttons and handle interactions from them

    GuildBot objects manipulate their configuration files
    > channel_ids.txt
        > stores [guild_id, command_channel_id] pairs
        > the command message is displayed in the command channel of every guild
        > the GuildBot can recover a deleted command channel on bot start or guild reset
    > server_lists/{guild_id}.txt
        > server_lists directory contains a file for every guild
        > a guild can have a virtually unlimited number of lists associated with it
        > start of a new list is defined with ">>>{list_name}<<<"
        > every line under a specific list name is considered a song name on the list

    all music cogs are part of the same MainBot object stored in GuildBot.bot

    every GuildBot instance stores bot states
        > is_playing: Bool - if a pointer is currently on a song
        > is_paused: Bool - if the playing of a song is paused
        > is_looped: Bool - if queue is looped
        > is_looped_single: Bool - if single track is looped
        > is_shuffled: Bool - if queue or part of queue is shuffled
        > is_downloading: Bool - if a track or list is currently being downloaded
        > short_queue
        > show_history
        > was_long_queue
        > p_index
        > shuffle_start_index
        > music_queue: list - a list of queued and already played song, a song is represented by a Song object
        > unshuffled_queue
        > skipped_while_shuffled
        > command_message
        > vc
    """
    # MainBot instance GuildBot instance is in
    bot = None

    def __init__(self, bot, guild: discord.guild.Guild):
        super().__init__(self, guild)
        GuildBot.bot = bot
        self.guild: discord.guild.Guild = guild

        # id of command message
        self.command_message: discord.Message | None = None

    # async part of __init__
    async def __init_async__(self) -> None:
        """
        Is part of __init__ function.
        Initiates command channel and command message.
        Clears existing command channel on bot start or cog reset.
        """
        # TODO: store ids in SQL database
        self.bot_channel_id = await GuildBot.get_id(self.guild)

        # clear command channel on start
        await GuildBot.bot.get_channel(self.bot_channel_id).purge(limit = 1)

        # start and update new live message
        embed = discord.Embed(
            title = 'Welcome to Shteff!',
            description = 'Use /play to add more songs to queue.',
            color = 0xf1c40f
        )

        self.command_message = await GuildBot.bot.get_channel(self.bot_channel_id).send(embed = embed, view = Buttons())

    async def update_msg(self) -> None:
        # TODO: finish docstring
        """Refreshes command message according to current bot states, lists and playing status."""
        # message content
        # TODO: check if content longer than content character limit
        # TODO: show playing progress bar
        content = ''

        if self.show_history:
            history = self.music_queue[:self.p_index]
            history.reverse()

            if history:
                content += '**History:**\n'

                for i, song in enumerate(history):
                    content += f'**{i + 1}** {song.to_msg_format()}\n'

                if self.music_queue[self.p_index + 1:]:
                    content += '\n'

        if self.music_queue[self.p_index + 1:]:
            i = self.p_index + 1
            added = 0
            content_len = 0

            song_strs: list[str] = []

            while i < len(self.music_queue) and content_len < 1500:
                if self.short_queue and i - self.p_index >= 5:
                    break
                song = self.music_queue[i]
                to_add = f'**{i - self.p_index}** {song.to_msg_format()}\n'
                song_strs.append(to_add)
                content_len += len(to_add)
                added += 1
                i += 1

            content += '**Queue:**\n'
            not_shown = len(self.music_queue[self.p_index + 1:]) - added
            if not_shown:
                content += f'And **{not_shown}** more...\n\n'
            content += ''.join(song_strs[::-1])

        # embed

        if self.music_queue[self.p_index:] and self.is_playing:
            current = self.music_queue[self.p_index]

            embed = discord.Embed(
                title = 'Welcome to Shteff!',
                description = 'Use /play to add more songs to queue.',
                color = current.color
            )

            embed.set_author(name = current.author.name)
            # TODO: add author icon_url to embed.set_author()

            embed.add_field(
                name = 'Currently playing:',
                value = current.name,
                inline = False
            )

            embed.add_field(
                name = 'Duration:',
                value = f'{current.timedelta_duration_to_str()}',
                inline = False
            )

            # TODO: maybe add release year inline with duration?

            embed.add_field(
                name = 'Track links:',
                value = f'[Spotify]({current.spotify_link})\n[YouTube]({current.yt_link})',
                inline = True
            )

            embed.add_field(
                name = 'Author links:',
                value = ''.join(author.print_with_url_format(new_line = True)
                                for author in current.authors),
                inline = True
            )

            embed.set_thumbnail(url = current.thumbnail_link)

        else:
            # set idle embed
            embed = discord.Embed(
                title = 'Welcome to Shteff!',
                description = 'Use /play to add more songs to queue.',
                color = 0xf1c40f
            )

        await self.command_message.edit(
            content = content,
            embed = embed,
            view = Buttons()
        )

    @staticmethod
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
                        replaced_info = await GuildBot.replace_command_channel(guild, channel_id)
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
                channel = await guild.create_text_channel('shteffs-disco')
                channel_id = channel.id

                with open('channel_ids.txt', 'a') as g:
                    g.write(f'{guild_id} {channel_id}\n')

                print(f'{c_time()} {c_event("CREATED CHANNEL")} {c_channel(channel_id)}')

            f.close()

            if replaced:
                GuildBot.replace("channel_ids.txt", pattern, subst)

            return channel_id

    @staticmethod
    async def replace_command_channel(guild: discord.guild.Guild, new_id: int) -> dict:
        """For a specified guild, replaces existing command channel id with new_id in channel_ids.txt."""
        channel = await guild.create_text_channel('shteffs-disco')
        channel_id = channel.id

        print(f'{c_time()} Command channel deleted, {c_event("CREATED CHANNEL")} {c_channel(channel_id)}')

        return {'pattern': f'{new_id}', 'subst': f'{channel_id}', 'id': channel_id}

    @staticmethod
    def replace(file_path: str, pattern: str, subst: str) -> None:
        """In a text file, replaces pattern with subst."""
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

    @staticmethod
    async def create_music_cog(bot, guild: discord.guild.Guild):
        """
        Creates a GuildBot object for guild with id guild_id.
        A GuildBot is only created by calling this function, not by directly declaring an instance.
        After creating the instance, __init_async__() is called, that contains async commands needed for initialization.
        """
        m_cog = GuildBot(bot, guild)
        await m_cog.__init_async__()
        return m_cog


class BtnStyle:
    grey = discord.ButtonStyle.grey
    green = discord.ButtonStyle.green
    red = discord.ButtonStyle.red
    link = discord.ButtonStyle.link


class Buttons(discord.ui.View):
    def __init__(self, timeout=180):
        super().__init__(timeout = timeout)

    @staticmethod
    def get_cog(interaction: discord.Interaction):
        """Returns GuildBot object whose Buttons were interacted with."""
        bot = GuildBot.bot
        return bot.music_cogs[interaction.guild.id]

    # first row

    @discord.ui.button(label = '⎇', style = BtnStyle.grey, row = 0)
    async def shuffle_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = Buttons.get_cog(interaction)
        await cog.shuffle()
        button.style = BtnStyle.green if cog.is_shuffled else BtnStyle.grey
        await interaction.response.edit_message(view = self)

    @discord.ui.button(label = '◁', style = BtnStyle.grey, row = 0)
    async def previous_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = Buttons.get_cog(interaction)
        await cog.previous()
        await interaction.response.edit_message(view = self)

    @discord.ui.button(label = '▉', style = BtnStyle.grey, row = 0)
    async def pause_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = Buttons.get_cog(interaction)
        cog.pause()
        button.style = BtnStyle.green if cog.is_paused else BtnStyle.grey
        button.label = '▶' if cog.is_paused else '▉'
        await interaction.response.edit_message(view = self)

    @discord.ui.button(label = '▷', style = BtnStyle.grey, row = 0)
    async def skip_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = Buttons.get_cog(interaction)
        await cog.skip()
        await interaction.response.edit_message(view = self)

    @discord.ui.button(label = '⭯', style = BtnStyle.grey, row = 0)
    async def loop_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = Buttons.get_cog(interaction)
        cog.loop()
        button.style = BtnStyle.green if cog.is_looped else BtnStyle.grey
        await interaction.response.edit_message(view = self)

    # second row

    @discord.ui.button(label = '✖', style = BtnStyle.red, row = 1)
    async def clear_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = Buttons.get_cog(interaction)
        await cog.clear()
        await interaction.response.edit_message(view = self)

    @discord.ui.button(label = '#', style = BtnStyle.red, row = 1)
    async def dc_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = Buttons.get_cog(interaction)
        await cog.dc()
        await interaction.response.edit_message(view = self)

    @discord.ui.button(label = '≡', style = BtnStyle.grey, row = 1, disabled = True)
    async def list_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.edit_message(view = self)

    @discord.ui.button(label = '⯆', style = BtnStyle.grey, row = 1)
    async def queue_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = Buttons.get_cog(interaction)
        await cog.queue()
        button.style = BtnStyle.green if cog.short_queue else BtnStyle.grey
        await interaction.response.edit_message(view = self)

    @discord.ui.button(label = '⯅', style = BtnStyle.grey, row = 1)
    async def history_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        cog = Buttons.get_cog(interaction)
        await cog.history()
        button.style = BtnStyle.green if cog.show_history else BtnStyle.grey
        await interaction.response.edit_message(view = self)
