import discord
from discord.ext import commands
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from services.economy_manager import economy_manager
from utils.embeds import build_success_embed, build_error_embed
from utils.views import GiftConfirmView

# A scalable configuration for the shop.
# To add a new item, simply add a new dictionary entry below.
SHOP_ITEMS = {
    "image_perms": {
        "name": "Image Perms",
        "description": "Unlocks the ability to send images and GIFs.",
        "aliases": ["image", "image perms", "imageperms", "gif perms", "gif"],
        "cost": 10000,
        "type": "role",  
        "role_id": 1528954436003823628,
        "role_name": "Perks",
        "emoji": "🖼️"
    },
    "vip_permanent": {
        "name": "VIP (Permanent)",
        "description": "Unlocks Permanent VIP perks in the server.",
        "aliases": ["vip", "vip permanent", "permanent vip", "vip role"],
        "cost": 30000,
        "type": "role",
        "role_name": "VIP",
        "emoji": "💎"
    },
    "vip_rental": {
        "name": "VIP (30-day rental)",
        "description": "Unlocks VIP perks for 30 days.",
        "aliases": ["vip rental", "rental vip", "vip 30"],
        "cost": 12000,
        "type": "rental_role",
        "duration_days": 30,
        "role_name": "VIP",
        "emoji": "⭐"
    }
}

class EconomyCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.scheduler = AsyncIOScheduler()
        self.scheduler.add_job(self.check_expired_rentals, 'interval', hours=1)
        self.scheduler.start()

    async def check_expired_rentals(self):
        expired = await economy_manager.get_expired_rentals()
        for guild_id, user_id, role_name in expired:
            guild = self.bot.get_guild(guild_id)
            if guild:
                member = guild.get_member(user_id)
                if not member:
                    try:
                        member = await guild.fetch_member(user_id)
                    except discord.NotFound:
                        pass
                
                if member:
                    role = discord.utils.get(guild.roles, name=role_name)
                    if role and role in member.roles:
                        try:
                            await member.remove_roles(role, reason="VIP Rental Expired")
                        except discord.Forbidden:
                            pass
            await economy_manager.remove_rental(guild_id, user_id, role_name)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild:
            return
            
        awarded, total_coins = await economy_manager.add_message(message.guild.id, message.author.id)
        if awarded and total_coins > 0 and total_coins % 500 == 0:
            try:
                reward_channel = None
                for channel in message.guild.text_channels:
                    if "chat-reward" in channel.name.lower() or "chatreward" in channel.name.lower():
                        reward_channel = channel
                        break
                        
                if not reward_channel:
                    reward_channel = await message.guild.create_text_channel("chat-rewards", reason="Created for economy milestone notifications")
                
                await reward_channel.send(f"🎉 Congratulations {message.author.mention}! You've reached a massive milestone of **{total_coins:,} coins**!")
            except discord.Forbidden:
                pass

    @commands.hybrid_command(name="balance")
    async def balance(self, ctx, user: discord.Member = None):
        """Check your or another user's coin and message balance."""
        await ctx.defer()
        target_user = user or ctx.author
        if target_user.bot:
            await ctx.send(embed=build_error_embed("Bots don't have an economy balance!"), ephemeral=True)
            return

        msg_count, coins = await economy_manager.get_balance(ctx.guild.id, target_user.id)
        
        embed = discord.Embed(
            title=f"💰 Balance for {target_user.display_name}",
            color=0xFEE75C
        )
        embed.set_thumbnail(url=target_user.display_avatar.url)
        embed.add_field(name="Messages Sent", value=f"{msg_count:,}", inline=True)
        embed.add_field(name="Coins", value=f"{coins:,}", inline=True)
        
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="shop")
    async def shop(self, ctx):
        """Displays the server perk shop."""
        await ctx.defer()
        embed = discord.Embed(
            title="🛒 Server Perk Shop",
            description="Use `/redeem <item>` to purchase an item!",
            color=0x57F287
        )
        
        for key, item in SHOP_ITEMS.items():
            embed.add_field(
                name=f"{item['emoji']} {item['name']}", 
                value=f"**Cost:** {item['cost']} Coins\n*{item['description']}*", 
                inline=False
            )
            
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="redeem")
    @discord.app_commands.describe(item_name="The name of the item you want to buy (e.g., 'image perms')")
    async def redeem(self, ctx, item_name: str):
        """Purchase a perk from the shop."""
        await ctx.defer()
        
        # Find the requested item in the shop configuration
        selected_item = None
        for key, item in SHOP_ITEMS.items():
            if item_name.lower() in item["aliases"] or item_name.lower() == item["name"].lower():
                selected_item = item
                break
                
        if not selected_item:
            await ctx.send(embed=build_error_embed("That item does not exist in the shop! Try `/shop` to see available items."), ephemeral=True)
            return
            
        if selected_item["type"] in ["role", "rental_role"]:
            role = None
            if selected_item.get("role_id"):
                role = ctx.guild.get_role(selected_item["role_id"])
            
            if not role:
                # If the item defines a specific role name, use it, else fallback to the dynamic DB config (legacy)
                role_name = selected_item.get("role_name")
                if not role_name:
                    role_name = await economy_manager.get_reward_role(ctx.guild.id)
                role = discord.utils.get(ctx.guild.roles, name=role_name)
                
            if not role:
                try:
                    role = await ctx.guild.create_role(name=role_name, reason="Economy Shop Role Creation")
                except discord.Forbidden:
                    await ctx.send(embed=build_error_embed(f"The {role_name} role could not be found, and I lack permissions to create it! Please contact an admin."), ephemeral=True)
                    return
                
            if role in ctx.author.roles:
                await ctx.send(embed=build_error_embed(f"You already have {selected_item['name']}!"), ephemeral=True)
                return

            # Deduct coins
            success = await economy_manager.deduct_coins(ctx.guild.id, ctx.author.id, selected_item["cost"])
            if not success:
                await ctx.send(embed=build_error_embed(f"You don't have enough coins! This perk costs **{selected_item['cost']} Coins**."), ephemeral=True)
                return
                
            # Assign role
            try:
                await ctx.author.add_roles(role)
                if selected_item["type"] == "rental_role":
                    await economy_manager.add_rental(ctx.guild.id, ctx.author.id, role_name, selected_item["duration_days"])
                await ctx.send(embed=build_success_embed(f"Successfully purchased **{selected_item['name']}** for {selected_item['cost']} Coins!"))
            except discord.Forbidden:
                # Direct DB refund for robust failure handling
                async with economy_manager.pool.acquire() as conn:
                    async with conn.cursor() as cur:
                        await cur.execute("UPDATE users SET coins = coins + %s WHERE guild_id = %s AND user_id = %s", (selected_item["cost"], ctx.guild.id, ctx.author.id))
                await ctx.send(embed=build_error_embed("I don't have permission to assign that role. I have refunded your coins! Please contact an admin."), ephemeral=True)
        else:
            await ctx.send(embed=build_error_embed("This item type is not supported yet!"), ephemeral=True)

    @commands.hybrid_command(name="gift")
    @discord.app_commands.describe(user="The user you want to gift coins to", amount="Amount of coins to gift")
    async def gift(self, ctx, user: discord.Member, amount: int):
        """Gift coins to another user with no daily limit."""
        if user.bot:
            await ctx.send(embed=build_error_embed("You cannot gift coins to bots!"), ephemeral=True)
            return
            
        if amount <= 0:
            await ctx.send(embed=build_error_embed("Amount must be greater than 0!"), ephemeral=True)
            return
            
        _, coins = await economy_manager.get_balance(ctx.guild.id, ctx.author.id)
        if coins < amount:
            await ctx.send(embed=build_error_embed(f"You don't have enough coins! You need **{amount:,}** coins."), ephemeral=True)
            return

        embed = discord.Embed(
            title="🎁 Confirm Gift",
            description=f"Are you sure you want to gift **{amount:,} coins** to {user.mention}?*",
            color=0xFEE75C
        )

        async def confirm_callback(interaction: discord.Interaction):
            success, msg = await economy_manager.gift_coin(ctx.guild.id, ctx.author.id, user.id, amount)
            if success:
                await interaction.followup.send(embed=build_success_embed(f"Successfully gifted **{amount:,} coins** to {user.mention}!"))
            else:
                await interaction.followup.send(embed=build_error_embed(msg), ephemeral=True)

        view = GiftConfirmView(sender_id=ctx.author.id, confirm_callback=confirm_callback)
        await ctx.send(embed=embed, view=view)

async def setup(bot):
    await bot.add_cog(EconomyCog(bot))
