import discord
from discord.ext import commands
from discord import app_commands

from functions.display import *
from functions.database import *
from config import SUPREME_USER  # Import SUPREME_USER from the config


class Admin(commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot

    @app_commands.command(name="points", description="User command to display points of users")
    async def points(self, interaction: discord.Interaction, user: discord.User = None):
        if user == None:
            user = interaction.user

        points = get_points(id=user.id)
        return await display_points(interaction=interaction, user=user, points=points)

    @app_commands.command(name="add-points", description="Admin command to add points to people")
    async def add_points(self, interaction: discord.Interaction, user: discord.User, points: int):
        if not user_admin(id=interaction.user.id):
            return await user_forbidden(interaction=interaction)
        
        if points <= 0:
            return await neg_number(interaction=interaction)
        
        if add_points(id=user.id, points=points):
            return await points_added(interaction=interaction, points=points, user=user)
        else:
            return await points_error(interaction=interaction)
        
    @app_commands.command(name="rem-points", description="Admin command to remove points from people")
    async def rem_points(self, interaction: discord.Interaction, user: discord.User, points: int):
        if not user_admin(id=interaction.user.id):
            return await user_forbidden(interaction=interaction)
        
        if points <= 0:
            return await neg_number(interaction=interaction)
        
        if add_points(id=user.id, points=-points):
            return await points_removed(interaction=interaction, points=points, user=user)
        else:
            return await points_error(interaction=interaction)
        

    @app_commands.command(name="add-admin", description="Supreme user command to add a user as an admin")
    async def add_admin(self, interaction: discord.Interaction, user: discord.User):
        if interaction.user.id != SUPREME_USER:  # Check if the user is the supreme user
            return await user_forbidden(interaction=interaction, ephemeral=True)

        if set_admin(id=user.id, is_admin=True):
            await admin_added(interaction=interaction, user=user)
        else:
            await admin_add_failed(interaction=interaction)

    @app_commands.command(name="rem-admin", description="Supreme user command to remove an admin")
    async def rem_admin(self, interaction: discord.Interaction):
        if interaction.user.id != SUPREME_USER:  # Check if the user is the supreme user
            return await user_forbidden(interaction=interaction, ephemeral=True)

        admins = get_admins()
        if not admins:
            return await no_admins_found(interaction=interaction)

        options = [
            discord.SelectOption(label=str(await self.bot.fetch_user(admin_id)), value=str(admin_id))
            for admin_id in admins
        ]

        async def callback(select_interaction: discord.Interaction):
            admin_id = int(select_interaction.data["values"][0])
            if set_admin(id=admin_id, is_admin=False):
                await admin_removed(interaction=select_interaction)
            else:
                await admin_remove_failed(interaction=select_interaction)

        await admin_selection_embed(interaction=interaction, options=options)

    @app_commands.command(name="add-slot", description="Admin command to add new slot")
    async def add_slot(self, interaction: discord.Interaction, channel: discord.TextChannel, default_name: str):
        if not user_admin(id=interaction.user.id):
            return await user_forbidden(interaction=interaction)
        
        price_points = 1

        if price_points <= 0:
            return await neg_number(interaction=interaction)

        if add_slot(channel_id=channel.id, price_points=price_points, default_name=default_name):
            await slot_added(interaction=interaction, channel=channel, price_points=price_points, default_name=default_name)
        else:
            return await points_error(interaction=interaction)

    @app_commands.command(name="rem-slot", description="Admin command to remove a slot")
    async def rem_slot(self, interaction: discord.Interaction):
        if not user_admin(id=interaction.user.id):
            return await user_forbidden(interaction=interaction)

        slots = get_slots()
        if not slots:
            embed = discord.Embed(
                title="🟥 No Slots Found",
                description="No slots were found to remove.",
                color=discord.Color.red()
            )
            return await interaction.response.send_message(embed=embed)

        options = [
            discord.SelectOption(label=f"Slot {slot_id}", value=str(slot_id))
            for slot_id in slots
        ]

        class SlotSelect(discord.ui.Select):
            def __init__(self, outer):
                super().__init__(placeholder="Select a slot to remove", options=options)
                self.outer = outer

            async def callback(self, select_interaction: discord.Interaction):
                if select_interaction.user.id != interaction.user.id:
                    return await select_interaction.response.send_message("This selection is not for you!", ephemeral=True)
                
                slot_id = int(self.values[0])
                if remove_slot(channel_id=slot_id):
                    channel = await self.outer.bot.fetch_channel(slot_id)
                    await slot_removed(interaction=select_interaction, channel=channel)
                else:
                    embed = discord.Embed(
                        title="🟥 Failed to Remove Slot",
                        description="An error occurred while trying to remove the slot. Please try again.",
                        color=discord.Color.red()
                    )
                    await select_interaction.response.send_message(embed=embed, ephemeral=True)

        class SlotSelectView(discord.ui.View):
            def __init__(self, outer):
                super().__init__()
                self.add_item(SlotSelect(outer))

        embed = discord.Embed(
            title="🛠️ Slot Removal",
            description="Select a slot to remove from the dropdown below.",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, view=SlotSelectView(self))

    
async def setup(bot: commands.Bot):
    await bot.add_cog(Admin(bot=bot))