import subprocess
import sys

import discord
from discord import app_commands
from discord.ext import commands

import cogs.music_cog as mc
from cogs.anti_spam_cog import anti_spam_cog
from colors import *
from secrets import token

bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

global music_cogs
music_cogs = {}


@bot.event
async def on_ready() -> None:
    """
    Runs on bot login.
    Syncs slash commands.
    Creates MusicCog objects for every guild.
    """
    # sync commands
    print(f'{c_time()} {c_event("SYNCING COMMANDS")}')
    try:
        synced = await bot.tree.sync()
        print(f'{c_time()} {c_event("SYNCED")} {len(synced)} command(s)')
    # TODO: add specific exception
    except:
        print(f'{c_time()} {c_err()} failed to sync command(s)')

    bot.remove_command('help')
    await bot.add_cog(anti_spam_cog(bot))

    # create music cog for every guild bot is in
    for guild in bot.guilds:
        music_cogs[guild.id] = await add_guild(guild)
        # sync commands
        # TODO: move syncing to add_guild() function
        # try:
        #    await bot.tree.sync(guild = discord.Object(id=guild))
        #    print(f'{c_time()} {c_event("SYNCED")} commands in guild {c_guild(guild)}')
        # except:
        #    print(f'{c_time()} {c_err()} failed syncing commands in guild {c_guild(guild)}')

    print(f'\n{c_login()} as {bot.user}\nBot user id: {c_user(bot.user.id)}\n')


async def add_guild(guild_id: int) -> mc.MusicCog:
    """
    Creates a MusicCog object for specific guild.
    """
    m_cog = await mc.create_music_cog(bot, guild_id)
    await bot.add_cog(m_cog)
    print(f'{c_time()} {c_event("ADDED GUILD")} {c_guild(guild_id)} with channel {c_channel(m_cog.bot_channel_id)}')
    return m_cog


@bot.tree.command(name='play', description='Adds a song/list to queue.')
@app_commands.describe(song='The name or link of song/list.')
async def play(interaction: discord.Interaction, song: str) -> None:
    """
    If user calling the command is in a voice channel, adds wanted song/list to queue of that guild.
    """
    vc = interaction.user.voice.channel
    # if user is not in a voice channel
    if vc is None:
        await interaction.response.send_message('Connect to a voice channel to play songs!', ephemeral=True)
    # if user is in a voice channel
    else:
        # TODO: send empty response
        await interaction.response.send_message('Adding song.', ephemeral=True)
        cog = music_cogs[interaction.guild.id]
        await cog.add_to_queue(song, vc)


@bot.tree.command(name='swap', description='Swap places of two queued songs.')
@app_commands.describe(song1='Place of first song in queue.', song2='Place of second song in the queue.')
async def swap(interaction: discord.Interaction, song1: int, song2: int) -> None:
    """
    Swaps places of two songs in the queue.
    Numbering of arguments starts with 1, 0 refers to the currently playing song.
    Indexes starting with 0 are passed to swap method of music cog.
    """
    # starting with guard clauses
    # both inputs must be numbers
    if not song1.isnumeric() or not song2.isnumeric():
        await interaction.response.send_message('Number was not given as input.', ephemeral=True)
        return

    # convert to int if both inputs are numeric
    i, j = int(song1) - 1, int(song2) - 1
    # swapping only if different indexes selected
    if i == j:
        await interaction.response.send_message('List indexes must be different.', ephemeral=True)
        return

    # checking if inputs are valid numbers
    # inputs are valid if both exist in queue
    cog = music_cogs[interaction.guild.id]
    queue_len = cog.get_queue_len()

    if i >= queue_len or j >= queue_len:
        await interaction.response.send_message('Specified indexes not in list.', ephemeral=True)
        return

    # swap if guard clauses passed
    await cog.swap(i, j)


@bot.tree.command(name='pause', description='Pauses or unpauses playing.')
async def pause(interaction: discord.Interaction):
    """
    Pauses if playing, unpauses if paused.
    """
    cog = music_cogs[interaction.guild.id]
    await cog.pause()

@bot.tree.command(name='history', description='Adds a song/list to queue.')
async def history(interaction: discord.Interaction) -> None:
    await interaction.response.send_message('', ephemeral=True)



def install_packages() -> None:
    """
    Installs all packages listed in requirements.txt file.
    """
    with open('requirements.txt', 'r') as packages:
        for package in packages:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', f'{package}'])


def main() -> None:
    """
    Main is the beginning of everything.
    """
    # install_packages()
    bot.run(token)


if __name__ == '__main__':
    main()
