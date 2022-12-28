"""
This file is part of Shteff which is released under the GNU General Public License v3.0.
See file LICENSE or go to <https://www.gnu.org/licenses/gpl-3.0.html> for full license details.
"""

# last changed 26/12/22
# changed how `GuildBot.__init__()` works
# moved `__init_async__` to `__init__`
# removed `GuildBot.create()` method

from os import fdopen, remove
from shutil import move, copymode
from tempfile import mkstemp
from asyncinit import asyncinit

import discord

from colors import *
from components.player import Player
from checks import user_with_bot_check
from exceptions import (
    InteractionFailedError,
    UserNotInVCError,
    BotNotInVCError,
    DifferentChannelsError
)


# noinspection PyAttributeOutsideInit
@asyncinit
class GuildBot(Player):
    # TODO: write docstring
    """
    docstring
    """

    bot = None

    default_color = 0xf1c40f
    default_embed = discord.Embed(
        title = 'Welcome to Shteff!',
        description = 'Use /play to add more songs to queue.',
        color = default_color
    )

    async def _async_init_(self, guild: discord.guild.Guild):
    # async def __init__(self, guild: discord.guild.Guild):
        # initialize player for specified guild
        super().__init__(self, guild)
        self.guild: discord.guild.Guild = guild

        # set up message objects
        self.command_message: discord.Message | None = None
        self.lyrics_message:  discord.Message | None = None

        # set default flags
        self.show_lyrics  = False
        self.short_queue  = False
        self.show_history = False

        # set up command channel
        self.command_channel_id: int              = await self.get_id(self.guild)
        self.command_channel: discord.TextChannel = self.bot.get_channel(self.command_channel_id)
        # create a new live message
        await self.create_live_msg()

    __init__ = _async_init_

        # todo: make queue display toggling a single button
        # todo: should behave like loop does

    async def create_live_msg(self):
        # clear command channel
        await self.command_channel.purge(limit = 10)
        # start a new live message
        self.command_message = await self.command_channel.send(embed = self.default_embed, view = Buttons())
        # update message
        await self.update_msg()


    def reset_flags(self) -> None:
        self.show_lyrics  = False
        self.short_queue  = False
        self.show_history = False


    async def update_msg(self) -> None:
        """
        Refreshes the command message to display the current bot states, lists, and playing status.

        The message will show the history of songs that have already been played, and the current queue of
        songs that are waiting to be played. If the bot is currently playing or paused, the message will also
        include an embed with information about the current song.

        The history section of the message will display the most recent songs played, up to the current song.
        The queue section of the message will display the upcoming songs in the order that they will be played.
        If the `short_queue` flag is set, only the next five songs in the queue will be shown. If there are
        more songs in the queue than are shown, a message will be included indicating the number of additional
        songs that are not shown.

        The embed will include the title, artist, and duration of the current song, as well as a progress bar
        showing the current position in the song. The embed will also use the color of the current song for
        its background.
        """
        # message content
        # todo: make history display a 50/50 split between history and queue
        # todo: maybe add a mode where songs are shown in order and the current song is bold
        # todo: if that is made, make list showing buttons a single button that loops through possible display modes
        # todo: adjust docstring when behaviour changed
        # todo: adjust docstring after lyrics moved to separate message
        # TODO: show playing progress bar
        content = ''

        if self.show_history:
            history = self.queue[:self.p_index]
            history.reverse()

            if history:
                content += '**History:**\n'

                for i, song in enumerate(history):
                    content += f'**{i + 1}** {song.to_msg_format()}\n'

                if self.queue[self.p_index + 1:]:
                    content += '\n'

        if self.queue[self.p_index + 1:]:
            i = self.p_index + 1
            added = 0
            content_len = 0

            song_strs: list[str] = []

            # God save me
            while i < len(self.queue) and content_len < 1800:
                if self.short_queue and i - self.p_index >= 5:
                    break
                song = self.queue[i]
                to_add = f'**{i - self.p_index}** {song.to_msg_format()}\n'
                song_strs.append(to_add)
                content_len += len(to_add)
                added += 1
                i += 1

            content += '**Queue:**\n'
            not_shown = len(self.queue[self.p_index + 1:]) - added
            if not_shown:
                content += f'And **{not_shown}** more...\n\n'
            content += ''.join(song_strs[::-1])

        if self.queue[self.p_index:] and self.is_playing or self.is_paused:
            current = self.queue[self.p_index]

            # create embed
            if current.color:
                color = discord.Color.from_rgb(*current.color)
            else:
                color = self.default_color

            embed = discord.Embed(
                title = 'Welcome to Shteff!',
                description = 'Use /play to add more songs to queue.',
                color = color
            )

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

            embed.add_field(
                name = 'Track links:',
                value = f'[Spotify]({current.spotify_link})\n[YouTube]({current.yt_link})',
                inline = True
            )

            embed.add_field(
                name = 'Author links:',
                value = ''.join(author.print_with_url_format(new_line = True) for author in current.authors),
                inline = True
            )

            if current.thumbnail_link is not None:
                embed.set_thumbnail(url = current.thumbnail_link)

            embed.set_footer(text = 'We do not guarantee the accuracy of the data provided.')

            # set lyrics message
            if self.show_lyrics:
                # todo: lyrics button returns to grey when queue cleared but works as expected
                lyrics_msg_content = f'**Lyrics:\n\n**{current.lyrics}\n\n'
                if self.lyrics_message is None:
                    if len(lyrics_msg_content) > 1900:
                        lyrics_msg_content = lyrics_msg_content[:1900]
                        lyrics_msg_content += '\n*Only the first 2000 characters of the lyrics can be displayed.*\n'
                    lyrics_msg_content += '*Lyrics provided by Genius.*'

                    self.lyrics_message = await self.command_channel.send(content = lyrics_msg_content)
                else:
                    await self.lyrics_message.edit(content = lyrics_msg_content)

        else:
            # set idle embed
            embed = self.default_embed
            embed.set_footer(text = '')
            await self.delete_lyrics_message()

        try:
            # edit message with generated elements
            await self.command_message.edit(
                content = content,
                embed = embed,
                view = Buttons()
            )
        except discord.errors.NotFound:
            # create a new message if last one was deleted
            await self.create_live_msg()


    async def toggle_queue(self) -> None:
        # todo: function call needs to be added to command queue
        self.short_queue = not self.short_queue
        await self.guild_bot.update_msg()


    async def toggle_history(self) -> None:
        # todo: function call needs to be added to command queue
        if self.show_history:
            self.show_history = False
            if self.was_long_queue:
                self.short_queue = False

        else:
            self.show_history = True
            if not self.short_queue:
                self.was_long_queue = True
                self.short_queue = True

        await self.guild_bot.update_msg()


    async def toggle_lyrics(self):
        # todo: function call needs to be added to command queue
        if self.show_lyrics:
            self.show_lyrics = False
            await self.delete_lyrics_message()
        else:
            self.show_lyrics = True
        await self.update_msg()


    async def delete_lyrics_message(self) -> None:
        if self.lyrics_message is None:
            return

        await self.lyrics_message.delete()
        self.lyrics_message = None


    @staticmethod
    async def get_id(guild: discord.guild.Guild) -> int:
        """
        Retrieves the ID of the command channel for the given guild.

        If a command channel has previously been set for the guild, the ID of that channel will
        be returned. If no command channel has been set, a new text channel will be created for the
        guild and the ID of the new channel will be returned.

        If the previously set command channel no longer exists in the guild, a new channel will
        be created and the ID of the new channel will be returned. The ID of the old channel will be
        replaced with the ID of the new channel in the database.

        Parameters:
        guild (discord.guild.Guild): The guild for which to retrieve the command channel ID.

        Returns:
        int: The ID of the command channel for the given guild.
        """
        replaced = False
        guild_id = guild.id

        with open('channel_ids.txt') as f:
            for line in f:
                # every line is a pair of '{guild id} {channel id}'
                r = line.split()
                if int(r[0]) == guild_id:
                    channel_id = int(r[1])
                    # check if channel doesn't exist currently
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
                # add new channel to database
                with open('channel_ids.txt', 'a') as g:
                    g.write(f'{guild_id} {channel_id}\n')
                print(f'{c_event("CREATED CHANNEL")} {c_channel(channel_id)}')
            f.close()

            if replaced:
                GuildBot.replace("channel_ids.txt", pattern, subst)

            return channel_id


    @staticmethod
    async def replace_command_channel(guild: discord.guild.Guild, new_id: int) -> dict:
        """
        Creates a new command channel for the given guild and returns information about the replacement.

        If the previously set command channel for the guild no longer exists, this method creates a new
        text channel for the guild and returns a dictionary with the ID of the new channel, the pattern to
        search for in the database, and the substitution to make.

        Parameters:
        guild (discord.guild.Guild): The guild for which to create a new command channel.
        new_id (int): The ID of the old command channel that has been deleted.

        Returns:
        dict: A dictionary containing the ID of the new command channel, the pattern to search for
            in the database, and the substitution to make.
        """
        channel = await guild.create_text_channel('shteffs-disco')
        channel_id = channel.id

        print(f'{c_event("CREATED CHANNEL")} {c_channel(channel_id)}, previous command channel deleted')

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


class BtnStyle:
    grey  = discord.ButtonStyle.grey
    green = discord.ButtonStyle.green
    red   = discord.ButtonStyle.red
    link  = discord.ButtonStyle.link


class Buttons(discord.ui.View):
    # todo: docstring
    # todo: move to another file maybe?
    def __init__(self, timeout=180):
        super().__init__(timeout = timeout)


    @staticmethod
    def get_bot(interaction: discord.Interaction):
        """Returns GuildBot object whose Buttons were interacted with."""
        return GuildBot.bot.guild_bots[interaction.guild.id]


    @staticmethod
    async def run_if_user_with_bot(interaction, guild_bot, func, command_type='player', *args) -> None:
        # todo: copy docstring from main
        # todo: check if guild_bot command or player command
        try:
            user_with_bot_check(interaction, guild_bot)

        except UserNotInVCError:
            await interaction.response.send_message(
                'Connect to a voice channel to use this command.',
                ephemeral = True
            )
            raise InteractionFailedError()

        except BotNotInVCError:
            await interaction.response.send_message(
                'Bot has to be with you in a voice channel to use this command.',
                ephemeral = True
            )
            raise InteractionFailedError()

        except DifferentChannelsError:
            await interaction.response.send_message(
                'You and the bot are in different voice channels, move to use this command.',
                ephemeral = True
            )
            raise InteractionFailedError()

        if command_type == 'player':
            await guild_bot.queue_command(func, *args)
        elif command_type == 'guild_bot':
            await func()

    # first row
    # todo: add try-except blocks like it is in main
    # todo: make player commands work as expected
    # todo: some wierd error with discord.ui.view when skipping?

    @discord.ui.button(label = '⎇', style = BtnStyle.grey, row = 0)
    async def shuffle_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild_bot = self.get_bot(interaction)
        await guild_bot.shuffle()
        button.style = BtnStyle.green if guild_bot.is_shuffled else BtnStyle.grey
        await interaction.response.edit_message(view = self)


    @discord.ui.button(label = '◁', style = BtnStyle.grey, row = 0)
    async def previous_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild_bot = self.get_bot(interaction)
        await guild_bot.previous()
        await interaction.response.edit_message(view = self)


    @discord.ui.button(label = '▉', style = BtnStyle.grey, row = 0)
    async def pause_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild_bot = self.get_bot(interaction)
        await guild_bot.pause()
        button.style = BtnStyle.green if guild_bot.is_paused else BtnStyle.grey
        button.label = '▶' if guild_bot.is_paused else '▉'
        await interaction.response.edit_message(view = self)


    @discord.ui.button(label = '▷', style = BtnStyle.grey, row = 0)
    async def skip_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild_bot = self.get_bot(interaction)
        await guild_bot.skip()
        # todo: what does the line below actually do?
        # todo: why the error???
        await interaction.response.edit_message(view = self)


    @discord.ui.button(label = '⭯', style = BtnStyle.grey, row = 0)
    async def loop_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild_bot = self.get_bot(interaction)
        await guild_bot.loop()
        button.style = BtnStyle.green if guild_bot.is_looped else BtnStyle.grey
        await interaction.response.edit_message(view = self)

    # second row

    @discord.ui.button(label = '✖', style = BtnStyle.red, row = 1)
    async def clear_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild_bot = self.get_bot(interaction)
        await guild_bot.clear()
        await interaction.response.edit_message(view = self)


    @discord.ui.button(label = '#', style = BtnStyle.red, row = 1)
    async def dc_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild_bot = self.get_bot(interaction)
        await guild_bot.dc()
        await interaction.response.edit_message(view = self)


    @discord.ui.button(label = '≡', style = BtnStyle.grey, row = 1)
    async def lyrics_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild_bot = self.get_bot(interaction)
        button.style = BtnStyle.green if guild_bot.show_lyrics else BtnStyle.grey

        try:
            await self.run_if_user_with_bot(interaction, guild_bot, guild_bot.toggle_lyrics, 'guild_bot')
        except InteractionFailedError:
            pass
        else:
            button.style = BtnStyle.green if guild_bot.show_lyrics else BtnStyle.grey
            await interaction.response.edit_message(view = self)


    @discord.ui.button(label = '⯆', style = BtnStyle.grey, row = 1)
    async def queue_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild_bot = self.get_bot(interaction)
        button.style = BtnStyle.green if guild_bot.short_queue else BtnStyle.grey

        try:
            await self.run_if_user_with_bot(interaction, guild_bot, guild_bot.toggle_queue, 'guild_bot')
        except InteractionFailedError:
            pass
        else:
            button.style = BtnStyle.green if guild_bot.short_queue else BtnStyle.grey
            await interaction.response.edit_message(view = self)


    @discord.ui.button(label = '⯅', style = BtnStyle.grey, row = 1)
    async def history_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild_bot = self.get_bot(interaction)
        button.style = BtnStyle.green if guild_bot.show_history else BtnStyle.grey

        try:
            await self.run_if_user_with_bot(interaction, guild_bot, guild_bot.toggle_history, 'guild_bot')
        except InteractionFailedError:
            pass
        else:
            button.style = BtnStyle.green if guild_bot.show_history else BtnStyle.grey
            await interaction.response.edit_message(view = self)
