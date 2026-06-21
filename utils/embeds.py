import discord

COLOR_DEFAULT = 0x2b2d31
COLOR_SUCCESS = 0x57F287
COLOR_ERROR = 0xED4245
COLOR_WARNING = 0xFEE75C

def build_challenge_embed(challenger: discord.Member, opponent: discord.Member, game_type: str) -> discord.Embed:
    embed = discord.Embed(
        title=f"🎮 New {game_type.capitalize()} Challenge!",
        description=f"{challenger.mention} has challenged {opponent.mention} to a **{game_type.capitalize()}** match!\n\n"
                    f"**First to 5 wins.**\n"
                    f"{opponent.mention}, type `!accept` to start the game or `!cancel` to decline.",
        color=COLOR_DEFAULT
    )
    embed.set_thumbnail(url=challenger.display_avatar.url)
    return embed

def build_match_start_embed(challenger: discord.Member, opponent: discord.Member, game_type: str) -> discord.Embed:
    embed = discord.Embed(
        title="⚔️ Match Started!",
        description=f"The **{game_type.capitalize()}** match between {challenger.mention} and {opponent.mention} has begun!\n"
                    f"{challenger.mention} goes first. Type `!{game_type}` to play.",
        color=COLOR_SUCCESS
    )
    return embed

def build_turn_result_embed(player: discord.Member, result: str) -> discord.Embed:
    embed = discord.Embed(
        description=f"🎲 {player.mention} got: **{result}**",
        color=COLOR_DEFAULT
    )
    return embed

def build_round_winner_embed(winner: discord.Member, challenger: discord.Member, opponent: discord.Member, c_score: int, o_score: int, next_turn: discord.Member) -> discord.Embed:
    embed = discord.Embed(
        title="🏆 Round Winner!",
        description=f"{winner.mention} wins this round!\n\n"
                    f"**Current Score:**\n"
                    f"{challenger.mention}: {c_score}\n"
                    f"{opponent.mention}: {o_score}\n\n"
                    f"It's {next_turn.mention}'s turn next.",
        color=COLOR_WARNING
    )
    return embed
    
def build_match_winner_embed(winner: discord.Member) -> discord.Embed:
    embed = discord.Embed(
        title="🎉 MATCH OVER 🎉",
        description=f"**{winner.mention} HAS REACHED 5 WINS!**\nCongratulations!",
        color=COLOR_SUCCESS
    )
    return embed

def build_error_embed(message: str) -> discord.Embed:
    return discord.Embed(description=f"❌ {message}", color=COLOR_ERROR)

def build_success_embed(message: str) -> discord.Embed:
    return discord.Embed(description=f"✅ {message}", color=COLOR_SUCCESS)
