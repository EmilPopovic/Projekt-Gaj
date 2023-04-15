import discord


class HelpCog:
    # todo: update this
    slash_commands = [
        ('/help', 'Sends a help message just like this one. How did you get here?'),
        ('/ping', 'Pong! Shows bot latency.'),
        ('/play', 'Connects the bot to voice channel and adds your song to the queue.'),
        ('/pause', 'Pauses or unpauses playing.'),
        ('/skip', 'Skips to the next song in the queue.'),
        ('/back', 'Goes back to the previously played song.'),
        ('/loop', 'Toggles between looping queue, looping a single song and not looping.'),
        ('/clear', 'Removes all songs from the queue and stops playing.'),
        ('/dc', 'Disconnects the bot from voice channel and clears the queue.'),
        ('/lyrics', 'Toggles song lyrics.'),
        ('/shuffle', 'Shuffles or unshuffles queue.'),
        ('/swap', 'Swaps the places of two song in the queue.'),
        ('/remove', 'Removes the song from the queue.'),
        ('/goto', 'Jumps to the song in the queue.'),
    ]

    button_commands = [
        ('⎇', 'Shuffle or unshuffle queue.'),
        ('◁', 'Go back one song.'),
        ('▉', 'Pause or unpause playing.'),
        ('▷', 'Skip currently playing song.'),
        ('⭯', 'Toggle between looping queue, looping a single song and not looping.'),
        ('✖', 'Clear the queue and stop playing.'),
        ('#', 'Disconnect Shteff from the voice channel.'),
        ('≡', 'Toggle song lyrics.'),
        ('⯆', 'Toggle short queue display (only the next five songs).'),
        ('⯅', 'Toggle history display (already played songs).')
    ]

    github_link = 'https://github.com/Mjolnir2425/Shteff'
    description = f'Shteff is a free and open source music bot. Source code is available at {github_link}.'

    @classmethod
    def get_buttons_content(cls):
        content = ''
        for name, description in cls.button_commands:
            content += f'`{name}` - {description}\n'
        return content

    @classmethod
    def get_slash_content(cls):
        content = ''
        for name, description in cls.slash_commands:
            content += f'`{name:10}` - {description}\n'
        return content

    @classmethod
    async def send_message(cls, interaction: discord.Interaction):
        embed = discord.Embed(
            title='The Manual',
            description='Read it.',
            color=0xf1c40f
        )
        embed.add_field(
            name='Slash commands:',
            value=cls.get_slash_content(),
            inline=False
        )
        embed.add_field(
            name='Button commands:',
            value=cls.get_buttons_content(),
            inline=False
        )
        embed.add_field(
            name='About us',
            value=cls.description,
            inline=False
        )
        embed.set_footer(text='We\'ve done our photosynthesis, have you?')

        await interaction.response.send_message(content='', embed=embed, ephemeral=True)
