import discord
from discord.ui import Select, View

from utils import Database, PermissionsCheck as check, BtnStyle


class CreatePlaylistButtons(discord.ui.View):
    def __init__(self, name, timeout = 180):
        self.name = name
        super().__init__(timeout = timeout)

    @discord.ui.button(label = 'Server Playlist', style = BtnStyle.grey, row = 0)
    async def server_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user
        guild = interaction.guild
        member = guild.get_member(user.id)
        if check.has_permissions(member):
            ListAdder.create_server(guild, self.name)
        else:
            await interaction.response.send_message(
                'You do not have sufficient permissions to create a server playlist.\nYou have to be an Admin or a DJ.',
                ephemeral = True
            )

    @discord.ui.button(label = 'Personal Playlist', style = BtnStyle.grey, row = 0)
    async def personal_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user
        ListAdder.create_personal(user, self.name)


class ListSelectButtons(discord.ui.View):
    def __init__(self, song, timeout=180):
        self.song = song
        super().__init__(timeout = timeout)

    @discord.ui.button(label = 'Server Playlist', style = BtnStyle.grey, row = 0)
    async def server_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user
        guild = interaction.guild
        member = guild.get_member(user.id)
        if check.has_permissions(member):
            await ListAdder.add_to_server(user, guild, self.song, interaction)
        else:
            await interaction.response.send_message(
                'You do not have sufficient permissions to add to a server playlist.\nYou have to be an Admin or a DJ.',
                ephemeral = True
            )

    @discord.ui.button(label = 'Personal Playlist', style = BtnStyle.grey, row = 0)
    async def personal_btn(self, interaction: discord.Interaction, button: discord.ui.Button):
        user = interaction.user
        await ListAdder.add_to_personal(user, self.song, interaction)


class ServerSelect(discord.ui.View):
    def __init__(self, playlists: list, timeout=180):
        self.playlists = playlists
        super().__init__(timeout = timeout)

        @discord.ui.select(
            placeholder = 'Select Playlist',
            min_values = 1,
            max_values = 5,
            options = self.playlists
        )
        async def select_callback(select, interaction):
            return select


#class PersonalSelect(discord.ui.view):
#    def __init__(self, playlists: list, timeout=180):
#        self.playlists = playlists
#        super().__init__(timeout = timeout)
#
#        @discord.ui.select(
#            placeholder = 'Select Playlist',
#            min_values = 1,
#            max_values = 5,
#            options = self.playlists
#        )
#        async def select_callback(select, interaction):
#            return select


class CreatePlaylistView(View):
    @discord.ui.select(
        custom_id = 'scope_select',
        options = [
            discord.SelectOption(label = 'Server Playlists', value = 'server'),
            discord.SelectOption(label = 'Personal Playlists', value = 'personal')
        ],
        row = 0
    )
    async def select_callback(self, select, interaction):
        selected = select.values[0]
        member = check.get_member(interaction)
        if selected == 'server' and not check.has_permissions(member):
            await interaction.response.send_message(
                'You do not have sufficient permissions to add to a server playlist.',
                ephemeral = True
            )
            return

        await interaction.followup.send(f'chosen option: {selected}')


class ListAdder:
    db: Database = None

    def __init__(self, song, interaction):
        self.select1 = None
        self.select2 = None
        #await self.add_to_playlist(song, interaction)


    async def add_to_playlist(self, song, interaction):
        user = interaction.user
        guild = interaction.guild
        await interaction.response.send_message(
            content = 'Select the playlists you want to add the song to.',
            view = CreatePlaylistView(),
            ephemeral = True
        )



    @classmethod
    async def add_to_server(cls, user, guild, song, interaction):
        playlists: list[str] = cls.db.get_server_lists(guild.id)

        selected_lists = await interaction.response.send_message(
            content = 'Select playlists you want to add the song to.',
            ephemeral = True
        )

        for playlist in selected_lists:
            cls.db.add_to_server_playlist(song, user.id, guild.id, playlist)

    @classmethod
    async def add_to_personal(cls, user, song, interaction):
        # a list containing names of a user's saved playlists
        playlists: list[str] = cls.db.get_user_lists(user.id)
        playlists = ['lista 1', 'lista 2', 'lista 3']

        select_options = [discord.SelectOption(label = playlists[0], default = True)]
        select_options.extend([discord.SelectOption(label = playlist) for playlist in playlists[1:]])

        select = Select(
            placeholder = 'Select Playlists.',
            options = select_options,
            max_values = len(playlists)
        )

        view = View()
        view.add_item(select)

        selected_lists = await interaction.response.send_message(
            content = 'Select one or more playlists to which you want to add the song to.',
            view = view,
            ephemeral = True
        )

        #for playlist in selected_lists:
        #    cls.db.add_to_personal_playlist(song, user.id, playlist)

    @classmethod
    def create_server(cls, guild, name):
        cls.db.create_server_playlist(guild.id, name)

    @classmethod
    def create_personal(cls, user, name):
        cls.db.create_personal_playlist(user.id, name)
