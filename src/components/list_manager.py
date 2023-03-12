from utils import InteractionResponder as Responder, SqlException, c_event, c_user, c_guild


class ListManager:
    # todo: remove placeholders
    def __init__(self, main_bot, db):
        self.main_bot = main_bot
        self.db = db

    def get_current_song(self, interaction):
        guild_bot = self.main_bot.get_bot_from_interaction(interaction)
        p_index = guild_bot.p_index
        queue = guild_bot.queue

        try:
            song = queue[p_index]
        except IndexError:
            return None
        else:
            if not song.is_good or song.from_file:
                return None
            return song

    async def add(self, interaction, name: str):
        # get the SongGenerator object of the song we want to add
        song = self.get_current_song(interaction)
        if song is None:
            await Responder.send('No song to add.', interaction, fail=True)

        # check if the list we want to add the song to exists
        try:
            lists = self.db.get_user_lists(interaction.user.id)
        except SqlException:
            await Responder.send('Internal error, try again later.', interaction, fail=True)
        else:
            if name not in lists:
                await Responder.send(f'Playlist named "{name}" does not exist', interaction, fail=True)

        # try to add the song to the list
        try:
            print(f'added "{song.name}" to "{name}"')
            # todo self.db.add_to_personal_playlist(song, interaction.user.id, name)
        except SqlException:
            await Responder.send('Internal error, try again later.', interaction, fail=True)
        else:
            await Responder.send(f'Added song to "{name}".', interaction)

    async def server_add(self, interaction, name: str):
        # get the SongGenerator object of the song we want to add
        song = self.get_current_song(interaction)
        if song is None:
            await Responder.send('No song to add.', interaction, fail=True)

        # check if the list we want to add the song to exists
        try:
            lists = self.db.get_user_lists(interaction.user.id)
        except SqlException:
            await Responder.send('Internal error, try again later.', interaction, fail=True)
        else:
            if name not in lists:
                await Responder.send(f'Playlist named "{name}" does not exist', interaction, fail=True)

        # try to add the song to the list
        try:
            print(f'added "{song.name}" to "{name}"')
            # todo self.db.add_to_personal_playlist(song, interaction.user.id, name)
        except SqlException:
            await Responder.send('Database error, try again later.', interaction, fail=True)
        else:
            await Responder.send(f'Added song to "{name}".', interaction)

    async def create(self, interaction, name: str):
        # max number of personal playlists is 25 per user
        try:
            user_lists = self.db.get_user_lists(interaction.user.id)
        except SqlException:
            await Responder.send('Database error, try again later.', interaction, fail=True)
            return
        else:
            num_of_lists = len(user_lists)
            if num_of_lists > 25:
                await Responder.send('Cannot have more than 25 lists.', interaction, fail=True)
                return

        try:
            self.db.create_personal_playlist(interaction.user.id, name)
        except SqlException:
            await Responder.send('Database error, try again later.', interaction, fail=True)
        else:
            print(f'{c_event("CREATED LIST")} for user {c_user(interaction.user.id)}')
            await Responder.send(f'Created playlist "{name}".', interaction)

    async def server_create(self, interaction, name: str):
        # max number of server playlists is 25 per server
        try:
            server_lists = self.db.get_server_lists(interaction.user.id)
        except SqlException:
            await Responder.send('Database error, try again later.', interaction, fail=True)
            return
        else:
            num_of_lists = len(server_lists)
            if num_of_lists > 25:
                await Responder.send('Cannot have more than 25 lists.', interaction, fail=True)
                return

        try:
            self.db.create_server_playlist(interaction.guild.id, name)
        except SqlException:
            await Responder.send('Database error, try again later.', interaction, fail=True)
        else:
            print(f'{c_event("CREATED LIST")} for guild {c_guild(interaction.guild.id)}')
            await Responder.send(f'Created playlist "{name}".', interaction)

    async def delete(self, interaction, name):
        try:
            server_lists = self.db.get_user_lists(interaction.user.id)
        except SqlException:
            await Responder.send('Database error, try again later.', interaction, fail=True)
            return
        else:
            if name not in server_lists:
                await Responder.send(f'"{name}" does not exist.', interaction, fail=True)
                return

        try:
            self.db.delete_personal_playlist(interaction.user.id)
        except SqlException:
            await Responder.send('Database error, try again later.', interaction, fail=True)
        else:
            await Responder.send(f'Deleted playlist "{name}".', interaction)

    async def server_delete(self, interaction, name):
        ...
