# cog files
import music_cog as mc
from help_cog import help_cog
from anti_spam_cog import anti_spam_cog

# discord api
import discord
from discord import app_commands
from discord.ext import commands

# tokens
from secrets import token

# package installation
import sys
import subprocess

# color coded terminal text
from colors import *


bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

global music_cogs
music_cogs = {}

@bot.event
async def on_ready():
    """
    Runs on bot login.
    Syncs slash commands.
    Creates MusicCog objects for every guild.
    """
    print(f'\n{c_login()} as {bot.user}\nBot user id: {c_user(bot.user.id)}\n')

    try:
        synced = await bot.tree.sync()
        print(f'{c_time()} {c_event("SYNCED")} {len(synced)} command(s)')
    except:
        print(f'{c_time()} {c_err()} failed to sync command(s)')

    bot.remove_command('help')
    await bot.add_cog(anti_spam_cog(bot))

    for guild in [guild.id for guild in bot.guilds]:
        music_cogs[guild] = await add_guild(guild)


async def add_guild(guild_id):
    """
    Creates a MusicCog object for specific guild.
    """
    m_cog = await mc.create_music_cog(bot, guild_id)
    await bot.add_cog(m_cog)
    print(f'{c_time()} {c_event("ADDED GUILD")} {c_guild(guild_id)} with channel {c_channel(m_cog.bot_channel_id)}')
    return m_cog


@bot.tree.command(name='p')
@app_commands.describe(query='song name')
async def p(ctx, interaction: discord.Interaction, query: str):
    """
    If user calling the command is in a voice channel, adds wanted song/list to queue of that guild.
    """
    vc = ctx.author.voice.channel
    # if user is not in a voice channel
    if vc is None:
        await interaction.response.send_message('Connect to a voice channel to play songs!', ephemeral=True)
    # if user is in a voice channel
    else:
        await music_cogs[ctx.guild.id].add_to_queue(query, vc)


def install_packages():
    """
    Installs all packages listed in requirements.txt file.
    """
    with open('requirements.txt', 'r') as packages:
        for package in packages:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', f'{package}'])


def main():
    """
    Main is the beginning of everything.
    """
    #install_packages()
    bot.run(token)


if __name__ ==  '__main__':
    main()
