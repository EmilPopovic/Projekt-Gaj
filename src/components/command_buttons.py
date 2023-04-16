import discord

from .list_select_modal import UserListSelectModal, ServerListSelectModal
from utils import BtnStyle, InteractionResponder as Responder


class CommandButtons(discord.ui.View):
    command_handler = None
    bot = None

    def __init__(self, timeout=180):
        super().__init__(timeout=timeout)

    # first row

    @discord.ui.button(label= '⎇', style=BtnStyle.grey, row=0)
    async def shuffle_btn_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        success = await self.command_handler.shuffle(interaction, send_response=False)
        if success:
            guild_bot = self.bot.get_bot_from_interaction(interaction)
            button.style = BtnStyle.green if guild_bot.queue.is_shuffled else BtnStyle.grey
            await interaction.response.edit_message(view=self)

    @discord.ui.button(label= '◁', style=BtnStyle.grey, row=0)
    async def previous_btn_callback(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.edit_message(view = self)
        await self.command_handler.previous(interaction, send_response=True)

    @discord.ui.button(label= '▉', style=BtnStyle.grey, row=0)
    async def pause_btn_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        success = await self.command_handler.pause(interaction, send_response=False)
        if success:
            guild_bot = self.bot.get_bot_from_interaction(interaction)
            button.style = BtnStyle.green if guild_bot.is_paused else BtnStyle.grey
            button.label = '▶' if guild_bot.is_paused else '▉'
            await interaction.response.edit_message(view=self)

    @discord.ui.button(label= '▷', style=BtnStyle.grey, row=0)
    async def skip_btn_callback(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.edit_message(view = self)
        await self.command_handler.skip(interaction, send_response=True)

    @discord.ui.button(label= '⭯', style=BtnStyle.grey, row=0)
    async def loop_btn_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        success = await self.command_handler.loop(interaction, send_response=False)
        if not success: return
        guild_bot = self.bot.get_bot_from_interaction(interaction)
        if guild_bot.queue.loop_status == 'queue':
            button.style = BtnStyle.green
        elif guild_bot.queue.loop_status == 'single':
            button.style = BtnStyle.blue
        else:
            button.style = BtnStyle.grey
        await interaction.response.edit_message(view=self)

    # second row

    @discord.ui.button(label= '✖', style=BtnStyle.red, row=1)
    async def clear_btn_callback(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.edit_message(view=self)
        await self.command_handler.clear(interaction, send_response=True)

    @discord.ui.button(label= '#', style=BtnStyle.red, row=1)
    async def dc_btn_callback(self, interaction: discord.Interaction, _: discord.ui.Button):
        await interaction.response.edit_message(view = self)
        await self.command_handler.disconnect(interaction, send_response=True)

    @discord.ui.button(label= '≡', style=BtnStyle.grey, row=1)
    async def lyrics_btn_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        success = await self.command_handler.lyrics(interaction, send_response=False)
        if not success: return
        guild_bot = self.bot.get_bot_from_interaction(interaction)
        button.style = BtnStyle.green if guild_bot.show_lyrics else BtnStyle.grey
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label= '+', style=BtnStyle.blue, row=1)
    async def add_btn_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(UserListSelectModal())

    @discord.ui.button(label= 'S+', style=BtnStyle.blue, row=1)
    async def server_add_btn_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(ServerListSelectModal())
