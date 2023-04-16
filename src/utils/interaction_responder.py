import discord

from .sql_bridge import SqlSong


class InteractionResponder:
    default_color_rgb = (194, 149, 76)
    default_color = discord.Color.from_rgb(*default_color_rgb)

    @classmethod
    async def send(
            cls,
            text: str,
            interaction: discord.Interaction,
            followup: bool = False,
            fail: bool = False,
            event: bool = False,
            ephemeral: bool = True
    ) -> None:
        if fail:
            title = 'Fail'
            color = discord.Color.from_rgb(242, 63, 67)
        elif event:
            title = 'Event'
            color = cls.default_color
        else:
            title = 'Success'
            color = discord.Color.from_rgb(33, 155, 85)

        embed = discord.Embed(
            title=title,
            description=text,
            color=color
        )
        if followup:
            await interaction.followup.send(content='', embed=embed, ephemeral=ephemeral)
        else:
            await interaction.response.send_message(content='', embed=embed, ephemeral=ephemeral)

    @classmethod
    async def show_playlists(
            cls,
            playlists: list[str],
            interaction: discord.Interaction
    ) -> None:
        msg = ''
        for playlist in playlists:
            msg += f'{playlist}\n'

        embed = discord.Embed(
            title='Playlists',
            description=msg,
            color=cls.default_color
        )
        await interaction.response.send_message(content='', embed=embed, ephemeral=True)

    @staticmethod
    async def show_songs(
            cls,
            songs: list[SqlSong],
            playlist_name: str,
            interaction: discord.Interaction
    ) -> None:
        song_names = [song.song_name for song in songs]
        song_authors = [song.author_name for song in songs]
        msg = ''
        for song_author, song_name in zip(song_authors, song_names):
            msg += f'{song_author} - {song_name}\n'

        embed = discord.Embed(
            title=playlist_name,
            description=msg,
            color=cls.default_color
        )
        await interaction.response.send_message(content='', embed=embed, ephemeral=True)
