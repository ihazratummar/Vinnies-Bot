import discord
from discord.ext import commands
from utils.checks import NotTicketChannel
from utils.embeds import build_error_embed
import traceback

class VinniesBot(commands.AutoShardedBot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        
        super().__init__(command_prefix="!", intents=intents, help_command=None)
        
    async def setup_hook(self):
        cogs = ["cogs.gambling", "cogs.admin"]
        for cog in cogs:
            await self.load_extension(cog)
            print(f"Loaded {cog}")
            
        print("Syncing command tree...")
        await self.tree.sync()
        print("Command tree synced!")

    async def on_ready(self):
        print(f"Logged in as {self.user} (ID: {self.user.id})")
        print("------")

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
