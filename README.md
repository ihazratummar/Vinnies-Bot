# V's Friend Bot

V's Friend Bot is a feature-rich, fully asynchronous Discord bot built with `discord.py`. It brings a complete multi-server gambling experience and a dynamic MySQL-powered economy system to your Discord servers.

## ✨ Features

### 🎲 Interactive Gambling System
Challenge your friends to fun mini-games using modern Discord UI Buttons and Embeds.
- **`/dice <user>`**: Roll the highest number on a 12-sided dice to win. Best of 5 wins the match.
- **`/coinflip <user>`**: A classic game of heads or tails. Best of 5 wins the match.
- **`/rps <user>`**: Rock, Paper, Scissors! Best of 3 wins the match.
- **Smart Turn Logic**: The bot enforces turns, prevents self-challenges, and correctly prevents users from being in multiple matches simultaneously.

### 💰 Multi-Server Economy System
A fully asynchronous, globally scalable MySQL economy system that isolates balances per server.
- **Message Milestones**: Users automatically earn **10 Coins** every time they send 1,000 messages in the server.
- **`/balance [user]`**: Check the coin and message count for yourself or another user.
- **`/shop`**: View the server's perk shop (Easily expandable via the `SHOP_ITEMS` config).
- **`/redeem <item>`**: Buy items from the shop. By default, it allows users to buy the "Perks" role for 5 Coins. If the role doesn't exist, the bot automatically creates it!
- **`/gift <user>`**: Gift 1 Coin to another user. Enforces a strict limit of 1 gift per specific user per day.

### ⚙️ Admin Tools
- **`/cancelmatch <user>`**: Forcefully cancel a stuck match or pending challenge.
- **`/setdice <number>`**: (Admin only) Rig the next dice roll to be a specific number between 2 and 12.

## 🚀 Setup & Installation

### Prerequisites
- **Python 3.8+**
- A **MySQL Database** (local or remote)
- A Discord Bot Token (from the [Discord Developer Portal](https://discord.com/developers/applications))
  - *Note: Ensure the **Message Content Intent** is enabled for the bot to track messages!*

### 1. Clone & Install Dependencies
Clone the repository and install the required Python packages:
```bash
pip install -r requirements.txt
```

### 2. Environment Variables
Create a `.env` file in the root directory and add the following configuration:
```env
BOT_TOKEN=your_discord_bot_token_here
DB_URI=mysql://username:password@hostname:3306/database_name
```

### 3. Run the Bot
Start the bot using Python:
```bash
python main.py
```
*Note: The bot will automatically connect to your MySQL database and create the required tables (`users`, `daily_gifts`, `guild_config`) if they do not exist!*

## 🛠️ Expanding the Shop
The economy shop was built to be completely dynamic and future-proof. 
To add new items or roles to the shop, simply open `cogs/economy.py` and add a new dictionary entry to the `SHOP_ITEMS` configuration at the very top of the file! No logic changes required.
