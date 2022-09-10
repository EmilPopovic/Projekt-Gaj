import asyncio
from discord.ext import commands
from discord_components import ComponentsBot
from help_cog import help_cog
from music_cog import music_cog
from anti_spam_cog import anti_spam_cog
from secrets import token


bot = ComponentsBot(command_prefix='!')


@bot.event
async def on_ready():
    print(f'\nLogged in as {bot.user}\nBOT START\n')


async def create_music_cog(bot, guild):
    music_cog = music_cog(bot, guild)
    await music_cog._init()
    return music_cog


async def main():
    '''Main je početak svega.'''
    bot.remove_command('help')

    bot.add_cog(help_cog(bot))

    print(bot.guilds)

    guilds = [guild.id for guild in bot.guilds]
    for guild in guilds:
        m_cog = await create_music_cog(bot, guild)
        bot.add_cog(m_cog)

    bot.add_cog(anti_spam_cog(bot))

    bot.run(token)


if __name__ ==  '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())