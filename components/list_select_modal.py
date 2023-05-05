import discord
from discord import ui

from utils import InteractionResponder as Responder, PermissionsCheck


class UserListSelectModal(ui.Modal, title= 'Select a playlist'):
    manager = None

    playlist_name = ui.TextInput(
        label = 'Playlist name',
        placeholder = 'My Playlist',
        required = True
    )

    async def on_submit(self, interaction: discord.Interaction):
        await self.manager.add_to_playlist(interaction, self.playlist_name.value, '', scope = 'user')

    async def on_error(self, interaction: discord.Interaction, error):
        await Responder.send('Something went wrong, try again later.', interaction, fail = True)


class ServerListSelectModal(ui.Modal, title= 'Select a playlist'):
    manager = None

    playlist_name = ui.TextInput(
        label = 'Playlist name',
        placeholder = 'My Playlist',
        required = True
    )

    async def on_submit(self, interaction: discord.Interaction):
        if PermissionsCheck.interaction_has_permissions(interaction):
            await self.manager.add_to_playlist(interaction, self.playlist_name.value, '', scope = 'server')
        else:
            msg = 'You don\'t seem to be an admin or a dj, so you cant use this button.'
            await Responder.send(msg, interaction, fail = True)

    async def on_error(self, interaction: discord.Interaction, error):
        await Responder.send('Something went wrong, try again later.', interaction, fail = True)