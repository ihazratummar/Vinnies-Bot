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
                        last_message_time DATETIME DEFAULT NULL,
                        last_active_date DATE DEFAULT NULL,
                        daily_coins_earned INT DEFAULT 0,
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
                await cur.execute("""
                    CREATE TABLE IF NOT EXISTS role_rentals (
                        guild_id BIGINT,
                        user_id BIGINT,
                        role_name VARCHAR(100),
                        expires_at DATETIME,
                        PRIMARY KEY (guild_id, user_id, role_name)
                    )
                """)
                await cur.execute("""
                    CREATE TABLE IF NOT EXISTS leaderboard_messages (
                        guild_id BIGINT PRIMARY KEY,
                        channel_id BIGINT,
                        message_id BIGINT
                    )
                """)
        print("MySQL Database connected and tables verified!")

    async def add_message(self, guild_id: int, user_id: int):
        if not self.pool: return False, 0
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cur:
                    await cur.execute("SELECT last_message_time, last_active_date, daily_coins_earned FROM users WHERE guild_id = %s AND user_id = %s", (guild_id, user_id))
                    result = await cur.fetchone()
                    
                    if not result:
                        await cur.execute("INSERT INTO users (guild_id, user_id, message_count, coins, last_message_time, last_active_date, daily_coins_earned) VALUES (%s, %s, 1, 2, NOW(), CURDATE(), 2)", (guild_id, user_id))
                        return True, 2
                        
                    last_msg_time, last_active_date, daily_earned = result
                    
                    await cur.execute("SELECT CURDATE()")
                    current_date = (await cur.fetchone())[0]
                    if last_active_date != current_date:
                        daily_earned = 0
                        
                    qualifies = False
                    if last_msg_time is None:
                        qualifies = True
                    else:
                        await cur.execute("SELECT TIMESTAMPDIFF(SECOND, %s, NOW())", (last_msg_time,))
                        diff_row = await cur.fetchone()
                        if diff_row and diff_row[0] is not None and diff_row[0] >= 30:
                            qualifies = True
                            
                    if qualifies:
                        await cur.execute("UPDATE users SET message_count = message_count + 1, coins = coins + 2, last_message_time = NOW(), last_active_date = CURDATE(), daily_coins_earned = %s WHERE guild_id = %s AND user_id = %s", (daily_earned + 2, guild_id, user_id))
                        await cur.execute("SELECT coins FROM users WHERE guild_id = %s AND user_id = %s", (guild_id, user_id))
                        total_coins = (await cur.fetchone())[0]
                        return True, total_coins
                    else:
                        await cur.execute("UPDATE users SET message_count = message_count + 1 WHERE guild_id = %s AND user_id = %s", (guild_id, user_id))
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

    async def add_coins(self, guild_id: int, user_id: int, amount: int):
        if not self.pool: return False
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("INSERT INTO users (guild_id, user_id, message_count, coins, daily_coins_earned) VALUES (%s, %s, 0, %s, 0) ON DUPLICATE KEY UPDATE coins = coins + %s", (guild_id, user_id, amount, amount))
                return True

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

    async def gift_coin(self, guild_id: int, sender_id: int, receiver_id: int, amount: int):
        if not self.pool: return False, "Database not connected."
        if sender_id == receiver_id: return False, "You cannot gift yourself!"
        if amount <= 0: return False, "Amount must be greater than 0!"
        
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                
                # Check balance
                await cur.execute("SELECT coins FROM users WHERE guild_id = %s AND user_id = %s", (guild_id, sender_id))
                result = await cur.fetchone()
                if not result or result[0] < amount:
                    return False, f"You don't have enough coins! You need **{amount:,}** coins."
                
                # Deduct sender, add to receiver
                await cur.execute("UPDATE users SET coins = coins - %s WHERE guild_id = %s AND user_id = %s", (amount, guild_id, sender_id))
                await cur.execute("INSERT INTO users (guild_id, user_id, message_count, coins) VALUES (%s, %s, 0, %s) ON DUPLICATE KEY UPDATE coins = coins + %s", (guild_id, receiver_id, amount, amount))
                
                return True, "Gift sent successfully!"

    async def get_reward_role(self, guild_id: int):
        if not self.pool: return "Perks"
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT reward_role_name FROM guild_config WHERE guild_id = %s", (guild_id,))
                result = await cur.fetchone()
                return result[0] if result else "Perks"

    async def set_reward_role(self, guild_id: int, role_name: str):
        if not self.pool: return False
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("INSERT INTO guild_config (guild_id, reward_role_name) VALUES (%s, %s) ON DUPLICATE KEY UPDATE reward_role_name = %s", (guild_id, role_name, role_name))
                return True

    async def add_rental(self, guild_id: int, user_id: int, role_name: str, duration_days: int):
        if not self.pool: return False
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("""
                    INSERT INTO role_rentals (guild_id, user_id, role_name, expires_at) 
                    VALUES (%s, %s, %s, DATE_ADD(NOW(), INTERVAL %s DAY))
                    ON DUPLICATE KEY UPDATE expires_at = DATE_ADD(expires_at, INTERVAL %s DAY)
                """, (guild_id, user_id, role_name, duration_days, duration_days))
                return True

    async def get_expired_rentals(self):
        if not self.pool: return []
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT guild_id, user_id, role_name FROM role_rentals WHERE expires_at <= NOW()")
                return await cur.fetchall()

    async def remove_rental(self, guild_id: int, user_id: int, role_name: str):
        if not self.pool: return False
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("DELETE FROM role_rentals WHERE guild_id = %s AND user_id = %s AND role_name = %s", (guild_id, user_id, role_name))
                return True

    async def get_top_users(self, guild_id: int, limit: int = 10):
        if not self.pool: return []
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT user_id, coins FROM users WHERE guild_id = %s ORDER BY coins DESC LIMIT %s", (guild_id, limit))
                return await cur.fetchall()

    async def get_leaderboard_msg(self, guild_id: int):
        if not self.pool: return None, None
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT channel_id, message_id FROM leaderboard_messages WHERE guild_id = %s", (guild_id,))
                return await cur.fetchone() or (None, None)
                
    async def get_all_leaderboards(self):
        if not self.pool: return []
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("SELECT guild_id, channel_id, message_id FROM leaderboard_messages")
                return await cur.fetchall()

    async def delete_leaderboard_msg(self, guild_id: int):
        if not self.pool: return
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("DELETE FROM leaderboard_messages WHERE guild_id = %s", (guild_id,))

    async def set_leaderboard_msg(self, guild_id: int, channel_id: int, message_id: int):
        if not self.pool: return
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute("INSERT INTO leaderboard_messages (guild_id, channel_id, message_id) VALUES (%s, %s, %s) ON DUPLICATE KEY UPDATE channel_id = %s, message_id = %s", (guild_id, channel_id, message_id, channel_id, message_id))

economy_manager = EconomyManager()
