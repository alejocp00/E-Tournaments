from abc import abstractmethod, ABC, abstractstaticmethod
from enum import Enum
from src.game.action import Action
from src.player.player import Player
from src.game.game_state import GameState

class GameEndCondition(Enum):
    Unfinished = 0
    Victory = 1
    Draw = 2

class Game(ABC):
    def __init__(self, game_name: str):
        self._game_name = game_name
        self._players = []
        self._id = -1
        self._game_state = None
        self._log = []

    @property
    def game_name(self):
        return self._game_name

    @property
    def players(self):
        return [player for player in self._players]

    @property
    def logs(self) -> list[Action]:
        return [log for log in self._log]

    @property
    def game_state(self) -> GameState:
        return self._game_state

    @property
    def game_id(self) -> int:
        return self._id

    def clone(self):
        return self.__class__()

    def set_game_id(self, id: int):
        self._id = id

    def add_player(self, player: Player):
        self._players.append(player)

    def remove_player(self, player: Player):
        self._players.remove(player)

    def add_players(self, player: list[Player]):
        self._players.extend(player)

    @abstractmethod
    def init_game_state(self):
        raise NotImplementedError

    @abstractmethod
    def get_winner(self) -> tuple[GameEndCondition,Player|None]:
        raise NotImplementedError

    @abstractmethod
    def perform_a_move(self, action: Action) -> Action:
        raise NotImplementedError

    def __iter__(self):
        return self

    @abstractmethod
    def __next__(self)->Action:
        """
        Main game loop made it as an iterable
        """
        raise NotImplementedError

    @abstractmethod
    def solve_draw(self)->None:
        """Get a winner in case of draw

        Raises:
            NotImplementedError: Not implemented in the child class
        """
        raise NotImplementedError

    @abstractmethod
    def get_all_data_as_string():
        raise NotImplementedError

    def __str__(self) -> str:
        return self._game_name
    
