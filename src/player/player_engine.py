from abc import ABC, abstractmethod
from src.game.game_state import GameState
from src.game.action import Action


class PlayerEngine(ABC):
    def __init__(self, engine_name: str):
        self._engine_name = engine_name

    @property
    def name(self) -> str:
        return self._engine_name

    @abstractmethod
    def get_next_action(self, game_state: GameState) -> Action:
        pass
