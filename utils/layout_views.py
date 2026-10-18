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
    def __init__(self, challenger: discord.Member, opponent: discord.Member, game_type: str, target_score: int, accept_cb, decline_cb):
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
        desc_text = (
            f"**{challenger.display_name}** has challenged **{opponent.display_name}** to a **{formatted_game}** match!\n"
            f"🎯 **Rules:** First to **{target_score}** wins.\n\n"
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
        button_style: str = "emoji"
    ):
        super().__init__(timeout=None)
        self.match = match
        self.action_cb = action_cb
        self.button_style = button_style

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

        if button_style == "menu":
            children.append(TextDisplay(f"👉 **{current_turn_member.mention}**, tap to choose your color:"))
            sel = Select(
                placeholder="🎨 Select a color to roll...",
                custom_id="select_v2_cd_color",
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
        elif button_style == "grid":
            # 2x3 grid with full labels: 2 buttons per row, perfectly balanced and never wraps on mobile
            children.append(TextDisplay(f"👉 **{current_turn_member.mention}**, choose a color to roll:"))
            g1 = ActionRow(
                Button(label="Red", emoji="🔴", style=discord.ButtonStyle.danger, custom_id="btn_v2_cd_red"),
                Button(label="Blue", emoji="🔵", style=discord.ButtonStyle.primary, custom_id="btn_v2_cd_blue"),
            )
            g1.children[0].callback = self._make_color_callback("red")
            g1.children[1].callback = self._make_color_callback("blue")

            g2 = ActionRow(
                Button(label="Green", emoji="🟢", style=discord.ButtonStyle.success, custom_id="btn_v2_cd_green"),
                Button(label="Yellow", emoji="🟡", style=discord.ButtonStyle.secondary, custom_id="btn_v2_cd_yellow"),
            )
            g2.children[0].callback = self._make_color_callback("green")
            g2.children[1].callback = self._make_color_callback("yellow")

            g3 = ActionRow(
                Button(label="Purple", emoji="🟣", style=discord.ButtonStyle.secondary, custom_id="btn_v2_cd_purple"),
                Button(label="Orange", emoji="🟠", style=discord.ButtonStyle.secondary, custom_id="btn_v2_cd_orange"),
            )
            g3.children[0].callback = self._make_color_callback("purple")
            g3.children[1].callback = self._make_color_callback("orange")

            children.extend([g1, g2, g3])
        else:
            # "emoji" default: Ultra-compact square emoji buttons (3x2), reduces width by 65% so it NEVER wraps on mobile!
            children.append(TextDisplay(f"👉 **{current_turn_member.mention}**, tap a color pad to roll:"))

            row1 = ActionRow(
                Button(emoji="🔴", style=discord.ButtonStyle.danger, custom_id="btn_v2_cd_red"),
                Button(emoji="🔵", style=discord.ButtonStyle.primary, custom_id="btn_v2_cd_blue"),
                Button(emoji="🟢", style=discord.ButtonStyle.success, custom_id="btn_v2_cd_green"),
            )
            row1.children[0].callback = self._make_color_callback("red")
            row1.children[1].callback = self._make_color_callback("blue")
            row1.children[2].callback = self._make_color_callback("green")

            row2 = ActionRow(
                Button(emoji="🟡", style=discord.ButtonStyle.secondary, custom_id="btn_v2_cd_yellow"),
                Button(emoji="🟣", style=discord.ButtonStyle.secondary, custom_id="btn_v2_cd_purple"),
                Button(emoji="🟠", style=discord.ButtonStyle.secondary, custom_id="btn_v2_cd_orange"),
            )
            row2.children[0].callback = self._make_color_callback("yellow")
            row2.children[1].callback = self._make_color_callback("purple")
            row2.children[2].callback = self._make_color_callback("orange")

            children.extend([row1, row2])

        container = Container(*children, accent_colour=COLOR_PURPLE)
        self.add_item(container)

    async def _on_select(self, interaction: discord.Interaction):
        if interaction.user.id != self.match.current_turn_player_id:
            await interaction.response.send_message(embed=build_error_embed("It's not your turn!"), ephemeral=True)
            return
        choice = interaction.data["values"][0]
        await self.action_cb(interaction, self.match, choice=choice)

    def _make_color_callback(self, color_name: str):
        async def callback(interaction: discord.Interaction):
            if interaction.user.id != self.match.current_turn_player_id:
                await interaction.response.send_message(embed=build_error_embed("It's not your turn!"), ephemeral=True)
                return
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
