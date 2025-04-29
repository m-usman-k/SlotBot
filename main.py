import discord, os
from discord.ext import commands

from dotenv import load_dotenv


load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")


bot = commands.Bot(command_prefix='!', intents=discord.Intents.all())


if __name__ == "__main__":
    bot.run(BOT_TOKEN)