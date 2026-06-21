import discord
import json
import os
from discord.ext import commands
from utils.embeds import build_success_embed

DATA_FILE = "admin_data.json"

def save_forced_dice(result):
    data = {}
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            pass
    data["forced_dice_result"] = result
    with open(DATA_FILE, "w") as f:
        json.dump(data, f)

def load_forced_dice():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                return json.load(f).get("forced_dice_result")
        except json.JSONDecodeError:
            pass
    return None

ALLOWED_USERS = [1474434976379437066, 1472003827216420977]

def is_allowed_user():
    async def predicate(ctx):
        if ctx.author.id not in ALLOWED_USERS:
            raise commands.MissingPermissions(["Bot Owner"])
        return True
    return commands.check(predicate)

class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.forced_dice_result = load_forced_dice()
        self.bot.clear_forced_dice = self.clear_forced_dice

    def clear_forced_dice(self):
        self.bot.forced_dice_result = None
        save_forced_dice(None)

    @commands.hybrid_command(name="setdice")
    @is_allowed_user()
    @discord.app_commands.default_permissions(administrator=True)
    async def setdice(self, ctx, result: int):
        """Forces the next dice roll to be a specific number."""
        if result < 1 or result > 12:
            await ctx.send("Dice result must be between 1 and 12.", ephemeral=True)
            return
        
        self.bot.forced_dice_result = result
        save_forced_dice(result)
        await ctx.send(embed=build_success_embed(f"Next dice roll will be {result}."), ephemeral=True)

    @commands.hybrid_command(name="cancelmatch")
    @is_allowed_user()
    async def cancelmatch(self, ctx, user: discord.Member):
        """Forcefully cancels an active match or pending challenge for a user."""
        from services.match_manager import match_manager
        success, msg, match = await match_manager.cancel_challenge_or_match(user.id)
        if success:
            await ctx.send(embed=build_success_embed(f"Successfully cancelled match/challenge for {user.mention}."), ephemeral=True)
        else:
            await ctx.send(embed=build_error_embed(f"User {user.mention} does not have an active match or pending challenge."), ephemeral=True)

async def setup(bot):
    await bot.add_cog(AdminCog(bot))
