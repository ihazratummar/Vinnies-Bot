import discord
from discord.ext import commands
from utils.checks import NotTicketChannel
from utils.embeds import build_error_embed
from core.config import ALLOWED_GUILD_IDS
import traceback

class VinniesBot(commands.AutoShardedBot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        
        super().__init__(command_prefix="!", intents=intents, help_command=None)
        
    async def _check_and_enforce_guild_lock(self, guild: discord.Guild):
        if ALLOWED_GUILD_IDS and guild.id not in ALLOWED_GUILD_IDS:
            print(f"[GUILD LOCK] Leaving unauthorized guild: '{guild.name}' (ID: {guild.id})")
            try:
                await guild.leave()
            except Exception as e:
                print(f"[GUILD LOCK ERROR] Failed to leave guild {guild.id}: {e}")

    async def setup_hook(self):
        cogs = ["cogs.gambling", "cogs.admin", "cogs.economy"]
        for cog in cogs:
            await self.load_extension(cog)
            print(f"Loaded {cog}")
            
        print("Initializing database...")
        from services.economy_manager import economy_manager
        await economy_manager.init_db()
            
        print("Syncing command tree...")
        await self.tree.sync()
        print("Command tree synced!")

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print("Enforcing server whitelist...")
        for guild in list(self.guilds):
            await self._check_and_enforce_guild_lock(guild)
        print("------")

    async def on_guild_join(self, guild: discord.Guild):
        print(f"[GUILD JOINED] Bot joined guild '{guild.name}' (ID: {guild.id})")
        await self._check_and_enforce_guild_lock(guild)


    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            error = error.original

        if isinstance(error, NotTicketChannel):
            await ctx.send(embed=build_error_embed(str(error)), ephemeral=True)
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send(embed=build_error_embed("You don't have permission to use this command."), ephemeral=True)
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(embed=build_error_embed(f"This command is on cooldown. Try again in {error.retry_after:.2f}s."), ephemeral=True)
        elif isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(embed=build_error_embed(f"You are missing a required argument: `{error.param.name}`. Please check the command usage."), ephemeral=True)
        elif isinstance(error, commands.BadArgument):
            await ctx.send(embed=build_error_embed("Invalid argument provided. " + str(error)), ephemeral=True)
        elif isinstance(error, commands.CommandNotFound):
            pass
        else:
            print(f"Ignoring exception in command {ctx.command}: {error}")
            traceback.print_exception(type(error), error, error.__traceback__)
