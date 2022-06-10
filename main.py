from discord.ext import commands
from help_cog import help_cog
from music_cog_1 import music_cog
from anti_spam_cog import anti_spam_cog


bot = commands.Bot(command_prefix='!')


@bot.event
async def on_ready():
    print('\nBOT START\n')


def main():
    '''Main je početak svega.'''
    bot.remove_command('help')

    bot.add_cog(help_cog(bot))
    bot.add_cog(music_cog(bot))
    bot.add_cog(anti_spam_cog(bot))

    with open('token.txt', 'r') as token:
        TOKEN = token.read()

    bot.run(TOKEN)


if __name__ == '__main__':
    main()