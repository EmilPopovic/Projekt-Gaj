import discord


class InteractionResponder:
    @staticmethod
    async def send(text: str,
                   interaction: discord.Interaction,
                   followup: bool = False,
                   fail: bool = False,
                   event: bool = False,
                   ephemeral: bool = True):
        if fail:
            title = 'Fail'
            color = discord.Color.from_rgb(242, 63, 67)
        elif event:
            title = 'Event'
            color = discord.Color.from_rgb(240, 178, 50)
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
