import discord
from discord.ui import (
    LayoutView,
    Container,
    Section,
    TextDisplay,
    Separator,
    Thumbnail,
    ActionRow,
    Button,
    Select,
    MediaGallery
)
from utils.embeds import build_error_embed

COLOR_GOLD = discord.Colour.gold()
COLOR_BLURPLE = discord.Colour.blurple()
COLOR_GREEN = discord.Colour.green()
COLOR_RED = discord.Colour.red()
COLOR_PURPLE = discord.Colour.from_rgb(138, 43, 226)
COLOR_DARK_FELT = discord.Colour.from_rgb(10, 36, 26)

class ChallengeLayoutView(LayoutView):
    """Component v2 layout for challenge invitations (Dice, Coinflip, Blackjack, etc.)."""
    def __init__(self, challenger: discord.Member, opponent: discord.Member, game_type: str, target_score: int, accept_cb, decline_cb, rules_text: str = None):
        super().__init__(timeout=None)
        self.challenger_id = challenger.id
        self.opponent_id = opponent.id
        self.accept_cb = accept_cb
        self.decline_cb = decline_cb

        formatted_game = game_type.replace("_", " ").title()

        accept_btn = Button(label="Accept", emoji="⚔️", style=discord.ButtonStyle.success, custom_id="btn_v2_accept")
        accept_btn.callback = self._on_accept

        decline_btn = Button(label="Decline", emoji="✖️", style=discord.ButtonStyle.secondary, custom_id="btn_v2_decline")
        decline_btn.callback = self._on_decline

        avatar_url = challenger.display_avatar.url if challenger and challenger.display_avatar else None
        rule_desc = rules_text if rules_text else f"First to **{target_score}** wins."
        desc_text = (
            f"**{challenger.display_name}** has challenged **{opponent.display_name}** to a **{formatted_game}** match!\n"
            f"🎯 **Rules:** {rule_desc}\n\n"
            f"{opponent.mention}, click below to respond:"
        )

        if avatar_url:
            challenge_sec = Section(desc_text, accessory=Thumbnail(avatar_url))
        else:
            challenge_sec = TextDisplay(desc_text)

        container = Container(
            TextDisplay(f"### 🎮 1v1 {formatted_game} Challenge"),
            Separator(spacing=discord.SeparatorSpacing.small),
            challenge_sec,
            Separator(spacing=discord.SeparatorSpacing.small),
            ActionRow(accept_btn, decline_btn),
            accent_colour=COLOR_GOLD
        )
        self.add_item(container)

    async def _on_accept(self, interaction: discord.Interaction):
        if interaction.user.id != self.opponent_id:
            await interaction.response.send_message(embed=build_error_embed("Only the challenged player can accept!"), ephemeral=True)
            return
        await self.accept_cb(interaction)

    async def _on_decline(self, interaction: discord.Interaction):
        if interaction.user.id not in (self.opponent_id, self.challenger_id):
            await interaction.response.send_message(embed=build_error_embed("You cannot interact with this challenge!"), ephemeral=True)
            return
        await self.decline_cb(interaction)


class DiceGameplayLayoutView(LayoutView):
    """Component v2 layout for active 1v1 Dice match with a sleek inline roll button or compact row."""
    def __init__(
        self,
        match,
        c_member: discord.Member,
        o_member: discord.Member,
        current_turn_member: discord.Member,
        action_cb,
        prev_roll_text: str = None,
        round_note: str = None,
        button_style: str = "inline"
    ):
        super().__init__(timeout=None)
        self.match = match
        self.action_cb = action_cb

        roll_btn = Button(label="Roll Dice", emoji="🎲", style=discord.ButtonStyle.primary, custom_id="btn_v2_roll")
        roll_btn.callback = self._on_roll

        round_num = getattr(match, "round_num", 1)
        header_text = f"### 🎲 1v1 Dice • Round {round_num}"
        score_text = f"> 🏆 **Match Score:** {c_member.mention} **({match.challenger.score})** — **({match.opponent.score})** {o_member.mention} *(First to {match.target_score})*"

        children = [
            TextDisplay(header_text),
            TextDisplay(score_text),
            Separator(spacing=discord.SeparatorSpacing.small)
        ]

        if prev_roll_text:
            children.append(TextDisplay(prev_roll_text))
            children.append(Separator(spacing=discord.SeparatorSpacing.small))

        if round_note:
            children.append(TextDisplay(round_note))
            children.append(Separator(spacing=discord.SeparatorSpacing.small))

        if button_style == "actionrow":
            children.append(TextDisplay(f"👉 **{current_turn_member.mention}**, it's your turn to roll:"))
            children.append(ActionRow(roll_btn))
        else:
            turn_sec = Section(
                f"👉 **{current_turn_member.mention}**, it's your turn!",
                accessory=roll_btn
            )
            children.append(turn_sec)

        container = Container(*children, accent_colour=COLOR_BLURPLE)
        self.add_item(container)

    async def _on_roll(self, interaction: discord.Interaction):
        if interaction.user.id != self.match.current_turn_player_id:
            await interaction.response.send_message(embed=build_error_embed("It's not your turn!"), ephemeral=True)
            return
        await self.action_cb(interaction, self.match, choice=None)


class DiceRoundResultLayoutView(LayoutView):
    """Component v2 layout for round conclusion with inline Next Round button."""
    def __init__(
        self,
        match,
        c_member: discord.Member,
        o_member: discord.Member,
        c_result_str: str,
        o_result_str: str,
        winner_member: discord.Member = None,
        next_turn_member: discord.Member = None,
        action_cb = None,
        button_style: str = "inline"
    ):
        super().__init__(timeout=None)
        self.match = match
        self.action_cb = action_cb

        round_num = getattr(match, "round_num", 1)
        is_tie = (winner_member is None)
        accent = COLOR_GOLD if is_tie else COLOR_GREEN

        header_text = f"### 🎲 Round {round_num} Result • {'Tie / Push' if is_tie else f'{winner_member.display_name} Wins!'}"
        score_text = f"> 🏆 **Match Score:** {c_member.mention} **({match.challenger.score})** — **({match.opponent.score})** {o_member.mention} *(First to {match.target_score})*"

        roll_summary = f"🎲 **{c_member.display_name}** rolled {c_result_str}\n🎲 **{o_member.display_name}** rolled {o_result_str}"

        children = [
            TextDisplay(header_text),
            TextDisplay(score_text),
            Separator(spacing=discord.SeparatorSpacing.small),
            TextDisplay(roll_summary),
            Separator(spacing=discord.SeparatorSpacing.small)
        ]

        if next_turn_member and action_cb:
            next_btn = Button(label="Roll Dice", emoji="🎲", style=discord.ButtonStyle.primary, custom_id="btn_v2_next_roll")
            next_btn.callback = self._on_roll
            if button_style == "actionrow":
                children.append(TextDisplay(f"👉 **{next_turn_member.mention}**, start the next round:"))
                children.append(ActionRow(next_btn))
            else:
                turn_sec = Section(
                    f"👉 **{next_turn_member.mention}**, start the next round!",
                    accessory=next_btn
                )
                children.append(turn_sec)

        container = Container(*children, accent_colour=accent)
        self.add_item(container)

    async def _on_roll(self, interaction: discord.Interaction):
        if interaction.user.id != self.match.current_turn_player_id:
            await interaction.response.send_message(embed=build_error_embed("It's not your turn!"), ephemeral=True)
            return
        await self.action_cb(interaction, self.match, choice=None)


class CoinflipGameplayLayoutView(LayoutView):
    """Component v2 layout for 1v1 Coinflip match with compact Heads/Tails buttons."""
    def __init__(
        self,
        match,
        c_member: discord.Member,
        o_member: discord.Member,
        current_turn_member: discord.Member,
        action_cb,
        prev_flip_text: str = None
    ):
        super().__init__(timeout=None)
        self.match = match
        self.action_cb = action_cb

        heads_btn = Button(label="Heads", emoji="🪙", style=discord.ButtonStyle.primary, custom_id="btn_v2_heads")
        heads_btn.callback = self._on_heads

        tails_btn = Button(label="Tails", emoji="🪙", style=discord.ButtonStyle.primary, custom_id="btn_v2_tails")
        tails_btn.callback = self._on_tails

        header_text = "### 🪙 1v1 Coinflip"
        score_text = f"> 🏆 **Match Score:** {c_member.mention} **({match.challenger.score})** — **({match.opponent.score})** {o_member.mention} *(First to {match.target_score})*"

        children = [
            TextDisplay(header_text),
            TextDisplay(score_text),
            Separator(spacing=discord.SeparatorSpacing.small)
        ]

        if prev_flip_text:
            children.append(TextDisplay(prev_flip_text))
            children.append(Separator(spacing=discord.SeparatorSpacing.small))

        children.append(TextDisplay(f"👉 **{current_turn_member.mention}**, choose Heads or Tails below:"))
        children.append(ActionRow(heads_btn, tails_btn))

        container = Container(*children, accent_colour=COLOR_GOLD)
        self.add_item(container)

    async def _on_heads(self, interaction: discord.Interaction):
        if interaction.user.id != self.match.current_turn_player_id:
            await interaction.response.send_message(embed=build_error_embed("It's not your turn!"), ephemeral=True)
            return
        await self.action_cb(interaction, self.match, choice="Heads")

    async def _on_tails(self, interaction: discord.Interaction):
        if interaction.user.id != self.match.current_turn_player_id:
            await interaction.response.send_message(embed=build_error_embed("It's not your turn!"), ephemeral=True)
            return
        await self.action_cb(interaction, self.match, choice="Tails")


class ColorDiceGameplayLayoutView(LayoutView):
    """Component v2 layout for active 1v1 Color Dice match with mobile-optimized button styles."""
    def __init__(
        self,
        match,
        c_member: discord.Member,
        o_member: discord.Member,
        current_turn_member: discord.Member,
        action_cb,
        prev_roll_text: str = None,
        button_style: str = "grid"
    ):
        super().__init__(timeout=None)
        self.match = match
        self.action_cb = action_cb
        self.button_style = button_style
        self._processing = False

        header_text = "### 🎨 1v1 Color Dice"
        score_text = f"> 🏆 **{c_member.display_name}** ({match.challenger.score}) vs ({match.opponent.score}) **{o_member.display_name}** • *First to {match.target_score}*"

        children = [
            TextDisplay(header_text),
            TextDisplay(score_text),
            Separator(spacing=discord.SeparatorSpacing.small)
        ]

        if prev_roll_text:
            children.append(TextDisplay(prev_roll_text))
            children.append(Separator(spacing=discord.SeparatorSpacing.small))

        turn_tag = getattr(match, "turn_count", 0)

        if button_style == "menu":
            children.append(TextDisplay(f"👉 **{current_turn_member.mention}**, tap to choose your target color:"))
            sel = Select(
                placeholder="🎨 Select a color to roll...",
                custom_id=f"select_v2_cd_{turn_tag}",
                options=[
                    discord.SelectOption(label="Red", emoji="🔴", value="red"),
                    discord.SelectOption(label="Blue", emoji="🔵", value="blue"),
                    discord.SelectOption(label="Green", emoji="🟢", value="green"),
                    discord.SelectOption(label="Yellow", emoji="🟡", value="yellow"),
                    discord.SelectOption(label="Purple", emoji="🟣", value="purple"),
                    discord.SelectOption(label="Orange", emoji="🟠", value="orange"),
                ]
            )
            sel.callback = self._on_select
            children.append(ActionRow(sel))
        elif button_style == "emoji":
            # Compact emoji pads (3x2)
            children.append(TextDisplay(f"👉 **{current_turn_member.mention}**, choose your target color to score:"))

            b_red = Button(emoji="🔴", style=discord.ButtonStyle.danger, custom_id=f"btn_v2_cd_red_{turn_tag}")
            b_red.callback = self._make_color_callback("red")
            b_blue = Button(emoji="🔵", style=discord.ButtonStyle.primary, custom_id=f"btn_v2_cd_blue_{turn_tag}")
            b_blue.callback = self._make_color_callback("blue")
            b_green = Button(emoji="🟢", style=discord.ButtonStyle.success, custom_id=f"btn_v2_cd_green_{turn_tag}")
            b_green.callback = self._make_color_callback("green")

            b_yellow = Button(emoji="🟡", style=discord.ButtonStyle.secondary, custom_id=f"btn_v2_cd_yellow_{turn_tag}")
            b_yellow.callback = self._make_color_callback("yellow")
            b_purple = Button(emoji="🟣", style=discord.ButtonStyle.secondary, custom_id=f"btn_v2_cd_purple_{turn_tag}")
            b_purple.callback = self._make_color_callback("purple")
            b_orange = Button(emoji="🟠", style=discord.ButtonStyle.secondary, custom_id=f"btn_v2_cd_orange_{turn_tag}")
            b_orange.callback = self._make_color_callback("orange")

            row1 = ActionRow(b_red, b_blue, b_green)
            row2 = ActionRow(b_yellow, b_purple, b_orange)
            children.extend([row1, row2])
        else:
            # "grid" default: 2x3 grid with full labels: 2 buttons per row, perfectly balanced, never wraps awkwardly on mobile
            children.append(TextDisplay(f"👉 **{current_turn_member.mention}**, choose your target color to score:"))

            b_red = Button(label="Red", emoji="🔴", style=discord.ButtonStyle.danger, custom_id=f"btn_v2_cd_red_{turn_tag}")
            b_red.callback = self._make_color_callback("red")
            b_blue = Button(label="Blue", emoji="🔵", style=discord.ButtonStyle.primary, custom_id=f"btn_v2_cd_blue_{turn_tag}")
            b_blue.callback = self._make_color_callback("blue")
            g1 = ActionRow(b_red, b_blue)

            b_green = Button(label="Green", emoji="🟢", style=discord.ButtonStyle.success, custom_id=f"btn_v2_cd_green_{turn_tag}")
            b_green.callback = self._make_color_callback("green")
            b_yellow = Button(label="Yellow", emoji="🟡", style=discord.ButtonStyle.secondary, custom_id=f"btn_v2_cd_yellow_{turn_tag}")
            b_yellow.callback = self._make_color_callback("yellow")
            g2 = ActionRow(b_green, b_yellow)

            b_purple = Button(label="Purple", emoji="🟣", style=discord.ButtonStyle.secondary, custom_id=f"btn_v2_cd_purple_{turn_tag}")
            b_purple.callback = self._make_color_callback("purple")
            b_orange = Button(label="Orange", emoji="🟠", style=discord.ButtonStyle.secondary, custom_id=f"btn_v2_cd_orange_{turn_tag}")
            b_orange.callback = self._make_color_callback("orange")
            g3 = ActionRow(b_purple, b_orange)

            children.extend([g1, g2, g3])

        container = Container(*children, accent_colour=COLOR_PURPLE)
        self.add_item(container)

    async def _on_select(self, interaction: discord.Interaction):
        if interaction.user.id != self.match.current_turn_player_id:
            await interaction.response.send_message(embed=build_error_embed("It's not your turn!"), ephemeral=True)
            return
        if self._processing:
            return
        self._processing = True
        choice = interaction.data["values"][0]
        await self.action_cb(interaction, self.match, choice=choice)

    def _make_color_callback(self, color_name: str):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.match.current_turn_player_id:
                await interaction.response.send_message(embed=build_error_embed("It's not your turn!"), ephemeral=True)
                return
            if self._processing:
                return
            self._processing = True
            await self.action_cb(interaction, self.match, choice=color_name)
        return callback


class BlackjackLayoutView(LayoutView):
    """Component v2 layout for 1v1 Blackjack featuring embedded table graphic and Hit/Stand controls."""
    def __init__(
        self,
        match,
        c_member: discord.Member,
        o_member: discord.Member,
        current_turn_member: discord.Member = None,
        action_cb = None,
        round_note: str = None,
        has_buttons: bool = True
    ):
        super().__init__(timeout=None)
        self.match = match
        self.action_cb = action_cb

        round_num = match.blackjack_data.get("round_num", 1) if hasattr(match, "blackjack_data") else 1
        header_text = f"### 🃏 1v1 Blackjack • Round {round_num}"
        score_text = f"> 🏆 **Match Score:** {c_member.mention} **({match.challenger.score})** — **({match.opponent.score})** {o_member.mention} *(First to {match.target_score})*"

        gallery_item = discord.MediaGalleryItem("attachment://blackjack.png")
        gallery = MediaGallery(gallery_item)

        children = [
            TextDisplay(header_text),
            TextDisplay(score_text),
            Separator(spacing=discord.SeparatorSpacing.small),
            gallery,
            Separator(spacing=discord.SeparatorSpacing.small)
        ]

        if round_note:
            children.append(TextDisplay(round_note))

        if has_buttons and current_turn_member and action_cb:
            hit_btn = Button(label="Hit", emoji="🃏", style=discord.ButtonStyle.success, custom_id="btn_v2_bj_hit")
            hit_btn.callback = self._on_hit

            stand_btn = Button(label="Stand", emoji="🛑", style=discord.ButtonStyle.danger, custom_id="btn_v2_bj_stand")
            stand_btn.callback = self._on_stand

            children.append(TextDisplay(f"👉 **{current_turn_member.mention}**, choose Hit or Stand:"))
            children.append(ActionRow(hit_btn, stand_btn))

        container = Container(*children, accent_colour=COLOR_DARK_FELT)
        self.add_item(container)

    async def _on_hit(self, interaction: discord.Interaction):
        if interaction.user.id != self.match.current_turn_player_id:
            await interaction.response.send_message(embed=build_error_embed("It's not your turn!"), ephemeral=True)
            return
        await self.action_cb(interaction, self.match, action="hit")

    async def _on_stand(self, interaction: discord.Interaction):
        if interaction.user.id != self.match.current_turn_player_id:
            await interaction.response.send_message(embed=build_error_embed("It's not your turn!"), ephemeral=True)
            return
        await self.action_cb(interaction, self.match, action="stand")


class MatchWinnerLayoutView(LayoutView):
    """Component v2 layout celebration card when a match reaches target score."""
    def __init__(self, winner: discord.Member, target_score: int, game_name: str = "Match", note: str = None):
        super().__init__(timeout=None)
        avatar_url = winner.display_avatar.url if winner and winner.display_avatar else None
        
        desc = (
            f"# 👑 CHAMPION: {winner.mention}!\n\n"
            f"**{winner.display_name}** has reached **{target_score} wins** and won the **{game_name.title()}** match!\n"
            f"🎉 *Congratulations!*"
        )
        if note:
            desc = f"{note}\n\n" + desc

        if avatar_url:
            sec = Section(desc, accessory=Thumbnail(avatar_url))
        else:
            sec = TextDisplay(desc)

        container = Container(
            sec,
            accent_colour=COLOR_GOLD
        )
        self.add_item(container)


class DiamondGameplayLayoutView(LayoutView):
    """
    Component v2 layout for 1v1 'Find the Diamond' minigame.
    Features:
    - 4x4 interactive button grid (Buttons 1-16) across 4 ActionRows
    - 5th ActionRow with a Provably Fair 'Verify' button
    - Real-time in-place card updates
    - Turn synchronization with concurrency guard
    - Authentic Discord v2 Component styling matching client requirements
    """
    def __init__(
        self,
        match,
        c_member: discord.Member,
        o_member: discord.Member,
        current_turn_member: discord.Member = None,
        action_cb = None,
        verify_cb = None,
        winner_member: discord.Member = None,
        payout: float = 0.0
    ):
        super().__init__(timeout=None)
        self.match = match
        self.current_turn_player_id = match.current_turn_player_id
        self.action_cb = action_cb
        self.verify_cb = verify_cb
        self._processing = False

        d_data = match.diamond_data
        match_id = d_data.get("match_id", 1)
        wager = d_data.get("wager", 2.0)
        revealed = d_data.get("revealed", {})
        press_count = d_data.get("presses", 0)
        is_finished = d_data.get("is_finished", False)
        winner_tile = d_data.get("winner_tile", None)
        turn_tag = getattr(match, "turn_count", 0)

        # Header information
        header_text = "# 💎 Find the Diamond"
        sub_text = f"**#{match_id}** · **${wager:.2f} each**"
        matchup_text = f"{c_member.mention} **vs** {o_member.mention}"

        content_lines = [header_text, sub_text, matchup_text, ""]

        if is_finished and winner_member and winner_tile:
            content_lines.append(f"🏆 **{winner_member.mention} found the diamond on button {winner_tile}! +${payout:.2f}**")
            content_lines.append(f"*{press_count} presses*")
        else:
            if current_turn_member:
                content_lines.append(f"👉 **{current_turn_member.mention}**, it's your turn to pick a button!")
            if press_count > 0:
                content_lines.append(f"*{press_count} presses*")

        children = [
            TextDisplay("\n".join(content_lines)),
            Separator(spacing=discord.SeparatorSpacing.small)
        ]

        # 4x4 Grid of Buttons (4 ActionRows of 4 buttons)
        for row_idx in range(4):
            row_buttons = []
            for col_idx in range(4):
                tile_num = row_idx * 4 + col_idx + 1

                if tile_num in revealed:
                    is_diamond = revealed[tile_num]
                    if is_diamond:
                        btn = Button(
                            emoji="💎",
                            style=discord.ButtonStyle.success,
                            disabled=True,
                            custom_id=f"btn_v2_dm_{tile_num}_hit"
                        )
                    else:
                        btn = Button(
                            emoji="❌",
                            style=discord.ButtonStyle.secondary,
                            disabled=True,
                            custom_id=f"btn_v2_dm_{tile_num}_miss"
                        )
                else:
                    if is_finished:
                        btn = Button(
                            label=str(tile_num),
                            style=discord.ButtonStyle.secondary,
                            disabled=True,
                            custom_id=f"btn_v2_dm_{tile_num}_done"
                        )
                    else:
                        btn = Button(
                            label=str(tile_num),
                            style=discord.ButtonStyle.primary,
                            custom_id=f"btn_v2_dm_{tile_num}_{turn_tag}"
                        )
                        btn.callback = self._make_tile_callback(tile_num)

                row_buttons.append(btn)
            children.append(ActionRow(*row_buttons))

        # 5th ActionRow: Provably Fair Verify Button
        verify_btn = Button(
            label="Verify",
            emoji="🔍",
            style=discord.ButtonStyle.secondary,
            custom_id=f"btn_v2_dm_verify_{match_id}"
        )
        verify_btn.callback = self._on_verify
        children.append(ActionRow(verify_btn))

        container = Container(*children, accent_colour=COLOR_GOLD)
        self.add_item(container)

    def _make_tile_callback(self, tile_num: int):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.current_turn_player_id:
                await interaction.response.send_message(embed=build_error_embed("It's not your turn!"), ephemeral=True)
                return
            if self._processing:
                return
            self._processing = True
            await self.action_cb(interaction, self.match, tile=tile_num)
        return callback

    async def _on_verify(self, interaction: discord.Interaction):
        if self.verify_cb:
            await self.verify_cb(interaction, self.match)
