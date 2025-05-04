import discord
from discord.ext import commands
from discord import app_commands
import time
import asyncio
from discord.app_commands import CheckFailure

from functions.display import *
from functions.database import *
from config import DURATION_CONFIG, POINTS_PRICES, TICKET_CATEGORY_ID, TICKET_NAME_FORMAT, TICKET_ADMIN_ROLES, SLOT_CONFIG

def is_admin():
    async def predicate(interaction: discord.Interaction) -> bool:
        if user_admin(interaction.user.id):
            return True
        raise CheckFailure("You do not have the required permissions to run this command.")
    return app_commands.check(predicate)

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
        slot_id = int(self.values[0])
        from config import DURATION_CONFIG
        slot_durations = [(key, DURATION_CONFIG[key]) for key in DURATION_CONFIG]  # Prepare slot durations
        await interaction.response.send_message(
            embed=discord.Embed(
                title="⏱️ Select Duration",
                description="Choose how long you want to rent this slot:",
                color=discord.Color.blue()
            ),
            view=SlotDurationView(slot_id, slot_durations, self.view.cog),  # Pass required arguments
            ephemeral=True
        )

class SlotDurationSelect(discord.ui.Select):
    def __init__(self, slot_id: int, slot_durations: list):
        self.slot_id = slot_id
        options = [
            discord.SelectOption(
                label=duration["name"],
                description=f"Buy {duration['name']} for {duration['points']} Points",
                value=key
            ) for key, duration in slot_durations
        ]
        super().__init__(placeholder="Duration you want to buy", options=options)

    async def callback(self, interaction: discord.Interaction):
        try:
            # Enforce one slot per user
            current_slot = get_user_slot(interaction.user.id)
            if current_slot:
                await interaction.response.send_message(
                    embed=discord.Embed(
                        title="❌ Slot Purchase Failed",
                        description="You already have an active slot!",
                        color=discord.Color.red()
                    ),
                    ephemeral=True
                )
                return
            duration = self.values[0]
            slot_info = get_slot_info(self.slot_id)
            if not slot_info:
                await slot_purchase_failed(interaction, "Invalid slot ID!", ephemeral=True)
                return
            points_per_duration, default_name, occupied, occupied_by, occupied_till, pings_left = slot_info
            if occupied:
                await slot_purchase_failed(interaction, "This slot is currently occupied!", ephemeral=True)
                return
            duration_info = DURATION_CONFIG[duration]
            duration_seconds = duration_info["seconds"]
            points_cost = duration_info["points"]
            if purchase_slot(self.slot_id, interaction.user.id, duration_seconds, points_cost):
                await self.view.display_claimed(interaction, self.slot_id, interaction.user)
            else:
                await interaction.response.send_message(
                    embed=discord.Embed(
                        title="❌ Slot Purchase Failed",
                        description="You don't have enough points or an error occurred!",
                        color=discord.Color.red()
                    ),
                    ephemeral=True
                )
        except Exception as e:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ Error",
                    description=f"An error occurred: {e}",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )

class SlotDurationView(discord.ui.View):
    def __init__(self, slot_id: int, slot_durations: list, cog):
        super().__init__(timeout=None)  # Make the view persistent
        self.add_item(SlotDurationSelect(slot_id, slot_durations))
        self.cog = cog

    async def display_claimed(self, interaction, slot_id, user):
        await self.cog.display_claimed(interaction, slot_id, user)

class SlotClaimedView(discord.ui.View):
    def __init__(self, owner_id, cog, slot_id, username, available_until, claimed_message=None, claimed_embed=None, info_message=None):
        super().__init__(timeout=None)  # Make the view persistent
        self.owner_id = owner_id
        self.cog = cog
        self.slot_id = slot_id
        self.username = username
        self.available_until = available_until
        self.claimed_message = claimed_message
        self.claimed_embed = claimed_embed
        self.info_message = info_message

    @discord.ui.button(label="Setup Slot", style=discord.ButtonStyle.primary)
    async def setup_slot(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            if interaction.user.id != self.owner_id:
                await user_forbidden(interaction, ephemeral=True)
                return
            setup_embed = discord.Embed(
                title="Slot Setup",
                description="Setup your Slot by using the menu below.",
                color=discord.Color.blue()
            )
            view = SetupOptionsView(setup_embed, self.claimed_message)
            await interaction.response.send_message(embed=setup_embed, view=view, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ Error",
                    description=f"An error occurred: {e}",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )

    @discord.ui.button(label="Use Ping", style=discord.ButtonStyle.secondary)
    async def use_ping(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            if interaction.user.id != self.owner_id:
                await user_forbidden(interaction, ephemeral=True)
                return
            # Get current pings from database
            slot_info = get_slot_info(self.slot_id)
            if not slot_info:
                return
            pings_left = slot_info[5]
            if pings_left <= 0:
                await interaction.response.send_message(
                    embed=discord.Embed(
                        title="❌ No Pings Left",
                        description="You have used all your pings for this slot.",
                        color=discord.Color.red()
                    ),
                    ephemeral=True
                )
                return
            # Update pings in database
            update_slot_pings(self.slot_id, pings_left - 1)
            # Update info embed
            info_embed = discord.Embed(
                title="Slot Information",
                description=f"**Pings Left - {pings_left - 1}**\nSlot available {self.available_until}",
                color=discord.Color.blue()
            )
            await self.info_message.edit(embed=info_embed, view=self)
            # Send ping message with embed
            ping_embed = discord.Embed(
                title="Ping Used",
                description=f"{interaction.user.mention} used a Ping and now has {pings_left - 1} Pings left",
                color=discord.Color.green()
            )
            await interaction.channel.send(content="@everyone", embed=ping_embed)
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="✅ Ping Sent",
                    description="Everyone has been pinged!",
                    color=discord.Color.green()
                ),
                ephemeral=True
            )
        except Exception as e:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ Error",
                    description=f"An error occurred: {e}",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )

class SetupOptionsSelect(discord.ui.Select):
    def __init__(self, parent_view):
        options = [
            discord.SelectOption(label="Set Description", description="Set the Description of the Shop Ticket Embed.", value="desc"),
            discord.SelectOption(label="Set Footer", description="Set the Footer of the Shop Ticket Embed.", value="footer"),
            discord.SelectOption(label="Set Color", description="Set the Color of the Shop Ticket Embed.", value="color"),
        ]
        super().__init__(placeholder="Choose The Action To Perform", options=options)
        self.parent_view = parent_view
    async def callback(self, interaction: discord.Interaction):
        if self.values[0] == "desc":
            await interaction.response.send_modal(DescriptionModal(self.parent_view, self.parent_view.claimed_message))
        elif self.values[0] == "footer":
            await interaction.response.send_modal(FooterModal(self.parent_view, self.parent_view.claimed_message))
        elif self.values[0] == "color":
            await interaction.response.send_modal(ColorModal(self.parent_view, self.parent_view.claimed_message))

class SetupOptionsView(discord.ui.View):
    def __init__(self, embed, claimed_message):
        super().__init__(timeout=None)
        self.embed = embed
        self.claimed_message = claimed_message
        self.add_item(SetupOptionsSelect(self))

class DescriptionModal(discord.ui.Modal, title="Set Description"):
    def __init__(self, parent_view, claimed_message):
        super().__init__()
        self.parent_view = parent_view
        self.claimed_message = claimed_message
        self.desc = discord.ui.TextInput(label="New Description", style=discord.TextStyle.paragraph, required=True)
        self.add_item(self.desc)
    async def on_submit(self, interaction: discord.Interaction):
        embed = self.parent_view.embed
        embed.description = self.desc.value
        await self.claimed_message.edit(embed=embed)
        await interaction.response.send_message("Description updated!", ephemeral=True)

class FooterModal(discord.ui.Modal, title="Set Footer"):
    def __init__(self, parent_view, claimed_message):
        super().__init__()
        self.parent_view = parent_view
        self.claimed_message = claimed_message
        self.footer = discord.ui.TextInput(label="New Footer", style=discord.TextStyle.short, required=True)
        self.add_item(self.footer)
    async def on_submit(self, interaction: discord.Interaction):
        embed = self.parent_view.embed
        embed.set_footer(text=self.footer.value)
        await self.claimed_message.edit(embed=embed)
        await interaction.response.send_message("Footer updated!", ephemeral=True)

class ColorModal(discord.ui.Modal, title="Set Color"):
    def __init__(self, parent_view, claimed_message):
        super().__init__()
        self.parent_view = parent_view
        self.claimed_message = claimed_message
        self.color = discord.ui.TextInput(label="New Color (hex, e.g. #7289da)", style=discord.TextStyle.short, required=True)
        self.add_item(self.color)
    async def on_submit(self, interaction: discord.Interaction):
        embed = self.parent_view.embed
        try:
            embed.color = discord.Color(int(self.color.value.replace('#', ''), 16))
            await self.claimed_message.edit(embed=embed)
            await interaction.response.send_message("Color updated!", ephemeral=True)
        except Exception:
            await interaction.response.send_message("Invalid color format! Use hex like #7289da", ephemeral=True)

class SetupSelect(discord.ui.Select):
    def __init__(self, cog, slot_id):
        options = [
            discord.SelectOption(label="Choose The Action To Perform", value="choose", description="Choose what you want to do")
        ]
        super().__init__(placeholder="Choose The Action To Perform", options=options)
        self.cog = cog
        self.slot_id = slot_id
    async def callback(self, interaction: discord.Interaction):
        try:
            await self.cog.display_setup_options(interaction, self.slot_id, ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ Error",
                    description=f"An error occurred: {e}",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )

class SetupSelectView(discord.ui.View):
    def __init__(self, cog, slot_id):
        super().__init__()
        self.add_item(SetupSelect(cog, slot_id))

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
                slots = get_slots()
                current_time = int(time.time())
                for slot_id in slots:
                    slot_info = get_slot_info(slot_id)
                    if not slot_info:
                        continue
                    points_per_duration, default_name, occupied, occupied_by, occupied_till, pings_left = slot_info
                    if points_per_duration is None:
                        print(f"Warning: Slot {slot_id} has no points_per_duration set. Skipping.")
                        continue
                    slot_durations = [(key, DURATION_CONFIG[key]) for key in DURATION_CONFIG]
                    channel = self.bot.get_channel(slot_id)
                    if occupied and occupied_till and current_time >= occupied_till:
                        if channel:
                            try:
                                await delete_all_messages(channel)
                                view = SlotDurationView(slot_id, slot_durations, self)
                                await display_slot_available(channel, slot_id, slot_durations, view)
                                await channel.edit(name=default_name)
                                with db_connection() as conn:
                                    cursor = conn.cursor()
                                    cursor.execute(f"""
                                        UPDATE slots 
                                        SET occupied = 0, 
                                            occupied_by = 0, 
                                            occupied_till = 0,
                                            pings_left = {SLOT_CONFIG['default_pings']} 
                                        WHERE id = {slot_id}
                                    """)
                            except Exception as e:
                                print(f"Error resetting slot {slot_id}: {e}")
            except Exception as e:
                print(f"Error in slot check loop: {e}")
            await asyncio.sleep(10)

    async def cog_load(self):
        # On cog load (bot startup), delete all messages and send available embed for every slot channel
        await self.bot.wait_until_ready()
        slots = get_slots()
        for slot_id in slots:
            slot_info = get_slot_info(slot_id)  # Retrieve slot information here
            if not slot_info:
                continue
            points_per_duration, default_name, occupied, occupied_by, occupied_till, pings_left = slot_info
            if points_per_duration is None:
                print(f"Warning: Slot {slot_id} has no points_per_duration set. Skipping.")
                continue
            slot_durations = [(key, DURATION_CONFIG[key]) for key in DURATION_CONFIG]
            channel = self.bot.get_channel(slot_id)
            if channel:
                try:
                    await delete_all_messages(channel)
                    await display_slot_available(channel, slot_id, slot_durations, SlotDurationView(slot_id, slot_durations, self))
                except Exception as e:
                    print(f"Error initializing slot {slot_id}: {e}")

    @app_commands.command(name="points-shop", description="Open the points shop")
    async def points_shop(self, interaction: discord.Interaction):
        add_user(id=interaction.user.id)
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
                value=f"Price: {price}$",
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

    async def display_claimed(self, interaction, slot_id, user):
        slot_info = get_slot_info(slot_id)
        if not slot_info:
            return
        pings_left = slot_info[5]  # Get pings_left from database
        available_until_ts = slot_info[4]  # occupied_till
        username = user.name
        owner_id = user.id
        claimed_embed = discord.Embed(
            title=f"Slot - {username}",
            description="No Shop setup yet",
            color=discord.Color.purple()
        )
        # Format the timestamp for Discord
        if available_until_ts and available_until_ts > 0:
            available_until = f"<t:{available_until_ts}:R>"
        else:
            available_until = "N/A"
        info_embed = discord.Embed(
            title="Slot Information",
            description=f"**Pings Left - {pings_left}**\nSlot available {available_until}",
            color=discord.Color.blue()
        )
        channel = interaction.channel
        await delete_all_messages(channel)
        claimed_message = await channel.send(embed=claimed_embed)
        info_message = await channel.send(embed=info_embed)
        view = SlotClaimedView(  # pass info_message for updating
            owner_id, self, slot_id, username, available_until, claimed_message=claimed_message, claimed_embed=claimed_embed, info_message=info_message
        )
        await info_message.edit(view=view)

    async def display_setup(self, interaction, slot_id, ephemeral=False):
        view = SetupSelectView(self, slot_id)
        if ephemeral:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="Slot Setup",
                    description="Setup your Slot by using the menu below.",
                    color=discord.Color.blue()
                ),
                view=view,
                ephemeral=True
            )
        else:
            await display_slot_setup(interaction.channel, view)

    async def display_setup_options(self, interaction, slot_id, ephemeral=False):
        view = SetupOptionsView(discord.Embed(title="Slot Setup", description="Setup your Slot by using the menu below.", color=discord.Color.blue()), None)
        if ephemeral:
            await interaction.response.send_message(
                view=view,
                ephemeral=True
            )
        else:
            await display_slot_setup_options(interaction.channel, view)

    @app_commands.command(name="add-pings", description="Add pings to a user's slot (Admin only)")
    @is_admin()
    async def add_pings(self, interaction: discord.Interaction, user: discord.User, amount: int):
        # Check if user has an active slot
        current_slot = get_user_slot(user.id)
        if not current_slot:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ Error",
                    description="This user doesn't have an active slot!",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )
            return

        slot_id = current_slot[0]
        slot_info = get_slot_info(slot_id)
        if not slot_info:
            return

        # Get current pings and add the new amount
        current_pings = slot_info[5]  # pings_left is at index 5
        new_pings = current_pings + amount
        update_slot_pings(slot_id, new_pings)

        # Update the embed message
        channel = self.bot.get_channel(slot_id)
        if channel:
            async for message in channel.history(limit=10):
                if message.embeds and "Slot Information" in message.embeds[0].title:
                    embed = message.embeds[0]
                    embed.description = f"**Pings Left - {new_pings}**\nSlot available {embed.description.split('Slot available')[1]}"
                    await message.edit(embed=embed)
                    break

        await interaction.response.send_message(
            embed=discord.Embed(
                title="✅ Pings Added",
                description=f"Added {amount} pings to {user.mention}'s slot. They now have {new_pings} pings left.",
                color=discord.Color.green()
            ),
            ephemeral=True
        )

    @app_commands.command(name="remove-pings", description="Remove pings from a user's slot (Admin only)")
    @is_admin()
    async def remove_pings(self, interaction: discord.Interaction, user: discord.User, amount: int):
        # Check if user has an active slot
        current_slot = get_user_slot(user.id)
        if not current_slot:
            await interaction.response.send_message(
                embed=discord.Embed(
                    title="❌ Error",
                    description="This user doesn't have an active slot!",
                    color=discord.Color.red()
                ),
                ephemeral=True
            )
            return

        slot_id = current_slot[0]
        slot_info = get_slot_info(slot_id)
        if not slot_info:
            return

        # Get current pings and remove the amount
        current_pings = slot_info[5]  # pings_left is at index 5
        new_pings = max(0, current_pings - amount)  # Ensure pings don't go below 0
        update_slot_pings(slot_id, new_pings)

        # Update the embed message
        channel = self.bot.get_channel(slot_id)
        if channel:
            async for message in channel.history(limit=10):
                if message.embeds and "Slot Information" in message.embeds[0].title:
                    embed = message.embeds[0]
                    embed.description = f"**Pings Left - {new_pings}**\nSlot available {embed.description.split('Slot available')[1]}"
                    await message.edit(embed=embed)
                    break

        await interaction.response.send_message(
            embed=discord.Embed(
                title="✅ Pings Removed",
                description=f"Removed {amount} pings from {user.mention}'s slot. They now have {new_pings} pings left.",
                color=discord.Color.green()
            ),
            ephemeral=True
        )

async def setup(bot: commands.Bot):
    await bot.add_cog(Point(bot=bot))