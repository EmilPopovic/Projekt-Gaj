# todo: rewrite all of this

from discord.ext import commands


class AntiSpamCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot_id = 831241901629243392
        self.bot_channels = [972589111980458054]
        self.bot_list_of_commands = ['!play', '!p', '!playing', '!swap', '!s']

    @commands.Cog.listener('on_message')
    async def delete_spam(self, message):
        msg_channel = message.channel.id
        msg = message.content
        msg_author = message.author.id
        if msg_channel in self.bot_channels and not any(bot_command in msg for bot_command in self.bot_list_of_commands) and msg_author != self.bot_id:
            await message.delete()
