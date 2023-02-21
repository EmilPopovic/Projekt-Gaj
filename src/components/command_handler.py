import discord

from utils import CommandExecutionError, user_with_bot_check, InteractionResponder as Responder


# noinspection PyBroadException
class CommandHandler:
    def __init__(self, main_bot):
        self.bot = main_bot

    @staticmethod
    async def handle_interaction_error(interaction, exception):
        match type(exception).__name__:
            case 'UserNotInVCError':
                await Responder.send('Connect to a voice channel to use this command.', interaction, fail = True)
            case 'BotNotInVCError':
                await Responder.send('Shteff must be in a voice channel to use this command.', interaction, fail = True)
            case 'DifferentChannelsError':
                await Responder.send('You and Shteff are in different voice channels.', interaction, fail = True)
            case _:
                await Responder.send('An undocumented error occurred.', interaction, fail = True)

    # todo: ignore command if bot not in vc
    async def __execute(self,
                        guild_bot,
                        func,
                        success_msg: str,
                        interaction: discord.Interaction,
                        send_response: bool = True,
                        args=None,
                        kwargs=None) -> bool:
        try:
            user_with_bot_check(interaction, guild_bot)
        except Exception as exception:
            await self.handle_interaction_error(interaction, exception)
            return False

        try:
            if args is None and kwargs is None:
                await func()
            elif args is None:
                await func(**kwargs)
            elif kwargs is None:
                await func(*args)
            else:
                await func(*args, **kwargs)
        except CommandExecutionError as error:
            await Responder.send(error.message, interaction, fail = True)
            return False
        except Exception as _:
            await Responder.send('An undocumented error occurred.', interaction, fail = True)
            return False
        else:
            if send_response: await Responder.send(success_msg, interaction)
            return True

    async def play(self, interaction: discord.Interaction, song: str, place: int = None, send_response=True):
        """If user calling the command is in a voice channel, adds wanted song/list to queue of that guild."""
        guild_bot = self.bot.guild_bots[interaction.guild.id]

        user_voice_state: discord.VoiceState | None = interaction.user.voice
        bot_vc_id: int | None = guild_bot.voice_channel.id if (guild_bot.voice_channel is not None) else None

        # if user is not in a voice channel
        if user_voice_state is None:
            await Responder.send('Connect to a voice channel to play songs.', interaction, fail = True)
            return
        # if user is in a different voice channel than the bot
        elif bot_vc_id and user_voice_state.channel.id != bot_vc_id:
            await Responder.send('You are not in a voice channel with Shteff', interaction, fail = True)
            return
        # if user is in a voice channel with the bot
        try:
            await Responder.send('Trying to add song(s)', interaction, event = True)
            await guild_bot.add_to_queue(
                query = song,
                voice_channel = user_voice_state.channel,
                number = place,
                interaction = interaction
            )
        except CommandExecutionError as error:
            await Responder.send(error.message, interaction, followup = True, fail = True)
        except Exception as _:
            await Responder.send('An undocumented error occurred.', interaction, followup = True, fail = True)
        # else:
        #    if send_response: await interaction.response.send_message('Added song(s).', ephemeral=True)

    async def swap(self, interaction: discord.Interaction, song1: int, song2: int, send_response=True):
        guild_bot = self.bot.guild_bots[interaction.guild.id]
        args = song1, song2
        success = await self.__execute(guild_bot, guild_bot.swap, 'Songs swapped', interaction, send_response, args)
        return success

    async def remove(self, interaction: discord.Interaction, number: int, send_response=True):
        guild_bot = self.bot.guild_bots[interaction.guild.id]
        args = number
        success = await self.__execute(guild_bot, guild_bot.remove, 'Song removed', interaction, send_response, args)
        return success

    async def goto(self, interaction: discord.Interaction, number: int, send_response=True):
        guild_bot = self.bot.guild_bots[interaction.guild.id]
        args = number
        success = await self.__execute(guild_bot, guild_bot.goto, 'Jumped to song.', interaction, send_response, args)
        return success

    async def skip(self, interaction: discord.Interaction, send_response=True):
        guild_bot = self.bot.get_bot(interaction)
        success = await self.__execute(guild_bot, guild_bot.skip, 'Skipped to next song.', interaction, send_response)
        return success

    async def loop(self, interaction: discord.Interaction, send_response=True):
        guild_bot = self.bot.get_bot(interaction)
        success = await self.__execute(guild_bot, guild_bot.loop, 'Loop toggled.', interaction, send_response)
        return success

    async def clear(self, interaction: discord.Interaction, send_response=True):
        guild_bot = self.bot.get_bot(interaction)
        success = await self.__execute(guild_bot, guild_bot.clear, 'Queue cleared.', interaction, send_response)
        return success

    async def disconnect(self, interaction: discord.Interaction, send_response=True):
        guild_bot = self.bot.get_bot(interaction)
        success = await self.__execute(guild_bot, guild_bot.dc, 'Bot disconnected.', interaction, send_response)
        return success

    async def previous(self, interaction: discord.Interaction, send_response=True):
        guild_bot = self.bot.get_bot(interaction)
        success = await self.__execute(guild_bot, guild_bot.previous, 'Went to previous song.', interaction, send_response)
        return success

    async def queue(self, interaction: discord.Interaction, send_response=True):
        guild_bot = self.bot.get_bot(interaction)
        success = await self.__execute(guild_bot, guild_bot.toggle_queue, 'Display toggled.', interaction, send_response)
        return success

    async def history(self, interaction: discord.Interaction, send_response=True):
        guild_bot = self.bot.get_bot(interaction)
        success = await self.__execute(guild_bot, guild_bot.toggle_history, 'Display toggled.', interaction, send_response)
        return success

    async def lyrics(self, interaction: discord.Interaction, send_response=True):
        guild_bot = self.bot.get_bot(interaction)
        success = await self.__execute(guild_bot, guild_bot.toggle_lyrics, 'Lyrics toggled.', interaction, send_response)
        return success

    async def shuffle(self, interaction: discord.Interaction, send_response=True):
        guild_bot = self.bot.get_bot(interaction)
        success = await self.__execute(guild_bot, guild_bot.pause, 'Shuffle toggled.', interaction, send_response)
        return success

    async def pause(self, interaction: discord.Interaction, send_response=True):
        guild_bot = self.bot.get_bot(interaction)
        success = await self.__execute(guild_bot, guild_bot.pause, 'Player (un)paused.', interaction, send_response)
        return success
