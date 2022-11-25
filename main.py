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

import sys
import discord
from discord import app_commands
from discord.ext import commands

import cogs.guild_bot as mc
from cogs.anti_spam_cog import anti_spam_cog
from colors import *
from secrets import TOKEN
from checks import *
from exceptions import *


class MainBot(commands.AutoShardedBot):
    """
    This is the MainBot docstring, please finish it.
    """
    # TODO: docstring
    def __init__(self, intents=discord.Intents.all()):
        super().__init__(command_prefix = '!', intents = intents)
        self.music_cogs = {}

        # TODO: execute commands only if bot is in vc with bot
        @self.tree.command(name = 'play', description = 'Adds a song/list to queue.')
        @app_commands.describe(song = 'The name or link of song/list.')
        async def play(interaction: discord.Interaction, song: str) -> None:
            """If user calling the command is in a voice channel, adds wanted song/list to queue of that guild."""
            cog = self.music_cogs[interaction.guild.id]

            user_vc = interaction.user.voice
            bot_vc: int | None = cog.vc.channel.id if cog.vc else None

            # if user is not in a voice channel
            if user_vc is None:
                await interaction.response.send_message(
                    'Connect to a voice channel to play songs!',
                    ephemeral = True)
                return
            # if user is in a different voice channel than the bot
            elif bot_vc and user_vc.channel.id != bot_vc:
                await interaction.response.send_message(
                    'You are not in the same voice channel as the bot.',
                    ephemeral = True)
                return
            # if user is in a voice channel with the bot
            else:
                # TODO: send empty response
                await interaction.response.send_message('Adding song...', ephemeral = True)
                await cog.add_to_queue(song, user_vc.channel)

        @self.tree.command(name = 'skip', description = 'Skips currently playing song and plays next in queue.')
        async def skip(interaction: discord.Interaction):
            """Skips to next song in queue."""
            try:
                guild_bot = self.music_cogs[interaction.guild.id]
                await self.run_if_user_with_bot(interaction, guild_bot, guild_bot.skip)
            except InteractionFailedError:
                pass
            else:
                await interaction.response.send_message('Skipped song.', ephemeral = True)

        @self.tree.command(name = 'loop', description = 'Loops music queue or single song.')
        async def loop(interaction: discord.Interaction):
            """Loops the following queue including the current song (but not the history)."""
            try:
                guild_bot = self.music_cogs[interaction.guild.id]
                await self.run_if_user_with_bot(interaction, guild_bot, guild_bot.loop)
            except InteractionFailedError:
                pass
            else:
                await interaction.response.send_message('Toggled loop.', ephemeral = True)

        @self.tree.command(name = 'clear', description = 'Clears music queue and history, stops playing.')
        async def clear(interaction: discord.Interaction):
            """Loops the current song."""
            try:
                guild_bot = self.music_cogs[interaction.guild.id]
                await self.run_if_user_with_bot(interaction, guild_bot, guild_bot.clear)
            except InteractionFailedError:
                pass
            else:
                await interaction.response.send_message('Queue cleared.', ephemeral = True)

        @self.tree.command(name = 'dc', description = 'Disconnects bot from voice channel.')
        async def dc(interaction: discord.Interaction):
            """Disconnects bot from voice channel."""
            try:
                guild_bot = self.music_cogs[interaction.guild.id]
                await self.run_if_user_with_bot(interaction, guild_bot, guild_bot.dc)
            except InteractionFailedError:
                pass
            else:
                await interaction.response.send_message('Bot disconnected.', ephemeral = True)

        @self.tree.command(name = 'previous', description = 'Skips current song and plays previous.')
        async def previous(interaction: discord.Interaction):
            """Skips current song and plays first song in history, i.e. previous song."""
            try:
                guild_bot = self.music_cogs[interaction.guild.id]
                await self.run_if_user_with_bot(interaction, guild_bot, guild_bot.previous)
            except InteractionFailedError:
                pass
            else:
                await interaction.response.send_message('Went to previous song.', ephemeral = True)

        @self.tree.command(name = 'queue', description = 'Toggles queue display type (short/long).')
        async def queue(interaction: discord.Interaction):
            """Swaps queue display type. (short/long)"""
            try:
                guild_bot = self.music_cogs[interaction.guild.id]
                await self.run_if_user_with_bot(interaction, guild_bot, guild_bot.queue)
            except InteractionFailedError:
                pass
            else:
                await interaction.response.send_message('Queue display toggled.', ephemeral = True)

        @self.tree.command(name = 'history', description = 'Toggles history display type (show/hide).')
        async def history(interaction: discord.Interaction):
            """Swaps history display type. (show/hide)."""
            try:
                guild_bot = self.music_cogs[interaction.guild.id]
                await self.run_if_user_with_bot(interaction, guild_bot, guild_bot.history)
            except InteractionFailedError:
                pass
            else:
                await interaction.response.send_message('History display toggled.', ephemeral = True)

        @self.tree.command(name = 'shuffle', description = 'Toggles queue shuffle.')
        async def shuffle(interaction: discord.Interaction):
            """Shuffles music queue."""
            try:
                guild_bot = self.music_cogs[interaction.guild.id]
                await self.run_if_user_with_bot(interaction, guild_bot, guild_bot.shuffle)
            except InteractionFailedError:
                pass
            else:
                await interaction.response.send_message('Shuffle toggled.', ephemeral = True)

        @self.tree.command(name = 'swap', description = 'Swap places of two queued songs.')
        @app_commands.describe(song1 = 'Place of first song in queue.', song2 = 'Place of second song in the queue.')
        async def swap(interaction: discord.Interaction, song1: int, song2: int) -> None:
            """
            Swaps places of two songs in the queue.
            Numbering of arguments starts with 1, 0 refers to the currently playing song.
            Indexes starting with 0 are passed to swap method of music cog.
            """
            # indexes must be greater than 0
            if song1 <= 0 or song2 <= 0:
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

            # checking if inputs are valid numbers
            # inputs are valid if both exist in queue
            cog = self.music_cogs[interaction.guild.id]
            queue_len = cog.get_queue_len()

            if song1 > queue_len or song2 > queue_len:
                await interaction.response.send_message(
                    'Specified indexes not in queue.',
                    ephemeral = True)
                return

            # swap if guard clauses passed
            await cog.swap(song1, song2)

        @self.tree.command(name = 'pause', description = 'Pauses or unpauses playing.')
        async def pause(interaction: discord.Interaction):
            """
            Pauses if playing, unpauses if paused.
            """
            try:
                guild_bot = self.music_cogs[interaction.guild.id]
                await self.run_if_user_with_bot(interaction, guild_bot, guild_bot.pause)
            except InteractionFailedError:
                pass
            else:
                await interaction.response.send_message('Player paused.', ephemeral = True)

    async def on_guild_join(self, guild) -> None:
        # TODO: test
        """Creates GuildBot if bot joins a guild while running."""
        await self.add_guild(guild)

    async def on_ready(self):
        """
        Runs on bot login.
        Syncs slash commands.
        Creates GuildBot objects for every guild.
        """
        # TODO: print copyright license text to stdout
        # sync commands
        print(f'{c_time()} {c_event("SYNCING COMMANDS")}')
        try:
            synced = await self.tree.sync()
            print(f'{c_time()} {c_event("SYNCED")} {len(synced)} command(s)')
        except Exception as e:
            print(f'{c_time()} {c_err()} failed to sync command(s), {c_event("EXITING")}, Exception:\n{e}')
            sys.exit()

        self.remove_command('help')
        await self.add_cog(anti_spam_cog(self))

        # create music cog for every guild bot is in
        for guild in self.guilds:
            self.music_cogs[guild.id] = await self.add_guild(guild)

        print(f'\n{c_time()} {c_login()} as {self.user}\nBot user id: {c_user(self.user.id)}\n')

    async def add_guild(self, guild: discord.guild.Guild) -> object:
        """Creates a GuildBot object for specific guild."""
        m_cog = await mc.GuildBot.create_music_cog(bot = self, guild = guild)
        print(f'{c_time()} {c_event("ADDED GUILD")} {c_guild(guild.id)} with channel {c_channel(m_cog.bot_channel_id)}')
        return m_cog

    @staticmethod
    async def run_if_user_with_bot(interaction, guild_bot, func):
        # TODO: docstring
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

        await func()


if __name__ == '__main__':
    """Main is the beginning of everything."""
    print(
        """
Shteff  Copyright (C) 2022 Mjolnir2425, OvajStup
This program comes with ABSOLUTELY NO WARRANTY.
This is free software, and you are welcome to redistribute it.
"""
    )
    MainBot().run(TOKEN)
