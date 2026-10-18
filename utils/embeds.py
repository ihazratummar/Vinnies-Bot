import discord

COLOR_DEFAULT = 0x2b2d31
COLOR_SUCCESS = 0x57F287
COLOR_ERROR = 0xED4245
COLOR_WARNING = 0xFEE75C

def build_challenge_embed(challenger: discord.Member, opponent: discord.Member, game_type: str, target_score: int = 5) -> discord.Embed:
    formatted_game = game_type.replace("_", " ").title()
    embed = discord.Embed(
        title=f"🎮 New {formatted_game} Challenge!",
        description=f"{challenger.mention} has challenged {opponent.mention} to a **{formatted_game}** match!\n\n"
                    f"**First to {target_score} wins.**\n"
                    f"{opponent.mention}, click the buttons below to accept or decline.",
        color=COLOR_DEFAULT
    )
    embed.set_thumbnail(url=challenger.display_avatar.url)
    return embed

def build_match_start_embed(challenger: discord.Member, opponent: discord.Member, game_type: str) -> discord.Embed:
    formatted_game = game_type.replace("_", " ").title()
    gt = game_type.lower()
    if gt == "rps":
        instruction = "Click the buttons below to pick Rock, Paper, or Scissors."
    elif gt == "colored_dice":
        instruction = "Click your color choice below to take your turn."
    elif gt == "coinflip":
        instruction = "Click **Heads** or **Tails** below to take your turn."
    elif gt == "blackjack":
        instruction = "Click **Hit** or **Stand** below to take your turn."
    elif gt == "dice":
        instruction = "Click the **Roll Dice** button below to roll!"
    else:
        instruction = "Click the button below to take your turn."

    embed = discord.Embed(
        title="⚔️ Match Started!",
        description=f"The **{formatted_game}** match between {challenger.mention} and {opponent.mention} has begun!\n\n"
                    f"👉 {instruction}",
        color=COLOR_SUCCESS
    )
    return embed

def format_hand_display(cards: list, reveal: bool = True) -> tuple:
    """Returns (cards_str, total_str, raw_total)"""
    if not cards:
        return "*No cards*", "0", 0
        
    if not reveal and len(cards) >= 2:
        c1 = cards[0]
        displayed = f"[`{c1[0]}{c1[1]}`] [` 🂠 ? `]"
        first_val = 10 if c1[0] in ("J", "Q", "K") else (11 if c1[0] == "A" else int(c1[0]))
        return displayed, f"**{first_val} + ?**", first_val

    displayed = " ".join([f"[`{r}{s}`]" for r, s in cards])
    total = 0
    aces = 0
    for r, _ in cards:
        if r in ("J", "Q", "K"):
            total += 10
        elif r == "A":
            total += 11
            aces += 1
        else:
            total += int(r)
    while total > 21 and aces > 0:
        total -= 10
        aces -= 1

    if total > 21:
        total_str = f"💥 **BUST ({total})**"
    elif total == 21 and len(cards) == 2:
        total_str = "✨ **BLACKJACK! (21)**"
    else:
        total_str = f"**{total}**"

    return displayed, total_str, total

def build_blackjack_embed(
    challenger: discord.Member,
    opponent: discord.Member,
    challenger_cards: list,
    opponent_cards: list,
    c_score: int,
    o_score: int,
    target_score: int,
    current_turn_member: discord.Member = None,
    reveal_challenger: bool = True,
    reveal_opponent: bool = False,
    note: str = None,
    color: int = COLOR_DEFAULT,
    image_url: str = "attachment://blackjack.png"
) -> discord.Embed:
    embed = discord.Embed(
        title="🃏 1v1 Blackjack",
        color=color
    )
    
    desc_lines = []
    if note:
        desc_lines.append(f"{note}")
    if current_turn_member:
        desc_lines.append(f"👉 **Turn:** {current_turn_member.mention} — Click **Hit** or **Stand**")
    if desc_lines:
        embed.description = "\n".join(desc_lines)

    if image_url:
        embed.set_image(url=image_url)
    else:
        c_cards_str, c_total_str, _ = format_hand_display(challenger_cards, reveal=reveal_challenger)
        o_cards_str, o_total_str, _ = format_hand_display(opponent_cards, reveal=reveal_opponent)
        embed.add_field(
            name=f"👤 {challenger.display_name} (Score: {c_score}/{target_score})",
            value=f"{c_cards_str} • {c_total_str}",
            inline=False
        )
        embed.add_field(
            name=f"👤 {opponent.display_name} (Score: {o_score}/{target_score})",
            value=f"{o_cards_str} • {o_total_str}",
            inline=False
        )

    embed.set_footer(text=f"First to {target_score} wins! • Click buttons below or type 'hit' / 'stand'")
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
    
def build_match_winner_embed(winner: discord.Member, target_score: int = 5) -> discord.Embed:
    embed = discord.Embed(
        title="🎉 MATCH OVER 🎉",
        description=f"**{winner.mention} HAS REACHED {target_score} WINS!**\nCongratulations!",
        color=COLOR_SUCCESS
    )
    return embed

def build_error_embed(message: str) -> discord.Embed:
    return discord.Embed(description=f"❌ {message}", color=COLOR_ERROR)

def build_success_embed(message: str) -> discord.Embed:
    return discord.Embed(description=f"✅ {message}", color=COLOR_SUCCESS)
