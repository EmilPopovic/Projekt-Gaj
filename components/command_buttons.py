import discord

from .list_select_modal import UserListSelectModal, ServerListSelectModal
from utils import BtnStyle, InteractionResponder as Responder


class CommandButtons(discord.ui.View):
    command_handler = None
    bot = None

    def __init__(self, guild_bot, timeout=180):
        super().__init__(timeout=timeout)

        self.guild_bot = guild_bot

        # first row

        self.shuffle_button = discord.ui.Button(
                label='⎇',
                style=BtnStyle.green if self.guild_bot.queue.is_shuffled else BtnStyle.grey,
                row=0,
                custom_id='shuffle'
            )
        self.shuffle_button.callback = self.shuffle_btn_callback
        self.add_item(self.shuffle_button)

        self.previous_button = discord.ui.Button(
            label='◁',
            style=BtnStyle.grey,
            row=0,
            custom_id='previous'
        )
        self.previous_button.callback = self.previous_btn_callback
        self.add_item(self.previous_button)

        self.pause_button = discord.ui.Button(
            label='▶' if self.guild_bot.is_paused else '▉',
            style=BtnStyle.green if self.guild_bot.is_paused else BtnStyle.grey,
            row=0,
            custom_id='pause'
        )
        self.pause_button.callback = self.pause_btn_callback
        self.add_item(self.pause_button)

        self.skip_button = discord.ui.Button(
            label='▷',
            style=BtnStyle.grey,
            row=0,
            custom_id='skip'
        )
        self.skip_button.callback = self.skip_btn_callback
        self.add_item(self.skip_button)

        self.loop_button = discord.ui.Button(
            label='⭯',
            style=BtnStyle.grey if self.guild_bot.queue.loop_status == 'none' else BtnStyle.green,
            row=0,
            custom_id='loop'
        )
        self.loop_button.callback = self.loop_btn_callback
        self.add_item(self.loop_button)

        # second row

        self.clear_button = discord.ui.Button(
            label='✖',
            style=BtnStyle.red,
            row=1,
            custom_id='clear'
        )
        self.clear_button.callback = self.clear_btn_callback
        self.add_item(self.clear_button)

        self.disconnect_button = discord.ui.Button(
            label='#',
            style=BtnStyle.red,
            row=1,
            custom_id='dc'
        )
        self.disconnect_button.callback = self.dc_btn_callback
        self.add_item(self.disconnect_button)

        self.lyrics_button = discord.ui.Button(
            label='≡',
            style=BtnStyle.green if self.guild_bot.show_lyrics else BtnStyle.grey,
            row=1,
            custom_id='lyrics'
        )
        self.lyrics_button.callback = self.lyrics_btn_callback
        self.add_item(self.lyrics_button)

        self.add_button = discord.ui.Button(
            label='+',
            style=BtnStyle.blue,
            row=1,
            custom_id='user_add'
        )
        self.add_button.callback = self.add_btn_callback
        self.add_item(self.add_button)

        self.server_add_button = discord.ui.Button(
            label='S+',
            style=BtnStyle.blue,
            row=1,
            custom_id='server_add'
        )
        self.server_add_button.callback = self.server_add_btn_callback
        self.add_item(self.server_add_button)

    async def shuffle_btn_callback(self, interaction: discord.Interaction):
        success = await self.command_handler.shuffle(interaction, send_response=False)
        if success:
            self.shuffle_button.style = BtnStyle.green if self.guild_bot.queue.is_shuffled else BtnStyle.grey
            await interaction.response.edit_message(view=self)

    async def previous_btn_callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(view=self)
        await self.command_handler.previous(interaction, send_response=False)

    async def pause_btn_callback(self, interaction: discord.Interaction):
        success = await self.command_handler.pause(interaction, send_response=False)
        if success:
            self.pause_button.style = BtnStyle.green if self.guild_bot.is_paused else BtnStyle.grey
            self.pause_button.label = '▶' if self.guild_bot.is_paused else '▉'
            await interaction.response.edit_message(view=self)

    async def skip_btn_callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(view=self)
        await self.command_handler.skip(interaction, send_response=False)

    async def loop_btn_callback(self, interaction: discord.Interaction):
        success = await self.command_handler.loop(interaction, send_response=False)
        if success:
            if self.guild_bot.queue.loop_status == 'queue':
                self.loop_button.style = BtnStyle.green
            elif self.guild_bot.queue.loop_status == 'single':
                self.loop_button.style = BtnStyle.blue
            else:
                self.loop_button.style = BtnStyle.grey
            await interaction.response.edit_message(view=self)

    async def clear_btn_callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(view=self)
        await self.command_handler.clear(interaction, send_response=False)

    async def dc_btn_callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(view=self)
        await self.command_handler.disconnect(interaction, send_response=False)

    async def lyrics_btn_callback(self, interaction: discord.Interaction):
        success = await self.command_handler.lyrics(interaction, send_response=False)
        if success:
            self.lyrics_button.style = BtnStyle.green if self.guild_bot.show_lyrics else BtnStyle.grey
            await interaction.response.edit_message(view=self)

    @staticmethod
    async def add_btn_callback(interaction: discord.Interaction):
        await interaction.response.send_modal(UserListSelectModal())

    @staticmethod
    async def server_add_btn_callback(interaction: discord.Interaction):
        await interaction.response.send_modal(ServerListSelectModal())
