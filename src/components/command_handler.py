import discord

from utils.exceptions import CommandExecutionError
from utils.checks import user_with_bot_check

from utils import (
    CommandExecutionError,
    user_with_bot_check
)


# noinspection PyBroadException
class CommandHandler:
    def __init__(self, main_bot):
        self.bot = main_bot


    @staticmethod
    async def handle_interaction_error(interaction, exception):
        match type(exception).__name__:
            case 'UserNotInVCError':
                await interaction.response.send_message(
                    'Connect to a voice channel to use this command.',
                    ephemeral = True
                )
            case 'BotNotInVCError':
                await interaction.response.send_message(
                    'Bot has to be with you in a voice channel to use this command.',
                    ephemeral = True
                )
            case 'DifferentChannelsError':
                await interaction.response.send_message(
                    'You and the bot are in different voice channels, move to use this command.',
                    ephemeral = True
                )
            case _:
                await interaction.response.send_message(
                    'An undocumented error occurred.',
                    ephemeral = True
                )


    async def play(self, interaction: discord.Interaction, song: str, number: int = None) -> None:
        """If user calling the command is in a voice channel, adds wanted song/list to queue of that guild."""
        guild_bot = self.bot.guild_bots[interaction.guild.id]

        user_voice_state: discord.VoiceState | None = interaction.user.voice
        bot_vc_id: int | None = guild_bot.voice_channel.id if (guild_bot.voice_channel is not None) else None

        # if user is not in a voice channel
        if user_voice_state is None:
            await interaction.response.send_message('Connect to a voice channel to play songs.', ephemeral = True)
            return
        # if user is in a different voice channel than the bot
        elif bot_vc_id and user_voice_state.channel.id != bot_vc_id:
            await interaction.response.send_message('You are not in voice channel with the bot.', ephemeral = True)
            return
        # if user is in a voice channel with the bot
        try:
            await guild_bot.add_to_queue(song, user_voice_state.channel, number)
        except CommandExecutionError as error:
            await interaction.response.send_message(error.message, ephemeral = True)
        except:
            await interaction.response.send_message('An undocumented error occurred.', ephemeral = True)
        # else:
        #    await interaction.response.send_message('Added song(s).', ephemeral = True)


    async def skip(self, interaction: discord.Interaction) -> None:
        """Skips to next song in queue."""
        # get guild bot that should execute the command
        guild_bot = self.bot.guild_bots[interaction.guild.id]
        try:
            # check if user is with the bot, function raises exceptions otherwise
            user_with_bot_check(interaction, guild_bot)
        except Exception as exception:
            # send an error message if user is not with the bot
            await self.handle_interaction_error(interaction, exception)
            return

        try:
            # try to execute the command
            await guild_bot.skip()
        except CommandExecutionError as error:
            # if the command fails to execute, the right error message is shown
            await interaction.response.send_message(error.message, ephemeral = True)
        except:
            # if the error is undocumented, a generic error message is shown
            await interaction.response.send_message('An undocumented error occurred.', ephemeral = True)
        else:
            # follow up with a command confirmation
            await interaction.response.send_message('Skipped song.', ephemeral = True)


    async def loop(self, interaction: discord.Interaction) -> None:
        """Loops the following queue including the current song (but not the history)."""
        guild_bot = self.bot.guild_bots[interaction.guild.id]
        try:
            user_with_bot_check(interaction, guild_bot)
        except Exception as exception:
            await self.handle_interaction_error(interaction, exception)
            return

        try:
            await guild_bot.loop()
        except CommandExecutionError as error:
            await interaction.response.send_message(error.message, ephemeral = True)
        except:
            await interaction.response.send_message('An undocumented error occurred.', ephemeral = True)
        else:
            await interaction.response.send_message('Loop toggled.', ephemeral = True)


    async def clear(self, interaction: discord.Interaction) -> None:
        """Loops the current song."""
        guild_bot = self.bot.guild_bots[interaction.guild.id]
        try:
            user_with_bot_check(interaction, guild_bot)
        except Exception as exception:
            await self.handle_interaction_error(interaction, exception)
            return

        try:
            await guild_bot.clear()
        except CommandExecutionError as error:
            await interaction.response.send_message(error.message, ephemeral = True)
        except:
            await interaction.response.send_message('An undocumented error occurred.', ephemeral = True)
        else:
            await interaction.response.send_message('Queue cleared.', ephemeral = True)


    async def disconnect(self, interaction: discord.Interaction) -> None:
        """Disconnects bot from voice channel."""
        guild_bot = self.bot.guild_bots[interaction.guild.id]
        try:
            user_with_bot_check(interaction, guild_bot)
        except Exception as exception:
            await self.handle_interaction_error(interaction, exception)
            return

        try:
            await guild_bot.dc()
        except CommandExecutionError as error:
            await interaction.response.send_message(error.message, ephemeral = True)
        except:
            await interaction.response.send_message('An undocumented error occurred.', ephemeral = True)
        else:
            await interaction.response.send_message('Bot disconnected.', ephemeral = True)


    async def previous(self, interaction: discord.Interaction) -> None:
        """Skips current song and plays first song in history, i.e. previous song."""
        guild_bot = self.bot.guild_bots[interaction.guild.id]
        try:
            user_with_bot_check(interaction, guild_bot)
        except Exception as exception:
            await self.handle_interaction_error(interaction, exception)
            return

        try:
            await guild_bot.previous()
        except CommandExecutionError as error:
            await interaction.response.send_message(error.message, ephemeral = True)
        except:
            await interaction.response.send_message('An undocumented error occurred.', ephemeral = True)
        else:
            await interaction.response.send_message('Went to previous song.', ephemeral = True)


    async def queue(self, interaction: discord.Interaction) -> None:
        # todo: see how this behaves when ui button behaviour is changed
        """Swaps queue display type. (short/long)"""
        guild_bot = self.bot.guild_bots[interaction.guild.id]
        try:
            user_with_bot_check(interaction, guild_bot)
        except Exception as exception:
            await self.handle_interaction_error(interaction, exception)
            return

        try:
            await guild_bot.toggle_queue()
        except CommandExecutionError as error:
            await interaction.response.send_message(error.message, ephemeral = True)
        except:
            await interaction.response.send_message('An undocumented error occurred.', ephemeral = True)
        else:
            await interaction.response.send_message('Queue display toggled.', ephemeral = True)


    async def history(self, interaction: discord.Interaction) -> None:
        # todo: see how this behaves when ui button behaviour is changed
        """Swaps history display type. (show/hide)."""
        guild_bot = self.bot.guild_bots[interaction.guild.id]
        try:
            user_with_bot_check(interaction, guild_bot)
        except Exception as exception:
            await self.handle_interaction_error(interaction, exception)
            return

        try:
            await guild_bot.toggle_history()
        except CommandExecutionError as error:
            await interaction.response.send_message(error.message, ephemeral = True)
        except:
            await interaction.response.send_message('An undocumented error occurred.', ephemeral = True)
        else:
            await interaction.response.send_message('History toggled.', ephemeral = True)


    async def lyrics(self, interaction: discord.Interaction) -> None:
        """Swaps history display type. (show/hide)."""
        guild_bot = self.bot.guild_bots[interaction.guild.id]
        try:
            user_with_bot_check(interaction, guild_bot)
        except Exception as exception:
            await self.handle_interaction_error(interaction, exception)
            return

        try:
            await guild_bot.toggle_lyrics()
        except CommandExecutionError as error:
            await interaction.response.send_message(error.message, ephemeral = True)
        except:
            await interaction.response.send_message('An undocumented error occurred.', ephemeral = True)
        else:
            await interaction.response.send_message('Lyrics display toggled.', ephemeral = True)


    async def shuffle(self, interaction: discord.Interaction):
        """Shuffles music queue."""
        guild_bot = self.bot.guild_bots[interaction.guild.id]
        try:
            user_with_bot_check(interaction, guild_bot)
        except Exception as exception:
            await self.handle_interaction_error(interaction, exception)
            return

        try:
            await guild_bot.shuffle()
        except CommandExecutionError as error:
            await interaction.response.send_message(error.message, ephemeral = True)
        except:
            await interaction.response.send_message('An undocumented error occurred.', ephemeral = True)
        else:
            await interaction.response.send_message('Shuffle toggled.', ephemeral = True)


    async def swap(self, interaction: discord.Interaction, song1: int, song2: int) -> None:
        """
        Swaps places of two songs in the queue.
        Numbering of arguments starts with 1, 0 refers to the currently playing song.
        Indexes starting with 0 are passed to swap method of music guild_bot.
        """
        guild_bot = self.bot.guild_bots[interaction.guild.id]
        try:
            user_with_bot_check(interaction, guild_bot)
        except Exception as exception:
            await self.handle_interaction_error(interaction, exception)
            return

        try:
            await guild_bot.swap(song1, song2)
        except CommandExecutionError as error:
            await interaction.response.send_message(error.message, ephemeral = True)
        except:
            await interaction.response.send_message('An undocumented error occurred.', ephemeral = True)
        else:
            await interaction.response.send_message('Songs Swapped.', ephemeral = True)


    async def pause(self, interaction: discord.Interaction) -> None:
        """
        Pauses if playing, unpauses if paused.
        """
        guild_bot = self.bot.guild_bots[interaction.guild.id]
        try:
            user_with_bot_check(interaction, guild_bot)
        except Exception as exception:
            await self.handle_interaction_error(interaction, exception)
            return

        try:
            await guild_bot.pause()
        except CommandExecutionError as error:
            await interaction.response.send_message(error.message, ephemeral = True)
        except:
            await interaction.response.send_message('An undocumented error occurred.', ephemeral = True)
        else:
            await interaction.response.send_message('Player (un)paused.', ephemeral = True)


    async def remove(self, interaction: discord.Interaction, number: int) -> None:
        """
        Pauses if playing, unpauses if paused.
        """
        guild_bot = self.bot.guild_bots[interaction.guild.id]
        try:
            user_with_bot_check(interaction, guild_bot)
        except Exception as exception:
            await self.handle_interaction_error(interaction, exception)
            return

        try:
            await guild_bot.remove(number)
        except CommandExecutionError as error:
            await interaction.response.send_message(error.message, ephemeral = True)
        except:
            await interaction.response.send_message('An undocumented error occurred.', ephemeral = True)
        else:
            await interaction.response.send_message('Song removed from queue.', ephemeral = True)


    async def goto(self, interaction: discord.Interaction, number: int) -> None:
        """
        Pauses if playing, unpauses if paused.
        """
        guild_bot = self.bot.guild_bots[interaction.guild.id]
        try:
            user_with_bot_check(interaction, guild_bot)
        except Exception as exception:
            await self.handle_interaction_error(interaction, exception)
            return

        try:
            await guild_bot.goto(number)
        except CommandExecutionError as error:
            await interaction.response.send_message(error.message, ephemeral = True)
        except:
            await interaction.response.send_message('An undocumented error occurred.', ephemeral = True)
        else:
            await interaction.response.send_message('Jumped to song.', ephemeral = True)


    # async def create(self, interaction: discord.Interaction, name: str) -> None:
    #    """
    #    Pauses if playing, unpauses if paused.
    #    """
    #    await interaction.response.send_message(
    #        content = 'Select playlist type.',
    #        view = CreatePlaylistButtons(name),
    #        ephemeral = True
    #    )


    # async def add(self, interaction: discord.Interaction, number: int = 0) -> None:
    #    """
    #    Pauses if playing, unpauses if paused.
    #    """
    #    guild_bot = self.guild_bots[interaction.guild.id]

    #    song_index = guild_bot.p_index + number
    #    song = guild_bot.queue[song_index]

    #    await interaction.response.send_message(
    #        content = 'Select playlist type.',
    #        view = ListSelectButtons(song),
    #        ephemeral = True
    #    )
