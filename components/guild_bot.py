"""
This file is part of Shteff which is released under the GNU General Public License v3.0.
See file LICENSE or go to <https://www.gnu.org/licenses/gpl-3.0.html> for full license details.
"""

# last changed 23/12/22
# update_msg now takes color in (r, g, b) format, instead of discord
# changed formatting from one blank line between functions to two
# set default color as class variable

from os import fdopen, remove
from shutil import move, copymode
from tempfile import mkstemp

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


class GuildBot(Player):
    # TODO: write docstring
    """
    docstring
    """
    # MainBot instance GuildBot instance is in
    bot = None
    default_color = 0xf1c40f


    def __init__(self, bot, guild: discord.guild.Guild):
        super().__init__(self, guild)
        GuildBot.bot = bot
        self.guild: discord.guild.Guild = guild

        # id of command message
        self.command_message: discord.Message | None = None

        self.show_lyrics = False
        self.short_queue = False
        self.show_history = False

        # todo: make queue display toggling a single button
        # todo: should behave like loop does
        # todo: show a couple of verses at a time, move with arrows


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


    def reset_bot_states(self) -> None:
        super().reset_bot_states()
        self.show_lyrics = False
        self.short_queue = False
        self.show_history = False


    async def update_msg(self) -> None:
        # TODO: finish docstring
        """Refreshes command message according to current bot states, lists and playing status."""
        # message content
        # todo: make history display a 50/50 split between history and queue
        # todo: maybe add a mode where songs are shown in order and the current song is bold
        # todo: if that is made, make list showing buttons a single button that loops through possible display modes
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
            while i < len(self.queue) and content_len < 1500:
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

        # embed

        if self.queue[self.p_index:] and self.is_playing or self.is_paused:
            current = self.queue[self.p_index]

            embed = discord.Embed(
                title = 'Welcome to Shteff!',
                description = 'Use /play to add more songs to queue.',
                color = discord.Color.from_rgb(*current.color)
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

            if self.show_lyrics:
                embed.add_field(
                    name = 'Lyrics',
                    value = current.lyrics[:1024],
                    inline = False
                )

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

            embed.set_footer(text = 'We do not guarantee the accuracy of the data provided.')

        else:
            # set idle embed
            embed = discord.Embed(
                title = 'Welcome to Shteff!',
                description = 'Use /play to add more songs to queue.',
                color = self.default_color
            )
            embed.set_footer(text = '')

        # edit message with generated elements
        await self.command_message.edit(
            content = content,
            embed = embed,
            view = Buttons()
        )


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
        else:
            self.show_lyrics = True
            current = self.queue[self.p_index]
            current.set_lyrics()
        await self.update_msg()


    @staticmethod
    async def get_id(guild: discord.guild.Guild) -> int:
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
        """For a specified guild, replaces existing command channel id with new_id in channel_ids.txt."""
        channel = await guild.create_text_channel('shteffs-disco')
        channel_id = channel.id

        print(f'Command channel deleted, {c_event("CREATED CHANNEL")} {c_channel(channel_id)}')

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
    async def create_guild_bot(bot, guild: discord.guild.Guild):
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
    def get_bot(interaction: discord.Interaction):
        """Returns GuildBot object whose Buttons were interacted with."""
        bot = GuildBot.bot
        return bot.guild_bots[interaction.guild.id]


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
        cog = Buttons.get_bot(interaction)
        await cog.shuffle()
        button.style = BtnStyle.green if cog.is_shuffled else BtnStyle.grey
        await interaction.response.edit_message(view = self)


    @discord.ui.button(label = '◁', style = BtnStyle.grey, row = 0)
    async def previous_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild_bot = Buttons.get_bot(interaction)
        await guild_bot.previous()
        await interaction.response.edit_message(view = self)


    @discord.ui.button(label = '▉', style = BtnStyle.grey, row = 0)
    async def pause_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild_bot = Buttons.get_bot(interaction)
        await guild_bot.pause()
        button.style = BtnStyle.green if guild_bot.is_paused else BtnStyle.grey
        button.label = '▶' if guild_bot.is_paused else '▉'
        await interaction.response.edit_message(view = self)


    @discord.ui.button(label = '▷', style = BtnStyle.grey, row = 0)
    async def skip_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild_bot = Buttons.get_bot(interaction)
        await guild_bot.skip()
        await interaction.response.edit_message(view = self)


    @discord.ui.button(label = '⭯', style = BtnStyle.grey, row = 0)
    async def loop_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild_bot = Buttons.get_bot(interaction)
        await guild_bot.loop()
        button.style = BtnStyle.green if guild_bot.is_looped else BtnStyle.grey
        await interaction.response.edit_message(view = self)

    # second row

    @discord.ui.button(label = '✖', style = BtnStyle.red, row = 1)
    async def clear_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild_bot = Buttons.get_bot(interaction)
        await guild_bot.clear()
        await interaction.response.edit_message(view = self)


    @discord.ui.button(label = '#', style = BtnStyle.red, row = 1)
    async def dc_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild_bot = Buttons.get_bot(interaction)
        await guild_bot.dc()
        await interaction.response.edit_message(view = self)


    @discord.ui.button(label = '≡', style = BtnStyle.grey, row = 1)
    async def lyrics_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild_bot = Buttons.get_bot(interaction)
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
        guild_bot = Buttons.get_bot(interaction)
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
        guild_bot = Buttons.get_bot(interaction)
        button.style = BtnStyle.green if guild_bot.show_history else BtnStyle.grey

        try:
            await self.run_if_user_with_bot(interaction, guild_bot, guild_bot.toggle_history, 'guild_bot')
        except InteractionFailedError:
            pass
        else:
            button.style = BtnStyle.green if guild_bot.show_history else BtnStyle.grey
            await interaction.response.edit_message(view = self)
