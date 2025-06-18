import discord
from discord.ext import commands
from discord import app_commands

from config import *
from functions.display import *
from functions.database import *
from extensions.Point import is_admin, SlotDurationView  # Import both is_admin and SlotDurationView


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

    @app_commands.command(name="add-slot", description="Admin command to add a slot")
    async def add_slot(self, interaction: discord.Interaction, channel: discord.TextChannel, price_points: int, default_name: str):
        if not user_admin(id=interaction.user.id):
            return await user_forbidden(interaction=interaction)

        if add_slot(channel.id, price_points, default_name):
            # Get slot info for initial message
            slot_info = get_slot_info(channel.id)
            if slot_info:
                slot_durations = [(key, DURATION_CONFIG[key]) for key in DURATION_CONFIG]
                view = SlotDurationView(channel.id, slot_durations, self)
                await delete_all_messages(channel)
                await display_slot_available(channel, channel.id, slot_durations, view)
            await slot_added(interaction, channel, price_points, default_name)
        else:
            embed = discord.Embed(
                title="🟥 Failed to Add Slot",
                description="An error occurred while trying to add the slot. Please try again.",
                color=discord.Color.red()
            )
            await interaction.response.send_message(embed=embed)

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

    @app_commands.command(name="set-price", description="Set the price for a slot (Admin only)")
    @is_admin()
    async def set_price(self, interaction: discord.Interaction):
        slots = get_slots()
        if not slots:
            embed = discord.Embed(
                title="🟥 No Slots Found",
                description="No slots were found to set prices for.",
                color=discord.Color.red()
            )
            return await interaction.response.send_message(embed=embed)

        options = [
            discord.SelectOption(label=f"Slot {slot_id}", value=str(slot_id))
            for slot_id in slots
        ]

        class SlotSelect(discord.ui.Select):
            def __init__(self, outer):
                super().__init__(placeholder="Select a slot to set price for", options=options)
                self.outer = outer

            async def callback(self, select_interaction: discord.Interaction):
                if select_interaction.user.id != interaction.user.id:
                    return await select_interaction.response.send_message("This selection is not for you!", ephemeral=True)
                
                slot_id = int(self.values[0])
                slot_info = get_slot_info(slot_id)
                if not slot_info:
                    return await select_interaction.response.send_message("Failed to get slot information!", ephemeral=True)

                class PriceModal(discord.ui.Modal, title="Set Slot Price"):
                    def __init__(self, slot_id: int, current_price: int, outer):
                        super().__init__()
                        self.slot_id = slot_id
                        self.current_price = current_price
                        self.outer = outer
                        self.price = discord.ui.TextInput(
                            label="Points per hour",
                            placeholder=f"Current price: {current_price} points/hour",
                            required=True,
                            min_length=1,
                            max_length=5
                        )
                        self.add_item(self.price)

                    async def on_submit(self, interaction: discord.Interaction):
                        try:
                            new_price = int(self.price.value)
                            if new_price <= 0:
                                raise ValueError("Price must be positive")
                            
                            with db_connection() as conn:
                                cursor = conn.cursor()
                                cursor.execute(f"""
                                    UPDATE slots 
                                    SET points = {new_price}
                                    WHERE id = {self.slot_id}
                                """)
                            
                            # Update the channel message
                            channel = interaction.client.get_channel(self.slot_id)
                            if channel:
                                slot_durations = [(key, DURATION_CONFIG[key]) for key in DURATION_CONFIG]
                                view = SlotDurationView(self.slot_id, slot_durations, self.outer)
                                await delete_all_messages(channel)
                                await display_slot_available(channel, self.slot_id, slot_durations, view)
                            
                            await interaction.response.send_message(
                                embed=discord.Embed(
                                    title="✅ Price Updated",
                                    description=f"Slot {self.slot_id} price has been updated to {new_price} points/hour",
                                    color=discord.Color.green()
                                ),
                                ephemeral=True
                            )
                        except ValueError:
                            await interaction.response.send_message(
                                embed=discord.Embed(
                                    title="❌ Invalid Price",
                                    description="Please enter a valid positive number for the price.",
                                    color=discord.Color.red()
                                ),
                                ephemeral=True
                            )

                await select_interaction.response.send_modal(PriceModal(slot_id, slot_info[0], self.outer))

        class SlotSelectView(discord.ui.View):
            def __init__(self, outer):
                super().__init__()
                self.add_item(SlotSelect(outer))

        embed = discord.Embed(
            title="💰 Set Slot Price",
            description="Select a slot to set its price from the dropdown below.",
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, view=SlotSelectView(self))

    
async def setup(bot: commands.Bot):
    await bot.add_cog(Admin(bot=bot))