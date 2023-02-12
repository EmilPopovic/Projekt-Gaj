# todo: rewrite all of this

import discord
from discord.ext import commands


class HelpCog(commands.Cog):
    # todo: docstring
    # todo: finish help message
    help_message = '''
`/clear   ` - Clears queue and history, stops playing.
`/dc      ` - Disconnects bot from voice channel.
`/history ` - Toggles history display type (show/hide).
`/loop    ` - Loops queue or single song.
`/pause   ` - Pauses or unpauses playing.
`/play    ` - Adds a song/list to queue.
`/previous` - Skips current song and plays previous.
`/queue   ` - Toggles queue display type (short/long).
`/shuffle ` - Toggles queue shuffle.
`/skip    ` - Skips to the next queued song.
`/swap    ` - Swap places of queued songs.
`/lyrics  ` - Toggles lyrics display (show/hide).
'''
    bot = None


    @staticmethod
    async def command(interaction: discord.Interaction):
        await interaction.response.send_message(content = HelpCog.help_message, ephemeral = True)
