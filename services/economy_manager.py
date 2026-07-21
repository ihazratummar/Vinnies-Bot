import aiomysql
from urllib.parse import urlparse
from core.config import DB_URI

class EconomyManager:
    def __init__(self):
        self.pool = None
        self._parsed_uri = urlparse(DB_URI) if DB_URI else None

    async def init_db(self):
        if not self._parsed_uri:
            print("DB_URI not provided. Economy system disabled.")
            return

        print(f"Connecting to MySQL database at {self._parsed_uri.hostname}...")
        self.pool = await aiomysql.create_pool(
            host=self._parsed_uri.hostname,
            port=self._parsed_uri.port or 3306,
            user=self._parsed_uri.username,
            password=self._parsed_uri.password,
            db=self._parsed_uri.path.lstrip('/'),
            autocommit=True,
            pool_recycle=300
        )

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        guild_id BIGINT,
                        user_id BIGINT,
                        message_count INT DEFAULT 0,
                        coins INT DEFAULT 0,
                        PRIMARY KEY (guild_id, user_id)
                    )
                """)
                await cur.execute("""
                    CREATE TABLE IF NOT EXISTS daily_gifts (
                        guild_id BIGINT,
                        sender_id BIGINT,
                        receiver_id BIGINT,
                        timestamp DATE,
                        PRIMARY KEY (guild_id, sender_id, receiver_id, timestamp)
                    )
                """)
                await cur.execute("""
                    CREATE TABLE IF NOT EXISTS guild_config (
                        guild_id BIGINT PRIMARY KEY,
                        reward_role_name VARCHAR(255) DEFAULT 'Perks'
                    )
                """)
        print("MySQL Database connected and tables verified!")

    async def add_message(self, guild_id: int, user_id: int):
        if not self.pool: return False, 0
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute("INSERT INTO users (guild_id, user_id, message_count, coins) VALUES (%s, %s, 1, 0) ON DUPLICATE KEY UPDATE message_count = message_count + 1", (guild_id, user_id))
                    
                    await cur.execute("SELECT message_count FROM users WHERE guild_id = %s AND user_id = %s", (guild_id, user_id))
                    result = await cur.fetchone()
                    msg_count = result[0]
                    
                    if msg_count > 0 and msg_count % 1000 == 0:
                        await cur.execute("UPDATE users SET coins = coins + 10 WHERE guild_id = %s AND user_id = %s", (guild_id, user_id))
                        return True, 10
            return False, 0
        except Exception as e:
            print(f"Warning: Database error in add_message: {e}")
            return False, 0

    async def get_balance(self, guild_id: int, user_id: int):
        if not self.pool: return 0, 0
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT message_count, coins FROM users WHERE guild_id = %s AND user_id = %s", (guild_id, user_id))
                result = await cur.fetchone()
                if result:
                    return result[0], result[1]
                return 0, 0

    async def deduct_coins(self, guild_id: int, user_id: int, amount: int):
        if not self.pool: return False
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT coins FROM users WHERE guild_id = %s AND user_id = %s", (guild_id, user_id))
                result = await cur.fetchone()
                if not result or result[0] < amount:
                    return False
                await cur.execute("UPDATE users SET coins = coins - %s WHERE guild_id = %s AND user_id = %s", (amount, guild_id, user_id))
                return True

    async def gift_coin(self, guild_id: int, sender_id: int, receiver_id: int):
        if not self.pool: return False, "Database not connected."
        if sender_id == receiver_id: return False, "You cannot gift yourself!"
        
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                # Check daily limit
                await cur.execute("SELECT COUNT(*) FROM daily_gifts WHERE guild_id = %s AND sender_id = %s AND receiver_id = %s AND timestamp = CURDATE()", (guild_id, sender_id, receiver_id))
                count = (await cur.fetchone())[0]
                if count > 0:
                    return False, "You have already gifted this user today!"
                
                # Check balance
                await cur.execute("SELECT coins FROM users WHERE guild_id = %s AND user_id = %s", (guild_id, sender_id))
                result = await cur.fetchone()
                if not result or result[0] < 1:
                    return False, "You don't have enough coins to gift!"
                
                # Deduct sender, add to receiver
                await cur.execute("UPDATE users SET coins = coins - 1 WHERE guild_id = %s AND user_id = %s", (guild_id, sender_id))
                await cur.execute("INSERT INTO users (guild_id, user_id, message_count, coins) VALUES (%s, %s, 0, 1) ON DUPLICATE KEY UPDATE coins = coins + 1", (guild_id, receiver_id))
                
                # Record gift
                await cur.execute("INSERT INTO daily_gifts (guild_id, sender_id, receiver_id, timestamp) VALUES (%s, %s, %s, CURDATE())", (guild_id, sender_id, receiver_id))
                return True, "Gift sent successfully!"

    async def get_reward_role(self, guild_id: int):
        if not self.pool: return "Perks"
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT reward_role_name FROM guild_config WHERE guild_id = %s", (guild_id,))
                result = await cur.fetchone()
                if result and result[0]:
                    return result[0]
                return "Perks"

    async def set_reward_role(self, guild_id: int, role_name: str):
        if not self.pool: return False
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("INSERT INTO guild_config (guild_id, reward_role_name) VALUES (%s, %s) ON DUPLICATE KEY UPDATE reward_role_name = %s", (guild_id, role_name, role_name))
                return True

economy_manager = EconomyManager()
