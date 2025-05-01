import discord
from discord.ext import commands
from discord import app_commands
import time
import asyncio

from functions.display import *
from functions.database import *
from config import DURATION_CONFIG, POINTS_PRICES, TICKET_CATEGORY_ID, TICKET_NAME_FORMAT, TICKET_ADMIN_ROLES

class SlotPurchaseSelect(discord.ui.Select):
    def __init__(self, slots: list):
        options = [
            discord.SelectOption(
                label=f"Slot {slot_id}",
                description=name,
                value=str(slot_id)
            ) for slot_id, _, name, _ in slots
        ]
        super().__init__(
            placeholder="Select a slot to purchase...",
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message(
            embed=discord.Embed(
                title="⏱️ Select Duration",
                description="Choose how long you want to rent this slot:",
                color=discord.Color.blue()
            ),
            view=SlotDurationView(int(self.values[0])),
            ephemeral=True
        )

class SlotDurationSelect(discord.ui.Select):
    def __init__(self, slot_id: int):
        self.slot_id = slot_id
        options = [
            discord.SelectOption(
                label=name,
                value=key
            ) for key, (_, name) in DURATION_CONFIG.items()
        ]
        super().__init__(
            placeholder="Select duration...",
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        duration = self.values[0]
        
        # Get slot information
        slot_info = get_slot_info(self.slot_id)
        if not slot_info:
            await slot_purchase_failed(interaction, "Invalid slot ID!")
            return
        
        points_per_duration, default_name, occupied, occupied_by, occupied_till = slot_info
        
        # Check if slot is available
        if occupied:
            await slot_purchase_failed(interaction, "This slot is currently occupied!")
            return

        # Calculate cost
        duration_seconds, duration_name = DURATION_CONFIG[duration]
        points_cost = int(points_per_duration * (duration_seconds / 3600))  # Cost per hour

        # Try to purchase the slot
        if purchase_slot(self.slot_id, interaction.user.id, duration_seconds, points_cost):
            await slot_purchase_success(interaction, self.slot_id, duration_name, points_cost)
        else:
            await slot_purchase_failed(interaction, "You don't have enough points or an error occurred!")

class SlotDurationView(discord.ui.View):
    def __init__(self, slot_id: int):
        super().__init__()
        self.add_item(SlotDurationSelect(slot_id))

class SlotPurchaseView(discord.ui.View):
    def __init__(self, slots: list):
        super().__init__()
        self.add_item(SlotPurchaseSelect(slots))

class Point(commands.Cog):
    def __init__(self, bot):
        super().__init__()
        self.bot = bot
        create_ticket_tables()
        self.slot_check_task = self.bot.loop.create_task(self.check_slot_times())

    def cog_unload(self):
        if self.slot_check_task:
            self.slot_check_task.cancel()

    async def check_slot_times(self):
        await self.bot.wait_until_ready()
        while not self.bot.is_closed():
            try:
                # Get all slots
                slots = get_slots()
                current_time = int(time.time())
                
                for slot_id in slots:
                    slot_info = get_slot_info(slot_id)
                    if not slot_info:
                        continue
                        
                    points_per_duration, default_name, occupied, occupied_by, occupied_till = slot_info
                    
                    # Check if slot is occupied and time has expired
                    if occupied and occupied_till and current_time >= occupied_till:
                        # Get the channel
                        channel = self.bot.get_channel(slot_id)
                        if channel:
                            try:
                                # Reset the channel name
                                await channel.edit(name=default_name)
                                
                                # Update database
                                with db_connection() as conn:
                                    cursor = conn.cursor()
                                    cursor.execute(f"""
                                        UPDATE slots 
                                        SET occupied = 0, 
                                            occupied_by = 0, 
                                            occupied_till = 0 
                                        WHERE id = {slot_id}
                                    """)
                            except Exception as e:
                                print(f"Error resetting slot {slot_id}: {e}")
                
            except Exception as e:
                print(f"Error in slot check loop: {e}")
            
            await asyncio.sleep(60)  # Check every minute

    @app_commands.command(name="points-shop", description="Open the points shop")
    async def points_shop(self, interaction: discord.Interaction):
        await display_points_shop(interaction, self)

    async def create_purchase_ticket(self, interaction: discord.Interaction):
        # Get the category for tickets
        category = self.bot.get_channel(TICKET_CATEGORY_ID)
        if not category:
            await slot_purchase_failed(interaction, "Ticket system is not properly configured!")
            return

        # Create the ticket channel
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.guild.me: discord.PermissionOverwrite(read_messages=True),
            interaction.user: discord.PermissionOverwrite(read_messages=True)
        }
        
        # Add admin role overwrites
        for role_id in TICKET_ADMIN_ROLES:
            role = interaction.guild.get_role(role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True)

        channel = await category.create_text_channel(
            name=TICKET_NAME_FORMAT.format(user_name=interaction.user.name, ticket_id="temp"),
            overwrites=overwrites
        )

        # Create ticket in database
        ticket_id = create_ticket(channel.id, interaction.user.id)
        if not ticket_id:
            await channel.delete()
            await slot_purchase_failed(interaction, "Failed to create ticket!")
            return

        # Update channel name with ticket ID
        await channel.edit(name=TICKET_NAME_FORMAT.format(user_name=interaction.user.name, ticket_id=ticket_id))

        # Get crypto addresses
        addresses = get_crypto_addresses()
        if not addresses:
            await channel.delete()
            await slot_purchase_failed(interaction, "No payment methods available!")
            return

        # Send initial message
        embed = discord.Embed(
            title="🎫 Point Purchase Ticket",
            description="Welcome to your point purchase ticket! Please follow these steps:\n\n"
                       "1. Select your desired cryptocurrency from the dropdown menu\n"
                       "2. Send the exact amount to the provided address\n"
                       "3. Click 'Finish' and provide your transaction ID\n\n"
                       "Available Points Packages:",
            color=discord.Color.blue()
        )

        for points, price in POINTS_PRICES.items():
            embed.add_field(
                name=f"{points} Points",
                value=f"Price: {price}€",
                inline=True
            )

        await channel.send(embed=embed, view=TicketView(addresses))
        await interaction.response.send_message(
            embed=discord.Embed(
                title="✅ Ticket Created",
                description=f"Your ticket has been created: {channel.mention}",
                color=discord.Color.green()
            ),
            ephemeral=True
        )

    @app_commands.command(name="buy-slot", description="Buy a slot for a specific duration")
    async def buy_slot(self, interaction: discord.Interaction):
        # Check if user already has a slot
        current_slot = get_user_slot(interaction.user.id)
        if current_slot:
            return await slot_purchase_failed(interaction, "You already have an active slot!")

        # Get available slots
        slots = get_slots()
        if not slots:
            return await slot_purchase_failed(interaction, "No slots are currently available!")
        
        slot_info = []
        for slot_id in slots:
            info = get_slot_info(slot_id)
            if info:
                slot_info.append((slot_id, *info[:3]))

        await interaction.response.send_message(
            embed=discord.Embed(
                title="🎰 Purchase Slot",
                description="Select a slot to purchase:",
                color=discord.Color.blue()
            ),
            view=SlotPurchaseView(slot_info),
            ephemeral=True
        )

    @app_commands.command(name="check-slots", description="Check available slots")
    async def check_slots(self, interaction: discord.Interaction):
        slots = get_slots()
        if not slots:
            return await slot_purchase_failed(interaction, "No slots are currently available!")
        
        slot_info = []
        for slot_id in slots:
            info = get_slot_info(slot_id)
            if info:
                slot_info.append((slot_id, *info[:3]))  # Include id, points, name, and occupied status
        
        await display_available_slots(interaction, slot_info)

    @app_commands.command(name="slot-info", description="Get information about slots")
    async def slot_info(self, interaction: discord.Interaction):
        slots = get_slots()
        if not slots:
            return await slot_purchase_failed(interaction, "No slots are currently available!")
        
        slot_info = []
        for slot_id in slots:
            info = get_slot_info(slot_id)
            if info:
                slot_info.append((slot_id, *info[:3]))
        
        await interaction.response.send_message(
            embed=discord.Embed(
                title="🎰 Slot Information",
                description="Select a slot from the dropdown menu to view its details:",
                color=discord.Color.blue()
            ),
            view=SlotInfoView(slot_info)
        )

async def setup(bot: commands.Bot):
    await bot.add_cog(Point(bot=bot))