import asyncio
import music_cog as mc
from discord_components import ComponentsBot
from help_cog import help_cog
from anti_spam_cog import anti_spam_cog
from secrets import token


bot = ComponentsBot(command_prefix='!')


@bot.event
async def on_ready():
    print(f'\nLogged in as {bot.user}\nBOT START\n')
    print(f'Bot user id: {bot.user.id}')
    
    bot.remove_command('help')

    bot.add_cog(help_cog(bot))

    guilds = [guild.id for guild in bot.guilds]
    for guild in guilds:
        print(guild)

        m_cog = await create_music_cog(bot, guild)
        bot.add_cog(m_cog)

    bot.add_cog(anti_spam_cog(bot))


async def create_music_cog(bot, guild):
    music_cog = mc.music_cog(bot, guild)
    await music_cog._init()
    return music_cog


def main():
    '''Main je početak svega.'''
    bot.run(token)


if __name__ ==  '__main__':
    main()