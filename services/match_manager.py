import asyncio
from typing import Dict, Optional, Tuple
from models.match import Match, Player, MatchState, GameType

class MatchManager:
    def __init__(self):
        self.active_matches: Dict[int, Match] = {}
        self.pending_challenges: Dict[int, Match] = {}
        # Concurrency lock to prevent race conditions in high traffic
        self.lock = asyncio.Lock()

    async def get_active_match(self, user_id: int) -> Optional[Match]:
        async with self.lock:
            return self.active_matches.get(user_id)

    async def get_pending_challenge_for_user(self, user_id: int) -> Optional[Match]:
        async with self.lock:
            for match in self.pending_challenges.values():
                if match.opponent.id == user_id:
                    return match
            return None

    async def create_challenge(self, challenger_id: int, opponent_id: int, game_type: GameType, channel_id: int) -> Tuple[bool, str]:
        async with self.lock:
            if challenger_id == opponent_id:
                return False, "You cannot challenge yourself!"
            if challenger_id in self.active_matches:
                return False, "You already have an active match."
            if opponent_id in self.active_matches:
                return False, "Your opponent is currently in an active match."
            if challenger_id in self.pending_challenges:
                return False, "You already have a pending challenge. Cancel it first."
                
            challenger = Player(id=challenger_id)
            opponent = Player(id=opponent_id)
            match = Match(challenger=challenger, opponent=opponent, game_type=game_type, channel_id=channel_id)
            
            self.pending_challenges[challenger_id] = match
            return True, "Challenge created."

    async def accept_challenge(self, opponent_id: int, channel_id: int) -> Tuple[bool, str, Optional[Match]]:
        async with self.lock:
            match = None
            for m in self.pending_challenges.values():
                if m.opponent.id == opponent_id:
                    match = m
                    break
                    
            if not match:
                return False, "You have no pending challenges.", None
            if match.channel_id != channel_id:
                return False, "You must accept the challenge in the same channel it was made.", None
                
            del self.pending_challenges[match.challenger.id]
            
            match.state = MatchState.ACTIVE
            match.current_turn_player_id = match.challenger.id
            self.active_matches[match.challenger.id] = match
            self.active_matches[match.opponent.id] = match
            
            return True, "Challenge accepted! Match starting.", match

    async def cancel_challenge_or_match(self, user_id: int) -> Tuple[bool, str, Optional[Match]]:
        async with self.lock:
            if user_id in self.pending_challenges:
                match = self.pending_challenges.pop(user_id)
                return True, "Your pending challenge was canceled.", match
                
            if user_id in self.active_matches:
                match = self.active_matches[user_id]
                del self.active_matches[match.challenger.id]
                del self.active_matches[match.opponent.id]
                return True, "Your active match was canceled.", match
                
            for challenger_id, match in list(self.pending_challenges.items()):
                if match.opponent.id == user_id:
                    del self.pending_challenges[challenger_id]
                    return True, "You declined the pending challenge.", match

            return False, "You don't have any active matches or pending challenges to cancel.", None

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
            if match.challenger.id in self.active_matches:
                del self.active_matches[match.challenger.id]
            if match.opponent.id in self.active_matches:
                del self.active_matches[match.opponent.id]

match_manager = MatchManager()
