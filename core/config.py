import os
from dotenv import load_dotenv

load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DB_URI = os.getenv("DB_URI", "")

# Whitelisted Server IDs (Bot will leave any guild not in this list)
raw_guild_ids = os.getenv("ALLOWED_GUILD_IDS", "1417353554104029226,1126486185947189318")
ALLOWED_GUILD_IDS = [int(gid.strip()) for gid in raw_guild_ids.split(",") if gid.strip().isdigit()]

