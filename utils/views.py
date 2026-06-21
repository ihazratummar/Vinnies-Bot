import discord
from utils.embeds import build_error_embed

class ChallengeView(discord.ui.View):
    def __init__(self, challenger_id: int, opponent_id: int, accept_callback, cancel_callback):
        super().__init__(timeout=None)
        self.challenger_id = challenger_id
        self.opponent_id = opponent_id
        self.accept_callback = accept_callback
        self.cancel_callback = cancel_callback

    @discord.ui.button(label="Accept", style=discord.ButtonStyle.success, custom_id="btn_accept", emoji="✅")
    async def accept_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.opponent_id:
            await interaction.response.send_message(embed=build_error_embed("Only the challenged player can accept!"), ephemeral=True)
            return
        await self.accept_callback(interaction)

    @discord.ui.button(label="Decline/Cancel", style=discord.ButtonStyle.danger, custom_id="btn_cancel", emoji="❌")
    async def cancel_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id not in (self.challenger_id, self.opponent_id):
            await interaction.response.send_message(embed=build_error_embed("You cannot cancel this match!"), ephemeral=True)
            return
        await self.cancel_callback(interaction)

class GameplayView(discord.ui.View):
    def __init__(self, match, action_callback, cancel_callback):
        super().__init__(timeout=None)
        self.match = match
        self.action_callback = action_callback
        # cancel_callback is ignored here since players can no longer cancel mid-match
        
        if self.match.game_type.value == "dice":
            action_btn = discord.ui.Button(label="Roll Dice", style=discord.ButtonStyle.primary, custom_id="btn_dice", emoji="🎲")
            action_btn.callback = self._action_btn_callback_dice
            self.add_item(action_btn)
        else:
            heads_btn = discord.ui.Button(label="Heads", style=discord.ButtonStyle.primary, custom_id="btn_heads", emoji="🪙")
            heads_btn.callback = self._action_btn_callback_heads
            self.add_item(heads_btn)
            
            tails_btn = discord.ui.Button(label="Tails", style=discord.ButtonStyle.primary, custom_id="btn_tails", emoji="🪙")
            tails_btn.callback = self._action_btn_callback_tails
            self.add_item(tails_btn)

    async def _action_btn_callback_dice(self, interaction: discord.Interaction):
        if interaction.user.id != self.match.current_turn_player_id:
            await interaction.response.send_message(embed=build_error_embed("It's not your turn!"), ephemeral=True)
            return
        await self.action_callback(interaction, self.match, choice=None)

    async def _action_btn_callback_heads(self, interaction: discord.Interaction):
        if interaction.user.id != self.match.current_turn_player_id:
            await interaction.response.send_message(embed=build_error_embed("It's not your turn!"), ephemeral=True)
            return
        await self.action_callback(interaction, self.match, choice="Heads")

    async def _action_btn_callback_tails(self, interaction: discord.Interaction):
        if interaction.user.id != self.match.current_turn_player_id:
            await interaction.response.send_message(embed=build_error_embed("It's not your turn!"), ephemeral=True)
            return
        await self.action_callback(interaction, self.match, choice="Tails")
