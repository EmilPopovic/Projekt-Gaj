from discord.ext import commands


class help_cog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.help_message = '''
```
Komande:
!help - ispisuje sve komande
!p <ime pjesme> - traži pjesmu na youtubeu i pušta ju u glasovni kanal, nastavlja ako pauzirano
!q - prikazuje sadašnji popis
!h - prikazuje popis puštenih pjesama
!skip - preskače pjesmu
!clear - prestaje i briše popis
!leave - bot izlazi iz glasovnog kanala
!pause - pauzira sadašnju pjesmu, nastavlja ako pauzirano
!resume - nastavlja ako pauzirano
!dq - briše sve odgovore na !q poruke
!dh - briše sve odgovore na !h poruke
```
'''

    
    @commands.command(name='help', help='ispisuje sve komande')
    async def help(self, ctx):
        await ctx.channel.purge(limit=1)
        await ctx.send(self.help_message)