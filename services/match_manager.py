import asyncio
from typing import Dict, Optional, Tuple
from models.match import Match, Player, MatchState, GameType

class MatchManager:
    def __init__(self):
        # Keyed by (guild_id, user_id)
        self.active_matches: Dict[Tuple[int, int], Match] = {}
        self.pending_challenges: Dict[Tuple[int, int], Match] = {}
        # Concurrency lock to prevent race conditions in high traffic
        self.lock = asyncio.Lock()

    async def get_active_match(self, guild_id: int, user_id: int) -> Optional[Match]:
        async with self.lock:
            return self.active_matches.get((guild_id, user_id))

    async def get_pending_challenge_for_user(self, guild_id: int, user_id: int) -> Optional[Match]:
        async with self.lock:
            for match in self.pending_challenges.values():
                if match.guild_id == guild_id and match.opponent.id == user_id:
                    return match
            return None

    async def create_challenge(self, guild_id: int, challenger_id: int, opponent_id: int, game_type: GameType, channel_id: int) -> Tuple[bool, str]:
        async with self.lock:
            if challenger_id == opponent_id:
                return False, "You cannot challenge yourself!"
            if (guild_id, challenger_id) in self.active_matches:
                return False, "You already have an active match in this server."
            if (guild_id, opponent_id) in self.active_matches:
                return False, "Your opponent is currently in an active match in this server."
            if (guild_id, challenger_id) in self.pending_challenges:
                return False, "You already have a pending challenge in this server. Cancel it first."
                
            challenger = Player(id=challenger_id)
            opponent = Player(id=opponent_id)
            match = Match(challenger=challenger, opponent=opponent, game_type=game_type, channel_id=channel_id, guild_id=guild_id)
            
            self.pending_challenges[(guild_id, challenger_id)] = match
            return True, "Challenge created."

    async def accept_challenge(self, guild_id: int, opponent_id: int, channel_id: int) -> Tuple[bool, str, Optional[Match]]:
        async with self.lock:
            match = None
            for m in self.pending_challenges.values():
                if m.guild_id == guild_id and m.opponent.id == opponent_id:
                    match = m
                    break
                    
            if not match:
                return False, "You have no pending challenges in this server.", None
            if match.channel_id != channel_id:
                return False, "You must accept the challenge in the same channel it was made.", None
                
            del self.pending_challenges[(guild_id, match.challenger.id)]
            
            match.state = MatchState.ACTIVE
            match.current_turn_player_id = match.challenger.id
            self.active_matches[(guild_id, match.challenger.id)] = match
            self.active_matches[(guild_id, match.opponent.id)] = match
            
            return True, "Challenge accepted! Match starting.", match

    async def cancel_challenge_or_match(self, guild_id: int, user_id: int) -> Tuple[bool, str, Optional[Match]]:
        async with self.lock:
            key = (guild_id, user_id)
            if key in self.pending_challenges:
                match = self.pending_challenges.pop(key)
                return True, "Your pending challenge was canceled.", match
                
            if key in self.active_matches:
                match = self.active_matches[key]
                del self.active_matches[(guild_id, match.challenger.id)]
                del self.active_matches[(guild_id, match.opponent.id)]
                return True, "Your active match was canceled.", match
                
            for k, match in list(self.pending_challenges.items()):
                if match.guild_id == guild_id and match.opponent.id == user_id:
                    del self.pending_challenges[k]
                    return True, "You declined the pending challenge.", match

            return False, "You don't have any active matches or pending challenges to cancel in this server.", None

    async def cancel_matches_in_channel(self, channel_id: int):
        async with self.lock:
            to_remove_pending = [k for k, m in self.pending_challenges.items() if m.channel_id == channel_id]
            for k in to_remove_pending:
                del self.pending_challenges[k]
                
            to_remove_active = [k for k, m in self.active_matches.items() if m.channel_id == channel_id]
            for k in to_remove_active:
                del self.active_matches[k]

    async def update_score(self, match: Match, winner_id: int) -> bool:
        async with self.lock:
            if match.challenger.id == winner_id:
                match.challenger.score += 1
                if match.challenger.score >= match.target_score:
                    return True
            elif match.opponent.id == winner_id:
                match.opponent.score += 1
                if match.opponent.score >= match.target_score:
                    return True
            return False

    async def next_turn(self, match: Match):
        async with self.lock:
            if match.current_turn_player_id == match.challenger.id:
                match.current_turn_player_id = match.opponent.id
            else:
                match.current_turn_player_id = match.challenger.id

    async def end_match(self, match: Match):
        async with self.lock:
            match.state = MatchState.FINISHED
            if (match.guild_id, match.challenger.id) in self.active_matches:
                del self.active_matches[(match.guild_id, match.challenger.id)]
            if (match.guild_id, match.opponent.id) in self.active_matches:
                del self.active_matches[(match.guild_id, match.opponent.id)]

match_manager = MatchManager()
