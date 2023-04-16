import discord


class Help:
    default_color_rgb = (194, 149, 76)
    default_color = discord.Color.from_rgb(*default_color_rgb)

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

    playlist_commands = [
        ('/create', 'Creates a personal playlist.'),
        ('/server-create', 'Creates a server playlist.'),
        ('/delete', 'Deletes a personal playlist.'),
        ('/server-delete', 'Deletes a server playlist.'),
        ('/add', 'Adds a song to a personal playlist.'),
        ('/server-add', 'Adds a song to a server playlist.'),
        ('/obliterate', 'Removes a song from a personal playlist.'),
        ('/server-obliterate', 'Removes a song from a server playlist.'),
        ('/catalogue', 'Lists out personal playlists.'),
        ('/server-catalogue', 'Lists out server playlists.'),
        ('/manifest', 'Lists out the songs from personal playlists.'),
        ('/server-manifest', 'Lists out the songs from server playlists.'),
        ('/playlist', 'Adds a personal playlist to the queue.'),
        ('/server-playlist', 'Adds a server playlist to the queue.'),
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
        ('+', 'Add the song to a personal playlist.'),
        ('S+', 'Add the song to a server playlist.')
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
    def get_playlist_slash_content(cls):
        content = ''
        for name, description in cls.playlist_commands:
            content += f'`{name:20}` - {description}\n'
        return content

    @classmethod
    async def send_message(cls, interaction: discord.Interaction):
        embed = discord.Embed(
            title='The Manual',
            description='Read it. Please.',
            color=cls.default_color
        )
        embed.add_field(
            name='Slash commands:',
            value=cls.get_slash_content(),
            inline=False
        )
        embed.add_field(
            name = 'Playlist commands:',
            value = cls.get_playlist_slash_content(),
            inline = False
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
