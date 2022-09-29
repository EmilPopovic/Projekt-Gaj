import music_cog as mc
#import interactions
from discord.ext import commands
from help_cog import help_cog
from anti_spam_cog import anti_spam_cog
from secrets import token

import sys
import subprocess
import discord

from colors import *

intents = discord.Intents(messages=True, guilds=True)
bot = commands.Bot(command_prefix='!', intents=intents)
#bot = interactions.Client(token=token)


@bot.event
async def on_ready():
    print(f'\n{c_login()} as {bot.user}\nBot user id: {c_user(bot.user.id)}\n')

    bot.remove_command('help')
    await bot.add_cog(anti_spam_cog(bot))

    guilds = [guild.id for guild in bot.guilds]
    for guild in guilds:
        if guild == 831909949436198992:
            await add_guild(guild)


async def add_guild(guild_id):
    m_cog = await mc.create_music_cog(bot, guild_id)
    await bot.add_cog(m_cog)
    channel = m_cog.bot_channel_id
    print(f'{c_time()} {c_event("ADDED GUILD")} {c_guild(guild_id)} with channel {c_channel(channel)}')


def install_packages():
    with open('requirements.txt', 'r') as packages:
        for package in packages:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', f'{package}'])


def main():
    '''Main je početak svega.'''
    #install_packages()
    bot.run(token)
    #bot.start()


if __name__ ==  '__main__':
    main()
