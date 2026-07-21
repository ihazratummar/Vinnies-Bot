import discord
import random
from discord.ext import commands
from models.match import GameType
from services.match_manager import match_manager
from utils.checks import in_ticket_channel
from utils.views import ChallengeView, GameplayView, RPSView
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

    async def get_safe_member(self, guild, user_id):
        member = guild.get_member(user_id)
        if not member:
            try:
                member = await guild.fetch_member(user_id)
            except discord.NotFound:
                return None
        return member

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
        await ctx.send(embed=build_challenge_embed(ctx.author, opponent, "dice", 5), view=view)

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
        await ctx.send(embed=build_challenge_embed(ctx.author, opponent, "coinflip", 5), view=view)

    @commands.hybrid_command(name="rps")
    @commands.cooldown(1, 2, commands.BucketType.user)
    @in_ticket_channel()
    async def rps(self, ctx, opponent: discord.Member):
        """Challenges a user to a Rock Paper Scissors match."""
        if opponent.bot:
            await ctx.send(embed=build_error_embed("You cannot challenge a bot!"), ephemeral=True)
            return

        success, msg = await match_manager.create_challenge(ctx.guild.id, ctx.author.id, opponent.id, GameType.RPS, ctx.channel.id)
        if not success:
            await ctx.send(embed=build_error_embed(msg), ephemeral=True)
            return
            
        view = ChallengeView(ctx.author.id, opponent.id, self.accept_challenge, self.cancel_match)
        await ctx.send(embed=build_challenge_embed(ctx.author, opponent, "rps", 3), view=view)

    async def accept_challenge(self, interaction: discord.Interaction):
        await interaction.response.defer()
        success, msg, match = await match_manager.accept_challenge(interaction.guild.id, interaction.user.id, interaction.channel.id)
        if not success:
            await interaction.followup.send(embed=build_error_embed(msg), ephemeral=True)
            return
            
        challenger = await self.get_safe_member(interaction.guild, match.challenger.id)
        opponent = interaction.user
        game_type = match.game_type.value
        
        if not challenger:
            await interaction.followup.send(embed=build_error_embed("The challenger could not be found! They may have left the server."), ephemeral=True)
            await match_manager.cancel_challenge_or_match(interaction.guild.id, match.challenger.id)
            return
        
        # Remove buttons from original challenge message
        try:
            await interaction.message.edit(view=None)
        except:
            pass
        
        if game_type == GameType.RPS.value:
            match.rps_first_picker_id = match.challenger.id
            view = RPSView(match, self.play_turn)
        else:
            view = GameplayView(match, self.play_turn, self.cancel_match)
            
        await interaction.followup.send(embed=build_match_start_embed(challenger, opponent, game_type), view=view)

    async def cancel_match(self, interaction: discord.Interaction):
        await interaction.response.defer()
        success, msg, match = await match_manager.cancel_challenge_or_match(interaction.guild.id, interaction.user.id)
        if success:
            try:
                await interaction.message.edit(view=None)
            except:
                pass
            await interaction.followup.send(embed=build_success_embed(msg))
        else:
            await interaction.followup.send(embed=build_error_embed(msg), ephemeral=True)

    async def _handle_dice(self, interaction: discord.Interaction, match):
        if getattr(self.bot, "forced_dice_result", None) is not None:
            result = self.bot.forced_dice_result
            if hasattr(self.bot, "clear_forced_dice"):
                self.bot.clear_forced_dice()
            else:
                self.bot.forced_dice_result = None
                
            half = result // 2
            die1 = half
            die2 = result - half
            if die1 > 1 and die2 < 6 and random.choice([True, False]):
                die1 -= 1
                die2 += 1
            display_result = f"**{die1}** and **{die2}** (Total: **{result}**)"
        else:
            die1 = random.randint(1, 6)
            die2 = random.randint(1, 6)
            result = die1 + die2
            display_result = f"**{die1}** and **{die2}** (Total: **{result}**)"

        await interaction.followup.send(embed=build_turn_result_embed(interaction.user, display_result))
        match.current_round_score[interaction.user.id] = result
        return len(match.current_round_score) == 2

    async def _handle_coinflip(self, interaction: discord.Interaction, match, choice):
        choices = ["Heads", "Tails"]
        display_result = random.choice(choices)
        
        if choice == display_result:
            winner_id = interaction.user.id
            loser_id = match.challenger.id if interaction.user.id == match.opponent.id else match.opponent.id
        else:
            loser_id = interaction.user.id
            winner_id = match.challenger.id if interaction.user.id == match.opponent.id else match.opponent.id

        await interaction.followup.send(embed=build_turn_result_embed(interaction.user, f"You chose **{choice}**. The coin landed on **{display_result}**!"))
        match.current_round_score[winner_id] = 2
        match.current_round_score[loser_id] = 1
        return True

    async def _handle_rps(self, interaction: discord.Interaction, match, choice):
        match.rps_choices[interaction.user.id] = choice
        if len(match.rps_choices) == 1:
            await match_manager.next_turn(match)
            next_player = await self.get_safe_member(interaction.guild, match.current_turn_player_id)
            mention = next_player.mention if next_player else "Player"
            
            try:
                await interaction.message.edit(view=None)
            except: pass
            
            view = RPSView(match, self.play_turn)
            await interaction.followup.send(content=f"{interaction.user.mention} has locked in their choice!\n\n{mention}, it's your turn!", view=view)
            return False
        else:
            c_choice = match.rps_choices[match.challenger.id]
            o_choice = match.rps_choices[match.opponent.id]
            
            c_member = await self.get_safe_member(interaction.guild, match.challenger.id)
            o_member = await self.get_safe_member(interaction.guild, match.opponent.id)
            c_name = c_member.display_name if c_member else "Challenger"
            o_name = o_member.display_name if o_member else "Opponent"
            
            result_text = f"**{c_name}** chose **{c_choice}**\n**{o_name}** chose **{o_choice}**\n\n"
            
            if c_choice == o_choice:
                match.current_round_score[match.challenger.id] = 0
                match.current_round_score[match.opponent.id] = 0
                result_text += "**It's a tie!**"
            else:
                wins = {"Rock": "Scissors", "Paper": "Rock", "Scissors": "Paper"}
                if wins[c_choice] == o_choice:
                    match.current_round_score[match.challenger.id] = 2
                    match.current_round_score[match.opponent.id] = 1
                    result_text += f"**{c_name}** wins this round!"
                else:
                    match.current_round_score[match.opponent.id] = 2
                    match.current_round_score[match.challenger.id] = 1
                    result_text += f"**{o_name}** wins this round!"
            
            await interaction.followup.send(embed=build_turn_result_embed(interaction.user, result_text))
            return True

    async def _resolve_round(self, interaction: discord.Interaction, match):
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
            if game_over:
                await match_manager.end_match(match)
                winner_member = await self.get_safe_member(interaction.guild, winner_id)
                if winner_member:
                    await interaction.followup.send(embed=build_match_winner_embed(winner_member, match.target_score))
                return
            else:
                await match_manager.next_turn(match)
                
                if match.game_type == GameType.RPS:
                    match.rps_first_picker_id = match.opponent.id if match.rps_first_picker_id == match.challenger.id else match.challenger.id
                    match.current_turn_player_id = match.rps_first_picker_id
                    match.rps_choices.clear()
                    view = RPSView(match, self.play_turn)
                else:
                    match.current_turn_player_id = winner_id
                    view = GameplayView(match, self.play_turn, self.cancel_match)
                
                winner_member = await self.get_safe_member(interaction.guild, winner_id)
                challenger_member = await self.get_safe_member(interaction.guild, match.challenger.id)
                opponent_member = await self.get_safe_member(interaction.guild, match.opponent.id)
                next_player_member = await self.get_safe_member(interaction.guild, match.current_turn_player_id)
                
                await interaction.followup.send(
                    embed=build_round_winner_embed(
                        winner_member, 
                        challenger_member, 
                        opponent_member, 
                        match.challenger.score, 
                        match.opponent.score,
                        next_player_member
                    ),
                    view=view
                )
        else:
            await interaction.followup.send(embed=build_error_embed("It's a tie! No points awarded this round."))
            
            if match.game_type == GameType.RPS:
                match.rps_first_picker_id = match.opponent.id if match.rps_first_picker_id == match.challenger.id else match.challenger.id
                match.current_turn_player_id = match.rps_first_picker_id
                match.rps_choices.clear()
                view = RPSView(match, self.play_turn)
            else:
                match.current_turn_player_id = match.challenger.id 
                view = GameplayView(match, self.play_turn, self.cancel_match)
                
            challenger_member = await self.get_safe_member(interaction.guild, match.current_turn_player_id)
            mention = challenger_member.mention if challenger_member else "Player"
            await interaction.followup.send(content=f"{mention}, it's your turn to pick/roll/flip again.", view=view)

    async def play_turn(self, interaction: discord.Interaction, match, choice=None):
        await interaction.response.defer()
        if not hasattr(match, "current_round_score"):
            match.current_round_score = {}

        round_over = False
        if match.game_type == GameType.DICE:
            round_over = await self._handle_dice(interaction, match)
        elif match.game_type == GameType.COINFLIP:
            round_over = await self._handle_coinflip(interaction, match, choice)
        elif match.game_type == GameType.RPS:
            round_over = await self._handle_rps(interaction, match, choice)

        if not round_over:
            if match.game_type != GameType.RPS:
                try:
                    await interaction.message.edit(view=None)
                except:
                    pass
                await match_manager.next_turn(match)
                next_player = await self.get_safe_member(interaction.guild, match.current_turn_player_id)
                mention = next_player.mention if next_player else "Player"
                view = GameplayView(match, self.play_turn, self.cancel_match)
                await interaction.followup.send(content=f"{mention}, it's your turn!", view=view)
            return

        try:
            await interaction.message.edit(view=None)
        except:
            pass
            
        await self._resolve_round(interaction, match)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        """Cleans up matches if the channel (like a ticket) gets deleted mid-match."""
        await match_manager.cancel_matches_in_channel(channel.id)

async def setup(bot):
    await bot.add_cog(GamblingCog(bot))
