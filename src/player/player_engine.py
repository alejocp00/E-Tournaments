from abc import ABC, abstractmethod
from src.game.game_state import GameState
from game.action import Action


class PlayerEngine(ABC):
    @abstractmethod
    def get_next_action(self, game_state: GameState) -> Action:
        pass
