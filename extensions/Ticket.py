import discord
from discord.ext import commands
from discord import app_commands


class Ticket(commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot


async def setup(bot: commands.Bot):
    await bot.add_cog(Ticket(bot=bot))