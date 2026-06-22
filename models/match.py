from enum import Enum
from typing import Optional
from dataclasses import dataclass

class GameType(Enum):
    DICE = "dice"
    COINFLIP = "coinflip"

@dataclass
class Player:
    id: int
    score: int = 0

class MatchState(Enum):
    PENDING = "pending"
    ACTIVE = "active"
    FINISHED = "finished"

@dataclass
class Match:
    challenger: Player
    opponent: Player
    game_type: GameType
    channel_id: int
    guild_id: int
    target_score: int = 5
    state: MatchState = MatchState.PENDING
    current_turn_player_id: Optional[int] = None
