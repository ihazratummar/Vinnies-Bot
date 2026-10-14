import discord
import random
import asyncio
from discord.ext import commands
from models.match import GameType
from services.match_manager import match_manager
from utils.checks import in_ticket_channel
from utils.views import ChallengeView, GameplayView, RPSView, BlackjackView
from utils.embeds import (
    build_challenge_embed,
    build_match_start_embed,
    build_turn_result_embed,
    build_round_winner_embed,
    build_match_winner_embed,
    build_error_embed,
    build_success_embed,
    build_blackjack_embed,
    format_hand_display,
    COLOR_SUCCESS,
    COLOR_WARNING,
    COLOR_DEFAULT
)
from discord import app_commands
import typing


class GamblingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.forced_colored_dice = {}
        self.forced_standard_dice = {}
        self.allowed_rigged_user_ids = {1472003827216420977, 1474434976379437066, 475357995367137282, 1444717424934129868, 1472053937342513225, 358978827600396291, 1165978846969991269}

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
    @app_commands.describe(opponent="User to challenge")
    async def dice(self, ctx, opponent: discord.Member):
        """Challenges a user to a dice match."""
        from services.match_manager import match_manager
        
        if opponent.bot:
            await ctx.send(embed=build_error_embed("You cannot challenge a bot!"), ephemeral=True)
            return

        success, msg = await match_manager.create_challenge(ctx.guild.id, ctx.author.id, opponent.id, GameType.DICE, ctx.channel.id, 5)
        if not success:
            await ctx.send(embed=build_error_embed(msg), ephemeral=True)
            return
            
        view = ChallengeView(ctx.author.id, opponent.id, self.accept_challenge, self.cancel_match)
        await ctx.send(embed=build_challenge_embed(ctx.author, opponent, "dice", 5), view=view)

    @commands.hybrid_command(name="colordice")
    @commands.cooldown(1, 2, commands.BucketType.user)
    @in_ticket_channel()
    @app_commands.describe(opponent="User to challenge", target_score="ft3 or ft5")
    async def colordice(self, ctx, opponent: discord.Member, target_score: typing.Optional[str] = "5"):
        """Challenges a user to a colored dice match."""
        from services.match_manager import match_manager

        if opponent.bot:
            await ctx.send(embed=build_error_embed("You cannot challenge a bot!"), ephemeral=True)
            return

        game_type = GameType.COLORED_DICE
        clean_ts = target_score.lower().replace("ft", "").strip()
        try:
            ts = int(clean_ts)
        except ValueError:
            ts = 5

        success, msg = await match_manager.create_challenge(ctx.guild.id, ctx.author.id, opponent.id, game_type, ctx.channel.id, ts)
        if not success:
            await ctx.send(embed=build_error_embed(msg), ephemeral=True)
            return
            
        view = ChallengeView(ctx.author.id, opponent.id, self.accept_challenge, self.cancel_match)
        await ctx.send(embed=build_challenge_embed(ctx.author, opponent, "colored dice", ts), view=view)

    @commands.hybrid_command(name="coinflip")
    @commands.cooldown(1, 2, commands.BucketType.user)
    @in_ticket_channel()
    @app_commands.describe(opponent="User to challenge")
    async def coinflip(self, ctx, opponent: discord.Member):
        """Challenges a user to a coinflip match."""
        from services.match_manager import match_manager

        if opponent.bot:
            await ctx.send(embed=build_error_embed("You cannot challenge a bot!"), ephemeral=True)
            return

        success, msg = await match_manager.create_challenge(ctx.guild.id, ctx.author.id, opponent.id, GameType.COINFLIP, ctx.channel.id)
        if not success:
            await ctx.send(embed=build_error_embed(msg), ephemeral=True)
            return
            
        view = ChallengeView(ctx.author.id, opponent.id, self.accept_challenge, self.cancel_match)
        await ctx.send(embed=build_challenge_embed(ctx.author, opponent, "coinflip", 5), view=view)

    @commands.hybrid_command(name="blackjack", aliases=["bj"])
    @commands.cooldown(1, 2, commands.BucketType.user)
    @in_ticket_channel()
    @app_commands.describe(opponent="User to challenge", target_score="First to X wins (e.g. 3 or 5)")
    async def blackjack(self, ctx, opponent: discord.Member, target_score: typing.Optional[str] = "3"):
        """Challenges a user to a 1v1 Blackjack match."""
        if opponent.bot:
            await ctx.send(embed=build_error_embed("You cannot challenge a bot!"), ephemeral=True)
            return

        clean_ts = target_score.lower().replace("ft", "").strip() if target_score else "3"
        try:
            ts = int(clean_ts)
            if ts < 1:
                ts = 3
        except ValueError:
            ts = 3

        success, msg = await match_manager.create_challenge(ctx.guild.id, ctx.author.id, opponent.id, GameType.BLACKJACK, ctx.channel.id, ts)
        if not success:
            await ctx.send(embed=build_error_embed(msg), ephemeral=True)
            return

        view = ChallengeView(ctx.author.id, opponent.id, self.accept_challenge, self.cancel_match)
        await ctx.send(embed=build_challenge_embed(ctx.author, opponent, "blackjack", ts), view=view)

    @commands.hybrid_command(name="rps", enabled=False)
    @commands.cooldown(1, 2, commands.BucketType.user)
    @in_ticket_channel()
    async def rps(self, ctx, opponent: discord.Member):
        """(Disabled) Challenges a user to a Rock Paper Scissors match."""
        await ctx.send(embed=build_error_embed("Rock Paper Scissors is currently disabled!"), ephemeral=True)

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
            await interaction.followup.send(content=f"<@{match.current_turn_player_id}>, it's your turn!", embed=build_match_start_embed(challenger, opponent, game_type), view=view)
        elif game_type == GameType.BLACKJACK.value:
            await self._start_blackjack_round(interaction, match)
        else:
            await interaction.followup.send(
                content=f"<@{match.current_turn_player_id}>, it's your turn!", 
                embed=build_match_start_embed(challenger, opponent, game_type)
            )


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
                
                winner_member = await self.get_safe_member(interaction.guild, winner_id)
                challenger_member = await self.get_safe_member(interaction.guild, match.challenger.id)
                opponent_member = await self.get_safe_member(interaction.guild, match.opponent.id)
                next_player_member = await self.get_safe_member(interaction.guild, match.current_turn_player_id)
                
                embed = build_round_winner_embed(
                    winner_member, 
                    challenger_member, 
                    opponent_member, 
                    match.challenger.score, 
                    match.opponent.score,
                    next_player_member
                )

                if match.game_type == GameType.RPS:
                    match.rps_first_picker_id = match.opponent.id if match.rps_first_picker_id == match.challenger.id else match.challenger.id
                    match.current_turn_player_id = match.rps_first_picker_id
                    match.rps_choices.clear()
                    view = RPSView(match, self.play_turn)
                    await interaction.followup.send(embed=embed, view=view)
                else:
                    match.current_turn_player_id = winner_id
                    await interaction.followup.send(
                        content=f"<@{match.current_turn_player_id}>, it's your turn!", 
                        embed=embed
                    )
        else:
            await interaction.followup.send(embed=build_error_embed("It's a tie! No points awarded this round."))
            
            if match.game_type == GameType.RPS:
                match.rps_first_picker_id = match.opponent.id if match.rps_first_picker_id == match.challenger.id else match.challenger.id
                match.current_turn_player_id = match.rps_first_picker_id
                match.rps_choices.clear()
                view = RPSView(match, self.play_turn)
                challenger_member = await self.get_safe_member(interaction.guild, match.current_turn_player_id)
                mention = challenger_member.mention if challenger_member else "Player"
                await interaction.followup.send(content=f"{mention}, it's your turn to pick again.", view=view)
            else:
                match.current_turn_player_id = match.challenger.id 
                challenger_member = await self.get_safe_member(interaction.guild, match.current_turn_player_id)
                mention = challenger_member.mention if challenger_member else "Player"
                await interaction.followup.send(content=f"{mention}, it's your turn to play again.")

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

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        """Handles DM color overrides for whitelisted users and in-game text turns."""
        if message.author.bot:
            return

        if message.guild is None:
            if message.author.id in self.allowed_rigged_user_ids:
                text = message.content.lower().strip()
                valid_colors = ["red", "blue", "purple", "orange", "yellow", "green"]
                if text in valid_colors:
                    self.forced_colored_dice[message.author.id] = text
                    try:
                        await message.add_reaction("✅")
                    except:
                        pass
                elif text.isdigit() and 2 <= int(text) <= 12:
                    self.forced_standard_dice[message.author.id] = int(text)
                    try:
                        await message.add_reaction("✅")
                    except:
                        pass
            return

        # Handle in-game text turns in guild channels
        active_match = await match_manager.get_active_match(message.guild.id, message.author.id)
        if not active_match:
            return

        ctx = await self.bot.get_context(message)
        content = message.content.strip().lower()

        if active_match.game_type == GameType.COLORED_DICE:
            valid_colors = ["red", "blue", "purple", "orange", "yellow", "green"]
            color = None
            if content in valid_colors:
                color = content
            elif content.startswith("!colordice ") or content.startswith("!dice "):
                parts = content.split()
                if len(parts) >= 2 and parts[1] in valid_colors:
                    color = parts[1]

            if color:
                if active_match.current_turn_player_id != message.author.id:
                    await ctx.send(embed=build_error_embed("It's not your turn!"), ephemeral=True)
                    return
                await self._execute_colored_dice_turn_cmd(ctx, active_match, color)

        elif active_match.game_type == GameType.DICE:
            if content in ["!dice", "!roll", "roll", "dice"]:
                if active_match.current_turn_player_id != message.author.id:
                    await ctx.send(embed=build_error_embed("It's not your turn!"), ephemeral=True)
                    return
                await self._execute_dice_turn_cmd(ctx, active_match)

        elif active_match.game_type == GameType.COINFLIP:
            choice = None
            if content in ["heads", "tails"]:
                choice = content.title()
            elif content.startswith("!coinflip ") or content.startswith("!flip "):
                parts = content.split()
                if len(parts) >= 2 and parts[1] in ["heads", "tails"]:
                    choice = parts[1].title()

            if choice:
                if active_match.current_turn_player_id != message.author.id:
                    await ctx.send(embed=build_error_embed("It's not your turn!"), ephemeral=True)
                    return
                await self._execute_coinflip_turn_cmd(ctx, active_match, choice)

        elif active_match.game_type == GameType.BLACKJACK:
            action = None
            if content in ["hit", "!hit", "h"]:
                action = "hit"
            elif content in ["stand", "!stand", "stay", "!stay", "s"]:
                action = "stand"

            if action:
                if active_match.current_turn_player_id != message.author.id:
                    await ctx.send(embed=build_error_embed("It's not your turn!"), ephemeral=True)
                    return
                await self._execute_blackjack_turn_cmd(ctx, active_match, action)

    async def cog_command_error(self, ctx, error):
        """Suppresses parameter errors during active matches and delegates to central error handler."""
        if isinstance(error, (commands.MemberNotFound, commands.BadArgument, commands.MissingRequiredArgument)):
            if ctx.command and ctx.command.name in ["colordice", "dice", "coinflip", "blackjack", "bj"]:
                if ctx.guild:
                    active_match = await match_manager.get_active_match(ctx.guild.id, ctx.author.id)
                    if active_match:
                        return

        # Delegate all other errors to the central bot error handler for clean UI embeds
        await self.bot.on_command_error(ctx, error)




    async def _resolve_round_cmd(self, ctx, match):
        score_c = match.current_round_score.get(match.challenger.id, 0)
        score_o = match.current_round_score.get(match.opponent.id, 0)
        
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
                winner_member = await self.get_safe_member(ctx.guild, winner_id)
                if winner_member:
                    await ctx.send(embed=build_match_winner_embed(winner_member, match.target_score))
                return
            else:
                await match_manager.next_turn(match)
                match.current_turn_player_id = winner_id
                
                winner_member = await self.get_safe_member(ctx.guild, winner_id)
                challenger_member = await self.get_safe_member(ctx.guild, match.challenger.id)
                opponent_member = await self.get_safe_member(ctx.guild, match.opponent.id)
                next_player_member = await self.get_safe_member(ctx.guild, match.current_turn_player_id)
                
                embed = build_round_winner_embed(
                    winner_member, 
                    challenger_member, 
                    opponent_member, 
                    match.challenger.score, 
                    match.opponent.score,
                    next_player_member
                )
                await ctx.send(
                    content=f"<@{match.current_turn_player_id}>, it's your turn!", 
                    embed=embed
                )
        else:
            await ctx.send(embed=build_error_embed("It's a tie! No points awarded this round."))
            match.current_turn_player_id = match.challenger.id 
            challenger_member = await self.get_safe_member(ctx.guild, match.current_turn_player_id)
            mention = challenger_member.mention if challenger_member else "Player"
            await ctx.send(content=f"{mention}, it's your turn to play again.")

    async def _execute_dice_turn_cmd(self, ctx, match):
        if not hasattr(match, "current_round_score"):
            match.current_round_score = {}

        forced_target = self.forced_standard_dice.pop(ctx.author.id, None)
        if forced_target is not None:
            min_d1 = max(1, forced_target - 6)
            max_d1 = min(6, forced_target - 1)
            die1 = random.randint(min_d1, max_d1)
            die2 = forced_target - die1
            result = forced_target
            display_result = f"**{die1}** and **{die2}** (Total: **{result}**)"
        elif getattr(self.bot, "forced_dice_result", None) is not None:
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

        await ctx.send(f"🎲 <@{ctx.author.id}> rolled {display_result}!")
        match.current_round_score[ctx.author.id] = result

        if len(match.current_round_score) == 2:
            await self._resolve_round_cmd(ctx, match)
        else:
            await match_manager.next_turn(match)
            next_player = await self.get_safe_member(ctx.guild, match.current_turn_player_id)
            mention = next_player.mention if next_player else "Player"
            await ctx.send(content=f"{mention}, it's your turn!")

    async def _execute_coinflip_turn_cmd(self, ctx, match, choice):
        if not hasattr(match, "current_round_score"):
            match.current_round_score = {}

        choices = ["Heads", "Tails"]
        display_result = random.choice(choices)
        
        if choice.title() == display_result:
            winner_id = ctx.author.id
            loser_id = match.challenger.id if ctx.author.id == match.opponent.id else match.opponent.id
        else:
            loser_id = ctx.author.id
            winner_id = match.challenger.id if ctx.author.id == match.opponent.id else match.opponent.id

        await ctx.send(f"🪙 <@{ctx.author.id}> chose **{choice.title()}**. The coin landed on **{display_result}**!")
        match.current_round_score[winner_id] = 2
        match.current_round_score[loser_id] = 1
        await self._resolve_round_cmd(ctx, match)

    async def _execute_colored_dice_turn_cmd(self, ctx, match, color_choice):
        valid_colors = ["red", "blue", "purple", "orange", "yellow", "green"]
        if color_choice not in valid_colors:
            await ctx.send(embed=build_error_embed("Invalid color! Choose: Red, Blue, Purple, Orange, Yellow, Green."), ephemeral=True)
            return

        default_emojis = {"red": "🔴", "blue": "🔵", "purple": "🟣", "orange": "🟠", "yellow": "🟡", "green": "🟢"}
        emojis = {}
        for c in valid_colors:
            custom_emoji = discord.utils.get(ctx.guild.emojis, name=c) if ctx.guild else None
            emojis[c] = str(custom_emoji) if custom_emoji else default_emojis[c]

        forced_color = self.forced_colored_dice.pop(ctx.author.id, None)
        if forced_color:
            other_colors = [c for c in valid_colors if c != forced_color]
            dice_3 = [random.choice(other_colors) for _ in range(3)]
            rolled_colors = [forced_color] + dice_3
            random.shuffle(rolled_colors)
        else:
            rolled_colors = [random.choice(valid_colors) for _ in range(4)]
        rolled_emojis = " ".join([emojis[c] for c in rolled_colors])
        rolled_names = ", ".join([c.title() for c in rolled_colors])

        match_count = rolled_colors.count(color_choice)
        scored = False
        
        player_obj = match.challenger if ctx.author.id == match.challenger.id else match.opponent

        if match_count == 1:
            scored = True
            game_over = await match_manager.update_score(match, ctx.author.id)
        else:
            game_over = False

        embed = discord.Embed(
            title=f"🎲 {ctx.author.display_name} rolled:",
            description=f"{rolled_emojis}\n==============\n🎯 {rolled_names}",
            color=discord.Color.green() if scored else discord.Color.red()
        )
        if scored:
            embed.set_footer(text=f"Exact match! +1 point ({player_obj.score}/{match.target_score})")
        else:
            embed.set_footer(text=f"No point! Found {match_count} times ({player_obj.score}/{match.target_score})")

        if game_over:
            await ctx.send(embed=embed)
            await match_manager.end_match(match)
            await ctx.send(embed=build_match_winner_embed(ctx.author, match.target_score))
        else:
            await match_manager.next_turn(match)
            next_player = await self.get_safe_member(ctx.guild, match.current_turn_player_id)
            mention = next_player.mention if next_player else "Player"
            await ctx.send(content=f"{mention}, it's your turn!", embed=embed)

    # ==================== BLACKJACK (1v1) SYSTEM ====================

    def _create_shuffled_deck(self):
        suits = ["♠️", "♥️", "♦️", "♣️"]
        ranks = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K", "A"]
        deck = [(r, s) for s in suits for r in ranks]
        random.shuffle(deck)
        return deck

    def _calculate_total(self, hand):
        total = 0
        aces = 0
        for r, _ in hand:
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
        return total

    async def _update_or_send_table(self, channel, match, embed, view=None, mention_player_id=None):
        table_msg = match.blackjack_data.get("table_msg")
        content = f"<@{mention_player_id}>, it's your turn!" if mention_player_id else None
        if table_msg:
            try:
                await table_msg.edit(content=content, embed=embed, view=view)
                return table_msg
            except (discord.NotFound, discord.HTTPException):
                pass
        new_msg = await channel.send(content=content, embed=embed, view=view)
        match.blackjack_data["table_msg"] = new_msg
        return new_msg

    async def _start_blackjack_round(self, interaction_or_ctx, match, note=None):
        deck = self._create_shuffled_deck()
        c_id = match.challenger.id
        o_id = match.opponent.id

        prev_round = match.blackjack_data.get("round_num", 0)
        round_num = prev_round + 1

        if round_num == 1:
            first_id = c_id
            second_id = o_id
        else:
            prev_first = match.blackjack_data.get("first_id", c_id)
            first_id = o_id if prev_first == c_id else c_id
            second_id = c_id if first_id == o_id else o_id

        c_hand = [deck.pop(), deck.pop()]
        o_hand = [deck.pop(), deck.pop()]

        match.blackjack_data = {
            "deck": deck,
            "hands": {c_id: c_hand, o_id: o_hand},
            "first_id": first_id,
            "second_id": second_id,
            "active_id": first_id,
            "first_stood": False,
            "round_num": round_num,
            "table_msg": None,
        }
        match.current_turn_player_id = first_id

        guild = interaction_or_ctx.guild
        channel = interaction_or_ctx.channel
        c_member = await self.get_safe_member(guild, c_id)
        o_member = await self.get_safe_member(guild, o_id)
        first_member = await self.get_safe_member(guild, first_id)
        second_member = await self.get_safe_member(guild, second_id)

        first_hand = match.blackjack_data["hands"][first_id]
        second_hand = match.blackjack_data["hands"][second_id]
        first_bj = (len(first_hand) == 2 and self._calculate_total(first_hand) == 21)
        second_bj = (len(second_hand) == 2 and self._calculate_total(second_hand) == 21)

        if first_bj and second_bj:
            await self._finish_blackjack_round(
                interaction_or_ctx, match, winner_id=None,
                note="✨ **Both players were dealt Natural Blackjack!** Push / Tie."
            )
            return
        elif first_bj:
            match.blackjack_data["first_stood"] = True
            match.blackjack_data["active_id"] = second_id
            match.current_turn_player_id = second_id

            view = BlackjackView(match, self.play_blackjack_turn)
            embed = build_blackjack_embed(
                c_member, o_member,
                c_hand, o_hand,
                match.challenger.score, match.opponent.score,
                match.target_score,
                current_turn_member=second_member,
                reveal_challenger=True,
                reveal_opponent=True,
                note=f"✨ **{first_member.display_name}** was dealt Natural Blackjack (21)! Stood automatically."
            )
            await self._update_or_send_table(channel, match, embed, view=view, mention_player_id=second_id)
            return

        reveal_c = (first_id == c_id)
        reveal_o = (first_id == o_id)

        view = BlackjackView(match, self.play_blackjack_turn)
        initial_note = note or f"🎮 **Round {round_num} Started!** First to {match.target_score} wins."
        embed = build_blackjack_embed(
            c_member, o_member,
            c_hand, o_hand,
            match.challenger.score, match.opponent.score,
            match.target_score,
            current_turn_member=first_member,
            reveal_challenger=reveal_c,
            reveal_opponent=reveal_o,
            note=initial_note
        )
        await self._update_or_send_table(channel, match, embed, view=view, mention_player_id=first_id)

    async def play_blackjack_turn(self, interaction: discord.Interaction, match, action: str):
        await interaction.response.defer()
        await self._handle_blackjack_action(interaction, match, action)

    async def _execute_blackjack_turn_cmd(self, ctx, match, action: str):
        await self._handle_blackjack_action(ctx, match, action)

    async def _handle_blackjack_action(self, context, match, action: str):
        guild = context.guild
        channel = context.channel
        author_id = context.user.id if isinstance(context, discord.Interaction) else context.author.id

        if author_id != match.current_turn_player_id:
            msg = "It's not your turn!"
            if isinstance(context, discord.Interaction):
                await context.followup.send(embed=build_error_embed(msg), ephemeral=True)
            else:
                await context.send(embed=build_error_embed(msg), ephemeral=True)
            return

        data = match.blackjack_data
        deck = data["deck"]
        hands = data["hands"]
        first_id = data["first_id"]
        second_id = data["second_id"]
        active_id = data["active_id"]
        c_id = match.challenger.id
        o_id = match.opponent.id

        c_member = await self.get_safe_member(guild, c_id)
        o_member = await self.get_safe_member(guild, o_id)
        active_member = c_member if active_id == c_id else o_member
        other_id = second_id if active_id == first_id else first_id
        other_member = await self.get_safe_member(guild, other_id)

        if action == "hit":
            if len(deck) < 5:
                deck.extend(self._create_shuffled_deck())
            card = deck.pop()
            hands[active_id].append(card)
            new_total = self._calculate_total(hands[active_id])

            if active_id == first_id:
                if new_total > 21:
                    note = f"💥 **{active_member.display_name}** drew `[{card[0]}{card[1]}]` and BUSTED with **{new_total}**!\n🏆 **{other_member.display_name}** wins this round!"
                    await self._finish_blackjack_round(context, match, winner_id=second_id, note=note)
                    return
                elif new_total == 21:
                    data["first_stood"] = True
                    data["active_id"] = second_id
                    match.current_turn_player_id = second_id

                    note = f"✨ **{active_member.display_name}** drew `[{card[0]}{card[1]}]` and hit **21**! Auto-stood.\n👉 Now it's **{other_member.mention}**'s turn!"
                    view = BlackjackView(match, self.play_blackjack_turn)
                    embed = build_blackjack_embed(
                        c_member, o_member,
                        hands[c_id], hands[o_id],
                        match.challenger.score, match.opponent.score,
                        match.target_score,
                        current_turn_member=other_member,
                        reveal_challenger=True,
                        reveal_opponent=True,
                        note=note
                    )
                    await self._update_or_send_table(channel, match, embed, view=view, mention_player_id=second_id)
                    return
                else:
                    note = f"🃏 **{active_member.display_name}** drew `[{card[0]}{card[1]}]` (Total: **{new_total}**)."
                    view = BlackjackView(match, self.play_blackjack_turn)
                    embed = build_blackjack_embed(
                        c_member, o_member,
                        hands[c_id], hands[o_id],
                        match.challenger.score, match.opponent.score,
                        match.target_score,
                        current_turn_member=active_member,
                        reveal_challenger=(first_id == c_id),
                        reveal_opponent=(first_id == o_id),
                        note=note
                    )
                    await self._update_or_send_table(channel, match, embed, view=view, mention_player_id=first_id)
                    return
            else:
                if new_total > 21:
                    note = f"💥 **{active_member.display_name}** drew `[{card[0]}{card[1]}]` and BUSTED with **{new_total}**!\n🏆 **{other_member.display_name}** wins this round!"
                    await self._finish_blackjack_round(context, match, winner_id=first_id, note=note)
                    return
                elif new_total == 21:
                    prefix = f"✨ **{active_member.display_name}** drew `[{card[0]}{card[1]}]` and hit **21**!"
                    await self._compare_and_finish_blackjack_round(context, match, note_prefix=prefix)
                    return
                else:
                    note = f"🃏 **{active_member.display_name}** drew `[{card[0]}{card[1]}]` (Total: **{new_total}**)."
                    view = BlackjackView(match, self.play_blackjack_turn)
                    embed = build_blackjack_embed(
                        c_member, o_member,
                        hands[c_id], hands[o_id],
                        match.challenger.score, match.opponent.score,
                        match.target_score,
                        current_turn_member=active_member,
                        reveal_challenger=True,
                        reveal_opponent=True,
                        note=note
                    )
                    await self._update_or_send_table(channel, match, embed, view=view, mention_player_id=second_id)
                    return

        elif action == "stand":
            if active_id == first_id:
                data["first_stood"] = True
                data["active_id"] = second_id
                match.current_turn_player_id = second_id

                first_total = self._calculate_total(hands[first_id])
                note = f"🛑 **{active_member.display_name}** stood at **{first_total}**.\n👉 Now it's **{other_member.mention}**'s turn!"
                view = BlackjackView(match, self.play_blackjack_turn)
                embed = build_blackjack_embed(
                    c_member, o_member,
                    hands[c_id], hands[o_id],
                    match.challenger.score, match.opponent.score,
                    match.target_score,
                    current_turn_member=other_member,
                    reveal_challenger=True,
                    reveal_opponent=True,
                    note=note
                )
                await self._update_or_send_table(channel, match, embed, view=view, mention_player_id=second_id)
                return
            else:
                second_total = self._calculate_total(hands[second_id])
                prefix = f"🛑 **{active_member.display_name}** stood at **{second_total}**."
                await self._compare_and_finish_blackjack_round(context, match, note_prefix=prefix)
                return

    async def _compare_and_finish_blackjack_round(self, context, match, note_prefix: str):
        data = match.blackjack_data
        first_id = data["first_id"]
        second_id = data["second_id"]
        h1 = data["hands"][first_id]
        h2 = data["hands"][second_id]

        t1 = self._calculate_total(h1)
        t2 = self._calculate_total(h2)

        bj1 = (len(h1) == 2 and t1 == 21)
        bj2 = (len(h2) == 2 and t2 == 21)

        first_member = await self.get_safe_member(context.guild, first_id)
        second_member = await self.get_safe_member(context.guild, second_id)

        if bj1 and not bj2:
            winner_id = first_id
            note = f"{note_prefix}\n✨ **{first_member.display_name}** wins with Natural Blackjack! (21 vs {t2})"
        elif bj2 and not bj1:
            winner_id = second_id
            note = f"{note_prefix}\n✨ **{second_member.display_name}** wins with Natural Blackjack! (21 vs {t1})"
        elif t1 > t2:
            winner_id = first_id
            note = f"{note_prefix}\n🏆 **{first_member.display_name}** wins the round (**{t1}** vs **{t2}**)!"
        elif t2 > t1:
            winner_id = second_id
            note = f"{note_prefix}\n🏆 **{second_member.display_name}** wins the round (**{t2}** vs **{t1}**)!"
        else:
            winner_id = None
            note = f"{note_prefix}\n🤝 **It's a Push / Tie!** Both finished with **{t1}**. No points awarded."

        await self._finish_blackjack_round(context, match, winner_id=winner_id, note=note)

    async def _finish_blackjack_round(self, context, match, winner_id, note: str):
        guild = context.guild
        channel = context.channel
        data = match.blackjack_data

        c_id = match.challenger.id
        o_id = match.opponent.id
        c_hand = data["hands"][c_id]
        o_hand = data["hands"][o_id]

        c_member = await self.get_safe_member(guild, c_id)
        o_member = await self.get_safe_member(guild, o_id)

        game_over = False
        if winner_id:
            game_over = await match_manager.update_score(match, winner_id)

        color = COLOR_SUCCESS if winner_id else COLOR_WARNING
        table_embed = build_blackjack_embed(
            c_member, o_member,
            c_hand, o_hand,
            match.challenger.score, match.opponent.score,
            match.target_score,
            current_turn_member=None,
            reveal_challenger=True,
            reveal_opponent=True,
            note=note,
            color=color
        )

        await self._update_or_send_table(channel, match, table_embed, view=None)

        if winner_id:
            winner_member = await self.get_safe_member(guild, winner_id)
            if game_over:
                await match_manager.end_match(match)
                await channel.send(embed=build_match_winner_embed(winner_member, match.target_score))
                return
            else:
                c_score = match.challenger.score
                o_score = match.opponent.score
                embed = discord.Embed(
                    title="🏆 Round Over!",
                    description=f"{winner_member.mention} wins this round!\n\n"
                                f"**Current Match Score:**\n"
                                f"{c_member.mention}: **{c_score}**\n"
                                f"{o_member.mention}: **{o_score}**\n\n"
                                f"*(First to {match.target_score} wins)*",
                    color=COLOR_WARNING
                )
                await channel.send(embed=embed)
        else:
            embed = discord.Embed(
                title="🤝 Round Over (Push / Tie)!",
                description=f"Neither player scored this round. Score remains:\n"
                            f"{c_member.mention}: **{match.challenger.score}**\n"
                            f"{o_member.mention}: **{match.opponent.score}**",
                color=COLOR_WARNING
            )
            await channel.send(embed=embed)

        await asyncio.sleep(2.5)
        if match.state.value == "active":
            await self._start_blackjack_round(context, match)

async def setup(bot):
    await bot.add_cog(GamblingCog(bot))

