from abc import abstractmethod
from src.game.action import Action
# from src.player.player import Player


class GameState:

    IDLE = 0
    IN_PROGRESS = 1
    FINISHED = 2

    @property
    def state(self) -> int:
        return self._state

    @state.setter
    def state(self, state):
        self._state = state

    def __init__(
        self,
        players,
        current_player_index: int = 0,
    ):
        self._players = players
        self._current_player_index = current_player_index
        self._player_turn_queue = [current_player_index]
        self._state = GameState.IDLE

    @property
    def current_player_index(self):
        return self._current_player_index

    @current_player_index.setter
    def current_player_index(self, current_player_index):
        self._current_player_index = current_player_index

    @property
    def current_player(self):
        return self._players[self.current_player_index]

    @property
    def players(self) -> list:
        return self._players

    @property
    def player_turn_queue(self):
        return self._player_turn_queue

    def get_next_player(self):
        self._current_player_index = self._player_turn_queue.pop(0)
        return self._players[self._current_player_index]

    @abstractmethod
    def set_next_player(self):
        raise NotImplementedError

    @abstractmethod
    def get_all_moves(self) -> list[Action]:
        raise NotImplementedError
