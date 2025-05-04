import discord
from discord.ext import commands

from functions.database import *
from functions.blockchain import BlockchainVerifier

async def user_forbidden(interaction: discord.Interaction, ephemeral: bool = False):
    embed = discord.Embed(
        title="🟥 Forbidden",
        description="You do not have permission to perform this action.",
        color=discord.Color.red()
    )
    await interaction.response.send_message(embed=embed, ephemeral=ephemeral)

async def neg_number(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🟥 Negative Number",
        description="The number provided must be positive.",
        color=discord.Color.red()
    )
    await interaction.response.send_message(embed=embed)

async def points_added(interaction: discord.Interaction, points: int, user: discord.User):
    embed = discord.Embed(
        title="🎉 Points Awarded!",
        description=f"**{points} points** have been added to {user.mention} by {interaction.user.mention}.",
        color=discord.Color.green()
    )
    embed.set_footer(text=f"Awarded by {interaction.user.name}", icon_url=interaction.user.display_avatar.url)
    await interaction.response.send_message(embed=embed)

async def points_removed(interaction: discord.Interaction, points: int, user: discord.User):
    embed = discord.Embed(
        title="🥲 Points Removed!",
        description=f"**{points} points** have been removed from {user.mention} by {interaction.user.mention}.",
        color=discord.Color.red()
    )
    embed.set_footer(text=f"Removed by {interaction.user.name}", icon_url=interaction.user.display_avatar.url)
    await interaction.response.send_message(embed=embed)

async def points_error(interaction: discord.Interaction):
    embed = discord.Embed(
        title="⚠️ Action Unsuccessful",
        description="The attempt to add/remove points was not successful.",
        color=discord.Color.red()
    )
    embed.set_footer(text="Please try again or contact support if the issue continues.")
    await interaction.response.send_message(embed=embed)

async def display_points(interaction: discord.Interaction, user: discord.User, points: int):
    embed = discord.Embed(
        title="🎯 User Points",
        description=f"{user.mention} currently has **{points} points**.",
        color=discord.Color.blue()
    )
    embed.set_footer(text=f"Use /points to check yours")
    await interaction.response.send_message(embed=embed)

async def admin_added(interaction: discord.Interaction, user: discord.User):
    embed = discord.Embed(
        title="✅ Admin Added",
        description=f"{user.mention} has been successfully added as an admin.",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed)

async def admin_add_failed(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🟥 Failed to Add Admin",
        description="An error occurred while trying to add the admin. Please try again.",
        color=discord.Color.red()
    )
    await interaction.response.send_message(embed=embed)

async def no_admins_found(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🟥 No Admins Found",
        description="No admins were found to remove.",
        color=discord.Color.red()
    )
    await interaction.response.send_message(embed=embed)

async def admin_removed(interaction: discord.Interaction):
    embed = discord.Embed(
        title="✅ Admin Removed",
        description="The admin has been successfully removed.",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed)

async def admin_remove_failed(interaction: discord.Interaction):
    embed = discord.Embed(
        title="🟥 Failed to Remove Admin",
        description="An error occurred while trying to remove the admin. Please try again.",
        color=discord.Color.red()
    )
    await interaction.response.send_message(embed=embed)

async def admin_selection_embed(interaction: discord.Interaction, options: list[discord.SelectOption]):
    embed = discord.Embed(
        title="🛠️ Admin Selection",
        description="Select an admin to remove from the dropdown below.",
        color=discord.Color.blue()
    )
    view = discord.ui.View()
    view.add_item(discord.ui.Select(placeholder="Select an admin to remove", options=options))
    await interaction.response.send_message(embed=embed, view=view)

async def slot_added(interaction: discord.Interaction, channel: discord.TextChannel, price_points: int, default_name: str):
    embed = discord.Embed(
        title="✅ Slot Added",
        description=f"Slot **{channel.mention}** has been added with a price of **{price_points} points** and default name **{default_name}**.",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed)

async def slot_selection_embed(interaction: discord.Interaction, options: list[discord.SelectOption]):
    embed = discord.Embed(
        title="🛠️ Slot Selection",
        description="Select a slot to remove from the dropdown below.",
        color=discord.Color.blue()
    )
    view = discord.ui.View()
    view.add_item(discord.ui.Select(placeholder="Select a slot to remove", options=options))
    await interaction.response.send_message(embed=embed, view=view)

async def slot_removed(interaction: discord.Interaction, channel: discord.TextChannel):
    embed = discord.Embed(
        title="✅ Slot Removed",
        description=f"Slot **{channel.mention}** has been successfully removed.",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed)

async def slot_purchase_success(interaction: discord.Interaction, slot_id: int, duration: str, points: int):
    embed = discord.Embed(
        title="✅ Slot Purchased Successfully",
        description=f"You have successfully purchased Slot {slot_id} for {duration}.\nCost: {points} points",
        color=discord.Color.green()
    )
    await interaction.response.send_message(embed=embed)

async def slot_purchase_failed(interaction: discord.Interaction, reason: str, ephemeral: bool = False):
    embed = discord.Embed(
        title="❌ Slot Purchase Failed",
        description=reason,
        color=discord.Color.red()
    )
    await interaction.response.send_message(embed=embed, ephemeral=ephemeral)

async def payment_ticket_created(interaction: discord.Interaction, ticket_id: int, points: int, price: float, addresses: dict):
    embed = discord.Embed(
        title="💰 Payment Ticket Created",
        description=f"Please send {price}$ worth of crypto to one of the following addresses:",
        color=discord.Color.blue()
    )
    
    for crypto, address in addresses.items():
        embed.add_field(name=f"{crypto} Address", value=f"`{address}`", inline=False)
    
    embed.add_field(
        name="Instructions", 
        value="1. Send the exact amount to any of the addresses above\n2. Click 'Finish' after sending\n3. Wait for confirmation", 
        inline=False
    )
    
    embed.set_footer(text=f"Ticket ID: {ticket_id} | Amount: {points} points")
    await interaction.response.send_message(embed=embed)

async def display_available_slots(interaction: discord.Interaction, slots: list):
    embed = discord.Embed(
        title="🎰 Available Slots",
        description="Here are the available slots you can purchase:",
        color=discord.Color.blue()
    )
    
    for slot in slots:
        slot_id, points, name, occupied = slot
        status = "🔴 Occupied" if occupied else "🟢 Available"
        embed.add_field(
            name=f"Slot {slot_id} - {name}",
            value=f"Status: {status}",
            inline=False
        )
    
    await interaction.response.send_message(embed=embed)

async def display_slot_durations(interaction: discord.Interaction, slot_id: int, durations: list):
    embed = discord.Embed(
        title=f"⏱️ Available Durations for Slot <#{slot_id}>",
        description="Select how long you want to rent this slot:",
        color=discord.Color.blue()
    )
    
    for duration, points in durations:
        embed.add_field(
            name=duration,
            value=f"Cost: {points} points",
            inline=True
        )
    
    await interaction.response.send_message(embed=embed)

class TicketNameModal(discord.ui.Modal):
    def __init__(self, ticket_channel):
        super().__init__(title="Rename Ticket")
        self.ticket_channel = ticket_channel
        self.name = discord.ui.TextInput(
            label="New Ticket Name",
            placeholder="Enter new ticket name...",
            required=True,
            max_length=100
        )
        self.add_item(self.name)

    async def on_submit(self, interaction: discord.Interaction):
        await self.ticket_channel.edit(name=self.name.value)
        await interaction.response.send_message(embed=discord.Embed(
            title="✅ Ticket Renamed",
            description=f"Ticket has been renamed to {self.name.value}",
            color=discord.Color.green()
        ))

class TransactionModal(discord.ui.Modal):
    def __init__(self, crypto_type: str, points_amount: int, price_eur: float):
        super().__init__(title="Transaction Verification")
        self.crypto_type = crypto_type
        self.points_amount = points_amount
        self.price_eur = price_eur
        
        self.tx_id = discord.ui.TextInput(
            label="Transaction ID",
            placeholder="Enter your transaction ID...",
            required=True
        )
        self.add_item(self.tx_id)

    async def on_submit(self, interaction: discord.Interaction):
        from functions.database import is_transaction_id_used, save_trx_id, add_points
        
        # Get ticket ID from channel name
        ticket_id = int(interaction.channel.name.split('-')[-1])
        
        # Check if transaction ID is already used
        if is_transaction_id_used(self.tx_id.value):
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ Transaction Already Used",
                    description="This transaction ID has already been used for another ticket.",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )
            return
        
        # Verify transaction
        is_valid = await BlockchainVerifier.verify_transaction(
            self.crypto_type,
            self.tx_id.value,
            self.price_eur
        )
        
        if is_valid:
            # Add points to user
            if add_points(id=interaction.user.id, points=self.points_amount):
                # Save transaction ID to prevent reuse
                if not save_trx_id(self.tx_id.value):
                    await interaction.response.send_message(
                        embed=discord.Embed(
                            title="❌ Error",
                            description="Failed to store transaction ID. Please contact an administrator.",
                            color=discord.Color.red()
                        )
                    )
                    return

                # Send success message to user
                await interaction.response.send_message(
                    embed=discord.Embed(
                        title="✅ Payment Verified",
                        description=f"Your payment has been verified and {self.points_amount} points have been added to your account! The ticket will be closed shortly.",
                        color=discord.Color.green()
                    )
                )
                
                import asyncio
                await asyncio.sleep(10)  # Wait for 10 seconds before deleting the ticket
                await interaction.channel.delete()
            else:
                await interaction.response.send_message(
                    embed=discord.Embed(
                        title="❌ Error",
                        description="Failed to add points to your account. Please contact an administrator.",
                        color=discord.Color.red()
                    )
                )
        else:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ Invalid Transaction",
                    description="The transaction ID you provided could not be verified. Please check and try again.",
                    color=discord.Color.red()
                )
            )

class PointPurchaseView(discord.ui.View):
    def __init__(self, cog):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(label="Create Ticket", style=discord.ButtonStyle.primary, emoji="🎫")
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.cog.create_purchase_ticket(interaction)

async def display_points_shop(interaction: discord.Interaction, cog):
    embed = discord.Embed(
        title="🏪 Points Shop",
        description="Welcome to the Points Shop! Click the button below to create a purchase ticket.",
        color=discord.Color.blue()
    )
    
    # Add points packages
    from config import POINTS_PRICES
    for points, price in POINTS_PRICES.items():
        embed.add_field(
            name=f"{points} Points",
            value=f"Price: {price}$",
            inline=True
        )
    
    embed.set_footer(text="Click the button below to start your purchase")
    await interaction.response.send_message(embed=embed, view=PointPurchaseView(cog))

class CryptoSelect(discord.ui.Select):
    def __init__(self, addresses: dict):
        self.row = 0
        options = [
            discord.SelectOption(
                label=crypto_type,
                description=f"Pay with {crypto_type}",
                value=crypto_type
            ) for crypto_type in addresses.keys()
        ]
        super().__init__(
            placeholder="Select payment method...",
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        self.view.selected_crypto = self.values[0]  # Store the selected crypto
        await display_crypto_address(interaction, self.values[0])

class PointsPackageSelect(discord.ui.Select):
    def __init__(self):
        self.row = 0
        from config import POINTS_PRICES
        options = [
            discord.SelectOption(
                label=f"{points} Points",
                description=f"{price}$",
                value=str(points)
            ) for points, price in POINTS_PRICES.items()
        ]
        super().__init__(
            placeholder="Select points package...",
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        from config import POINTS_PRICES
        points = int(self.values[0])
        price = POINTS_PRICES[points]
        self.view.selected_points = points
        self.view.selected_price = price
        await interaction.response.send_message(
            embed=discord.Embed(
                title="✅ Points Package Selected",
                description=f"You selected **{points} points** for **{price}$**.",
                color=discord.Color.green()
            ),
            ephemeral=True
        )

class TicketView(discord.ui.View):
    def __init__(self, addresses: dict):
        super().__init__(timeout=None)
        self.add_item(PointsPackageSelect())
        self.add_item(CryptoSelect(addresses))
        self.selected_crypto = None
        self.selected_points = None
        self.selected_price = None

    @discord.ui.button(label="Rename Ticket", style=discord.ButtonStyle.secondary, emoji="✏️", row=2)
    async def rename_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        modal = TicketNameModal(interaction.channel)
        await interaction.response.send_modal(modal)

    @discord.ui.button(label="Close Ticket", style=discord.ButtonStyle.danger, emoji="🔒", row=2)
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not user_admin(interaction.user.id):
            await user_forbidden(interaction)
            return
        await interaction.channel.delete()

    @discord.ui.button(label="Finish", style=discord.ButtonStyle.success, emoji="✅", row=2)
    async def finish_payment(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.selected_crypto:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ Error",
                    description="Please select a payment method first!",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )
            return
            
        if not self.selected_points or not self.selected_price:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ Error",
                    description="Please select a points package first!",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )
            return
            
        modal = TransactionModal(self.selected_crypto, self.selected_points, self.selected_price)
        await interaction.response.send_modal(modal)

async def display_crypto_address(interaction: discord.Interaction, crypto_type: str):
    from functions.database import get_crypto_addresses
    addresses = get_crypto_addresses()
    
    if crypto_type not in addresses:
        await interaction.response.send_message(
            embed=discord.Embed(
                title="❌ Error",
                description="Invalid cryptocurrency selected.",
                color=discord.Color.red()
            ),
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title=f"💸 {crypto_type} Payment Address",
        description=f"Please send the exact amount to this address:",
        color=discord.Color.blue()
    )
    embed.add_field(name="Address", value=f"`{addresses[crypto_type]}`", inline=False)
    embed.add_field(
        name="Instructions",
        value="1. Send the exact amount to the address above\n2. Wait for 1 confirmation\n3. Click 'Finish' and provide your transaction ID",
        inline=False
    )
    await interaction.response.send_message(embed=embed, ephemeral=True)

class SlotInfoSelect(discord.ui.Select):
    def __init__(self, slots: list):
        options = [
            discord.SelectOption(
                label=f"Slot {slot_id}",
                description=name,
                value=str(slot_id)
            ) for slot_id, _, name, _ in slots
        ]
        super().__init__(
            placeholder="Select a slot to view info...",
            options=options
        )

    async def callback(self, interaction: discord.Interaction):
        from functions.database import get_slot_info
        slot_id = int(self.values[0])
        slot_info = get_slot_info(slot_id)
        
        if not slot_info:
            await slot_purchase_failed(interaction, "Failed to get slot information!")
            return
            
        points_per_duration = slot_info[0]
        from config import DURATION_CONFIG
        durations = []
        for duration_key, duration_data in DURATION_CONFIG.items():  # Correctly access nested dictionary
            seconds = duration_data["seconds"]
            name = duration_data["name"]
            points = int(points_per_duration * (seconds / 3600))
            durations.append((name, points))
        
        await display_slot_durations(interaction, slot_id, durations)

class SlotInfoView(discord.ui.View):
    def __init__(self, slots: list):
        super().__init__()
        self.add_item(SlotInfoSelect(slots))

async def delete_all_messages(channel: discord.TextChannel):
    async for msg in channel.history(limit=None):
        await msg.delete()

async def display_slot_available(channel: discord.TextChannel, slot_id: int, durations: list, view: discord.ui.View):
    await delete_all_messages(channel)
    embed = discord.Embed(
        title=f"Slot {slot_id} - Available",
        description="This Slot is currently available, you can buy it by using the Select Menu below.",
        color=discord.Color.blue()
    )
    await channel.send(embed=embed, view=view)  # Attach the persistent view

async def display_slot_claimed(channel: discord.TextChannel, slot_id: int, username: str, pings_left: int, available_until: str, owner_id: int, view: discord.ui.View):
    await delete_all_messages(channel)
    embed = discord.Embed(
        title=f"Slot {slot_id} - {username}",
        description="No Shop setup yet",
        color=discord.Color.purple()
    )
    info_embed = discord.Embed(
        title="Slot Information",
        description=f"**Pings Left - {pings_left}**\nSlot available {available_until}",
        color=discord.Color.blue()
    )
    await channel.send(embed=embed)
    await channel.send(embed=info_embed, view=view)

async def display_slot_setup(channel: discord.TextChannel, view: discord.ui.View):
    embed = discord.Embed(
        title="Slot Setup",
        description="Setup your Slot by using the menu below.",
        color=discord.Color.blue()
    )
    await channel.send(embed=embed, view=view)

async def display_slot_setup_options(channel: discord.TextChannel, view: discord.ui.View):
    await channel.send(view=view)

async def display_slot_ping(channel: discord.TextChannel, user: discord.User):
    await channel.send(f"@everyone Pinged by {user.mention}")


