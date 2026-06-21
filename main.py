from core.bot_setup import VinniesBot
from core.config import DISCORD_TOKEN

def main():
    if not DISCORD_TOKEN:
        print("Error: DISCORD_TOKEN not found in .env")
        return

    bot = VinniesBot()
    bot.run(DISCORD_TOKEN)

if __name__ == "__main__":
    main()
