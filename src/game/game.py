from abc import abstractmethod, ABC
from game.action import Action
from src.player.player import Player
from src.game.game_state import GameState


class Game(ABC):
    def __init__(self, game_name: str):
        self._game_name = game_name
        self._players = []
        self._id = -1
        self._game_state = None
        self._log = []

    @property
    def game_name(self):
        return self.game_name

    @property
    def players(self):
        return [player for player in self._players]

    @property
    def logs(self) -> list[Action]:
        return [log for log in self._log]

    @property
    def game_state(self) -> GameState:
        return self._game_state

    def clone(self):
        return self.__class__(self._game_name)

    def set_game_id(self, id: int):
        self._id = id

    def add_player(self, player: Player):
        self._players.append(player)

    def remove_player(self, player: Player):
        self._players.remove(player)

    def add_player(self, player: list[Player]):
        self._players.extend(player)

    @abstractmethod
    def init_game_state(self):
        raise NotImplementedError

    @abstractmethod
    def get_winner(self) -> Player:
        raise NotImplementedError

    @abstractmethod
    def perform_a_move(self, action: Action) -> Action:
        raise NotImplementedError

    def __iter__(self):
        return self

    @abstractmethod
    def __next__(self):
        """
        Main game loop made it as an iterable
        """
        raise NotImplementedError

    @abstractmethod
    def get_all_data_as_string():
        raise NotImplementedError
