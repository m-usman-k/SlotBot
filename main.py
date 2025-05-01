import discord, os
from discord.ext import commands

from dotenv import load_dotenv

from functions.database import *


load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")


bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())

@bot.event
async def on_ready():
    print(f"🟩 | Bot loaded as {bot.user.name}")

    setup_tables()
    print(f"🟩 | All tables setup")

    await bot.load_extension("extensions.Point")
    await bot.load_extension("extensions.Admin")
    await bot.load_extension("extensions.Ticket")
    print(f"🟩 | All extensions loaded")

    await bot.tree.sync()
    print(f"🟩 | Bot tree synced")


if __name__ == "__main__":
    bot.run(BOT_TOKEN)