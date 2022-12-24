"""
Shteff  Copyright (C) 2022 Mjolnir2425, OvajStup

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

# last changed 24/12/22
# changed 'Adding song...' to 'Adding song(s)...'
# changed some command descriptions and names
# added a comment about the structure of a command function
# changed formatting from one blank line between functions to two
# typehints on voice channel objects
# todo: check requirements.txt

import sys

import discord
from discord import app_commands
from discord.ext import commands

from components.guild_bot import GuildBot
from components.anti_spam_cog import anti_spam_cog
from colors import *
from secrets import TOKEN
from checks import user_with_bot_check
from exceptions import (
    InteractionFailedError,
    UserNotInVCError,
    BotNotInVCError,
    DifferentChannelsError
)


class MainBot(commands.AutoShardedBot):
    """
    This is the MainBot docstring, please finish it.
    """
    # TODO: docstring
    def __init__(self, intents=discord.Intents.all()):
        super().__init__(command_prefix = '!', intents = intents)
        self.guild_bots = {}

        @self.tree.command(name = 'play', description = 'Adds a song/list to queue.')
        @app_commands.describe(song = 'The name or link of song/list.')
        async def play(interaction: discord.Interaction, song: str) -> None:
            # todo: add optional insert argument that would add the song to the specified place in queue
            """If user calling the command is in a voice channel, adds wanted song/list to queue of that guild."""
            guild_bot = self.guild_bots[interaction.guild.id]

            user_voice_state: discord.VoiceState | None = interaction.user.voice
            bot_vc_id: int | None = guild_bot.voice_client.channel.id if guild_bot.voice_client is not None else None

            # if user is not in a voice channel
            if user_voice_state is None:
                await interaction.response.send_message(
                    'Connect to a voice channel to play songs!',
                    ephemeral = True)
                return
            # if user is in a different voice channel than the bot
            elif bot_vc_id and user_voice_state.channel.id != bot_vc_id:
                await interaction.response.send_message(
                    'You are not in the same voice channel as the bot.',
                    ephemeral = True)
                return
            # if user is in a voice channel with the bot
            else:
                # TODO: send empty response
                await interaction.response.send_message('Adding song(s)...', ephemeral = True)

                command = guild_bot.queue_command
                args = song, user_voice_state.channel
                # todo: use guild_bot.queue_command(...)
                # await guild_bot.queue_command(command, song, user_voice_state)
                await guild_bot.add_to_queue(song, user_voice_state.channel)

        # todo: command names and descriptions

        # the structure of most commands is the same
        # we get the guild_bot that the command should be executed in
        # then we run the command if user is in a voice channel with the bot
        # if the command is executed successfully, a confirmation message is sent
        # if the command fails to execute, nothing is done
        # because a message has already been sent from the
        # run_if_user_with_bot function

        @self.tree.command(name = 'skip', description = 'Skips to the next queued song.')
        async def skip(interaction: discord.Interaction) -> None:
            """Skips to next song in queue."""
            guild_bot = self.guild_bots[interaction.guild.id]
            try:
                await self.run_if_user_with_bot(interaction, guild_bot, guild_bot.skip)
            except InteractionFailedError:
                pass
            else:
                await interaction.response.send_message('Skipped song.', ephemeral = True)


        @self.tree.command(name = 'loop', description = 'Loops queue or single song.')
        async def loop(interaction: discord.Interaction) -> None:
            """Loops the following queue including the current song (but not the history)."""
            guild_bot = self.guild_bots[interaction.guild.id]
            try:
                await self.run_if_user_with_bot(interaction, guild_bot, guild_bot.loop)
            except InteractionFailedError:
                pass
            else:
                await interaction.response.send_message('Toggled loop.', ephemeral = True)


        @self.tree.command(name = 'clear', description = 'Clears queue and history, stops playing.')
        async def clear(interaction: discord.Interaction) -> None:
            """Loops the current song."""
            guild_bot = self.guild_bots[interaction.guild.id]
            try:
                await self.run_if_user_with_bot(interaction, guild_bot, guild_bot.clear)
            except InteractionFailedError:
                pass
            else:
                await interaction.response.send_message('Queue cleared.', ephemeral = True)


        @self.tree.command(name = 'dc', description = 'Disconnects bot from voice channel.')
        async def disconnect(interaction: discord.Interaction) -> None:
            """Disconnects bot from voice channel."""
            guild_bot = self.guild_bots[interaction.guild.id]
            try:
                await self.run_if_user_with_bot(interaction, guild_bot, guild_bot.dc)
            except InteractionFailedError:
                pass
            else:
                await interaction.response.send_message('Bot disconnected.', ephemeral = True)


        @self.tree.command(name = 'previous', description = 'Skips current song and plays previous.')
        async def previous(interaction: discord.Interaction) -> None:
            """Skips current song and plays first song in history, i.e. previous song."""
            guild_bot = self.guild_bots[interaction.guild.id]
            try:
                await self.run_if_user_with_bot(interaction, guild_bot, guild_bot.previous)
            except InteractionFailedError:
                pass
            else:
                await interaction.response.send_message('Went to previous song.', ephemeral = True)


        @self.tree.command(name = 'queue', description = 'Toggles queue display type (short/long).')
        async def queue(interaction: discord.Interaction) -> None:
            # todo: see how this behaves when ui button behaviour is changed
            """Swaps queue display type. (short/long)"""
            guild_bot = self.guild_bots[interaction.guild.id]
            try:
                await self.run_if_user_with_bot(interaction, guild_bot, guild_bot.toggle_queue)
            except InteractionFailedError:
                pass
            else:
                await interaction.response.send_message('Queue display toggled.', ephemeral = True)


        @self.tree.command(name = 'history', description = 'Toggles history display type (show/hide).')
        async def history(interaction: discord.Interaction) -> None:
            # todo: see how this behaves when ui button behaviour is changed
            """Swaps history display type. (show/hide)."""
            guild_bot = self.guild_bots[interaction.guild.id]
            try:
                await self.run_if_user_with_bot(interaction, guild_bot, guild_bot.toggle_history)
            except InteractionFailedError:
                pass
            else:
                await interaction.response.send_message('History display toggled.', ephemeral = True)


        @self.tree.command(name = 'toggle_lyrics', description = 'Toggles lyrics display (show/hide).')
        async def lyrics(interaction: discord.Interaction) -> None:
            """Swaps history display type. (show/hide)."""
            guild_bot = self.guild_bots[interaction.guild.id]
            try:
                await self.run_if_user_with_bot(interaction, guild_bot, guild_bot.toggle_lyrics)
            except InteractionFailedError:
                pass
            else:
                await interaction.response.send_message('Lyrics display toggled.', ephemeral = True)


        @self.tree.command(name = 'shuffle', description = 'Toggles queue shuffle.')
        async def shuffle(interaction: discord.Interaction):
            """Shuffles music queue."""
            guild_bot = self.guild_bots[interaction.guild.id]
            try:
                await self.run_if_user_with_bot(interaction, guild_bot, guild_bot.shuffle)
            except InteractionFailedError:
                pass
            else:
                await interaction.response.send_message('Shuffle toggled.', ephemeral = True)


        @self.tree.command(name = 'swap', description = 'Swap places of queued songs.')
        @app_commands.describe(song1 = 'Place of first song in queue.', song2 = 'Place of second song in the queue.')
        async def swap(interaction: discord.Interaction, song1: int, song2: int) -> None:
            """
            Swaps places of two songs in the queue.
            Numbering of arguments starts with 1, 0 refers to the currently playing song.
            Indexes starting with 0 are passed to swap method of music guild_bot.
            """
            # indexes must be greater than 0
            if song1 <= 0 or song2 <= 0:
                # todo: what if it could be <= 0?
                # todo: i.e. bring a song back from history
                await interaction.response.send_message(
                    'Queue index cannot be less than or equal to 0.',
                    ephemeral = True)
                return
            # swapping only if different indexes selected
            if song1 == song2:
                await interaction.response.send_message(
                    'Queue indexes must be different.',
                    ephemeral = True)
                return

            # todo: check this when executing command
            # checking if inputs are valid numbers
            # inputs are valid if both exist in queue
            guild_bot = self.guild_bots[interaction.guild.id]
            queue_len = len(guild_bot.queue[guild_bot.p_index + 1:])

            if song1 > queue_len or song2 > queue_len:
                await interaction.response.send_message(
                    'Specified indexes not in queue.',
                    ephemeral = True)
                return

            try:
                await self.run_if_user_with_bot(interaction, guild_bot, guild_bot.swap, song1, song2)
            except InteractionFailedError:
                pass
            # todo: add CommandExecutionError
            else:
                await interaction.response.send_message('Songs swapped.', ephemeral = True)


        @self.tree.command(name = 'pause', description = 'Pauses or unpauses playing.')
        async def pause(interaction: discord.Interaction) -> None:
            """
            Pauses if playing, unpauses if paused.
            """
            guild_bot = self.guild_bots[interaction.guild.id]
            try:
                await self.run_if_user_with_bot(interaction, guild_bot, guild_bot.pause)
            except InteractionFailedError:
                pass
            else:
                await interaction.response.send_message('Player paused.', ephemeral = True)


    @staticmethod
    async def run_if_user_with_bot(interaction, guild_bot, func, *args) -> None:
        # todo: docstring
        # todo: check if guild_bot command or player command maybe?
        # todo: this is broken lol
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

        await guild_bot.queue_command(func, *args)


    async def on_guild_join(self, guild) -> None:
        # TODO: test, probably doesn't work
        """Creates GuildBot if bot joins a guild while running."""
        await self.add_guild(guild)


    async def add_guild(self, guild: discord.guild.Guild) -> GuildBot:
        """Creates a GuildBot object for specific guild."""
        guild_bot = await GuildBot.create_guild_bot(bot = self, guild = guild)
        print(f'{c_event("ADDED GUILD")} {c_guild(guild.id)} with channel {c_channel(guild_bot.bot_channel_id)}')
        return guild_bot


    async def on_ready(self) -> None:
        """
        Runs on bot login.
        Syncs slash commands.
        Creates GuildBot objects for every guild.
        """
        # sync commands
        print(f'{c_event("SYNCING COMMANDS")}')
        try:
            synced = await self.tree.sync()
            print(f'{c_event("SYNCED")} {len(synced)} command(s)')
        except Exception as e:
            print(f'{c_err()} failed to sync command(s), {c_event("EXITING")}, Exception:\n{e}')
            sys.exit()

        self.remove_command('help')
        await self.add_cog(anti_spam_cog(self))

        # create music cog for every guild bot is in
        for guild in self.guilds:
            self.guild_bots[guild.id] = await self.add_guild(guild)

        print(f'{c_login()} as {self.user} with user id: {c_user(self.user.id)}')


if __name__ == '__main__':
    """Main is the beginning of everything."""
    print(
        """
Shteff  Copyright (C) 2022 Mjolnir2425, OvajStup
This program comes with ABSOLUTELY NO WARRANTY.
This is free software, and you are welcome to redistribute it.
"""
    )
    bot = MainBot()
    bot.run(TOKEN)
