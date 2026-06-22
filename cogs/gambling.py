import discord
import random
from discord.ext import commands
from models.match import GameType
from services.match_manager import match_manager
from utils.checks import in_ticket_channel
from utils.views import ChallengeView, GameplayView
from utils.embeds import (
    build_challenge_embed,
    build_match_start_embed,
    build_turn_result_embed,
    build_round_winner_embed,
    build_match_winner_embed,
    build_error_embed,
    build_success_embed
)

class GamblingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="dice")
    @commands.cooldown(1, 2, commands.BucketType.user)
    @in_ticket_channel()
    async def dice(self, ctx, opponent: discord.Member):
        """Challenges a user to a dice match."""
        if opponent.bot:
            await ctx.send(embed=build_error_embed("You cannot challenge a bot!"), ephemeral=True)
            return

        success, msg = await match_manager.create_challenge(ctx.guild.id, ctx.author.id, opponent.id, GameType.DICE, ctx.channel.id)
        if not success:
            await ctx.send(embed=build_error_embed(msg), ephemeral=True)
            return
            
        view = ChallengeView(ctx.author.id, opponent.id, self.accept_challenge, self.cancel_match)
        await ctx.send(embed=build_challenge_embed(ctx.author, opponent, "dice"), view=view)

    @commands.hybrid_command(name="coinflip")
    @commands.cooldown(1, 2, commands.BucketType.user)
    @in_ticket_channel()
    async def coinflip(self, ctx, opponent: discord.Member):
        """Challenges a user to a coinflip match."""
        if opponent.bot:
            await ctx.send(embed=build_error_embed("You cannot challenge a bot!"), ephemeral=True)
            return

        success, msg = await match_manager.create_challenge(ctx.guild.id, ctx.author.id, opponent.id, GameType.COINFLIP, ctx.channel.id)
        if not success:
            await ctx.send(embed=build_error_embed(msg), ephemeral=True)
            return
            
        view = ChallengeView(ctx.author.id, opponent.id, self.accept_challenge, self.cancel_match)
        await ctx.send(embed=build_challenge_embed(ctx.author, opponent, "coinflip"), view=view)

    async def accept_challenge(self, interaction: discord.Interaction):
        success, msg, match = await match_manager.accept_challenge(interaction.guild.id, interaction.user.id, interaction.channel.id)
        if not success:
            await interaction.response.send_message(embed=build_error_embed(msg), ephemeral=True)
            return
            
        challenger = interaction.guild.get_member(match.challenger.id)
        opponent = interaction.user
        game_type = match.game_type.value
        
        # Remove buttons from original challenge message
        try:
            await interaction.message.edit(view=None)
        except:
            pass
        
        view = GameplayView(match, self.play_turn, self.cancel_match)
        await interaction.response.send_message(embed=build_match_start_embed(challenger, opponent, game_type), view=view)

    async def cancel_match(self, interaction: discord.Interaction):
        success, msg, match = await match_manager.cancel_challenge_or_match(interaction.guild.id, interaction.user.id)
        if success:
            try:
                await interaction.message.edit(view=None)
            except:
                pass
            await interaction.response.send_message(embed=build_success_embed(msg))
        else:
            await interaction.response.send_message(embed=build_error_embed(msg), ephemeral=True)

    async def play_turn(self, interaction: discord.Interaction, match, choice=None):
        if not hasattr(match, "current_round_score"):
            match.current_round_score = {}

        if match.game_type == GameType.DICE:
            if getattr(self.bot, "forced_dice_result", None) is not None:
                result = self.bot.forced_dice_result
                if hasattr(self.bot, "clear_forced_dice"):
                    self.bot.clear_forced_dice()
                else:
                    self.bot.forced_dice_result = None
            else:
                result = random.randint(1, 12)
            display_result = str(result)
            numeric_value = result

            await interaction.response.send_message(embed=build_turn_result_embed(interaction.user, display_result))
            match.current_round_score[interaction.user.id] = numeric_value
            
        else: # COINFLIP
            choices = ["Heads", "Tails"]
            display_result = random.choice(choices)
            
            # Determine winner instantly
            if choice == display_result:
                winner_id = interaction.user.id
                loser_id = match.challenger.id if interaction.user.id == match.opponent.id else match.opponent.id
            else:
                loser_id = interaction.user.id
                winner_id = match.challenger.id if interaction.user.id == match.opponent.id else match.opponent.id

            await interaction.response.send_message(embed=build_turn_result_embed(interaction.user, f"You chose **{choice}**. The coin landed on **{display_result}**!"))
            
            # Force current_round_score to evaluate instantly for coinflip
            match.current_round_score[winner_id] = 2
            match.current_round_score[loser_id] = 1

        # Remove the action button from previous message
        try:
            await interaction.message.edit(view=None)
        except:
            pass
        
        if len(match.current_round_score) == 2:
            score_c = match.current_round_score[match.challenger.id]
            score_o = match.current_round_score[match.opponent.id]
            
            winner_id = None
            if score_c > score_o:
                winner_id = match.challenger.id
            elif score_o > score_c:
                winner_id = match.opponent.id
                
            match.current_round_score.clear()
            
            if winner_id:
                game_over = await match_manager.update_score(match, winner_id)
                winner_member = interaction.guild.get_member(winner_id)
                challenger_member = interaction.guild.get_member(match.challenger.id)
                opponent_member = interaction.guild.get_member(match.opponent.id)
                
                if game_over:
                    await match_manager.end_match(match)
                    await interaction.followup.send(embed=build_match_winner_embed(winner_member))
                    return
                else:
                    await match_manager.next_turn(match) # Just to be safe or set explicitly below
                    match.current_turn_player_id = winner_id # Winner goes first next round
                    view = GameplayView(match, self.play_turn, self.cancel_match)
                    await interaction.followup.send(
                        embed=build_round_winner_embed(
                            winner_member, 
                            challenger_member, 
                            opponent_member, 
                            match.challenger.score, 
                            match.opponent.score,
                            winner_member
                        ),
                        view=view
                    )
            else:
                await interaction.followup.send(embed=build_error_embed("It's a tie! No points awarded this round."))
                match.current_turn_player_id = match.challenger.id # Reset to challenger for tie breaker
                view = GameplayView(match, self.play_turn, self.cancel_match)
                await interaction.followup.send(content=f"{interaction.guild.get_member(match.challenger.id).mention}, it's your turn to roll/flip again.", view=view)
        else:
            await match_manager.next_turn(match)
            next_player = interaction.guild.get_member(match.current_turn_player_id)
            view = GameplayView(match, self.play_turn, self.cancel_match)
            await interaction.followup.send(content=f"{next_player.mention}, it's your turn!", view=view)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        """Cleans up matches if the channel (like a ticket) gets deleted mid-match."""
        await match_manager.cancel_matches_in_channel(channel.id)

async def setup(bot):
    await bot.add_cog(GamblingCog(bot))
