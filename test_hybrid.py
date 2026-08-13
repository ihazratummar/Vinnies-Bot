import discord
from discord.ext import commands
import typing
import asyncio

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.hybrid_command(name="testcmd")
async def testcmd(self, ctx, arg: typing.Optional[typing.Union[discord.Member, str]] = None):
    await ctx.send(f"Arg type: {type(arg)}, value: {arg}")

async def main():
    # just testing syntax
    print("Syntax valid")

if __name__ == "__main__":
    asyncio.run(main())
