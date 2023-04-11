import discord

from utils import BtnStyle


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
            button.style = BtnStyle.green if guild_bot.is_shuffled else BtnStyle.grey
            await interaction.response.edit_message(view=self)

    @discord.ui.button(label= '◁', style=BtnStyle.grey, row=0)
    async def previous_btn_callback(self, interaction: discord.Interaction, _: discord.ui.Button):
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
        await self.command_handler.skip(interaction, send_response=True)

    @discord.ui.button(label= '⭯', style=BtnStyle.grey, row=0)
    async def loop_btn_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        success = await self.command_handler.loop(interaction, send_response=False)
        if not success: return
        guild_bot = self.bot.get_bot_from_interaction(interaction)
        if guild_bot.is_looped:
            button.style = BtnStyle.green
        elif guild_bot.is_looped_single:
            button.style = BtnStyle.blue
        else:
            button.style = BtnStyle.grey
        await interaction.response.edit_message(view=self)

    # second row

    @discord.ui.button(label= '✖', style=BtnStyle.red, row=1)
    async def clear_btn_callback(self, interaction: discord.Interaction, _: discord.ui.Button):
        await self.command_handler.clear(interaction, send_response=True)

    @discord.ui.button(label= '#', style=BtnStyle.red, row=1)
    async def dc_btn_callback(self, interaction: discord.Interaction, _: discord.ui.Button):
        await self.command_handler.disconnect(interaction, send_response=True)

    @discord.ui.button(label= '≡', style=BtnStyle.grey, row=1)
    async def lyrics_btn_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        success = await self.command_handler.lyrics(interaction, send_response=False)
        if not success: return
        guild_bot = self.bot.get_bot_from_interaction(interaction)
        button.style = BtnStyle.green if guild_bot.show_lyrics else BtnStyle.grey
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label= '⯆', style=BtnStyle.grey, row=1)
    async def queue_btn_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        success = await self.command_handler.queue(interaction, send_response=False)
        if not success: return
        guild_bot = self.bot.get_bot_from_interaction(interaction)
        button.style = BtnStyle.green if guild_bot.short_queue else BtnStyle.grey
        await interaction.response.edit_message(view=self)

    @discord.ui.button(label= '⯅', style=BtnStyle.grey, row=1)
    async def history_btn_callback(self, interaction: discord.Interaction, button: discord.ui.Button):
        success = await self.command_handler.history(interaction, send_response=False)
        if not success: return
        guild_bot = self.bot.get_bot_from_interaction(interaction)
        button.style = BtnStyle.green if guild_bot.show_history else BtnStyle.grey
        await interaction.response.edit_message(view=self)
