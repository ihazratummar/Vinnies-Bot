import asyncio
import aiomysql
from urllib.parse import urlparse
import os
from dotenv import load_dotenv

load_dotenv()

async def reset_db():
    uri_str = os.getenv("DB_URI")
    parsed = urlparse(uri_str)
    
    print(f"Connecting to {parsed.hostname}...")
    pool = await aiomysql.create_pool(
        host=parsed.hostname,
        port=parsed.port or 3306,
        user=parsed.username,
        password=parsed.password,
        db=parsed.path.lstrip('/'),
        autocommit=True
    )
    
    async with pool.acquire() as conn:
        async with conn.cursor() as cur:
            await cur.execute("DROP TABLE IF EXISTS users, daily_gifts, guild_config")
            print("Dropped old tables!")
            
    pool.close()
    await pool.wait_closed()

if __name__ == "__main__":
    asyncio.run(reset_db())
