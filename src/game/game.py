from abc import abstractmethod, ABC
from game.action import Action
from src.player.player import Player
from src.game.game_state import GameState


class Game(ABC):
    def __init__(self, game_name: str, id: int):
        self._game_name = game_name
        self._players = []
        self._id = id

    @property
    def game_name(self):
        return self.game_name

    @property
    def players(self):
        return [player for player in self._players]

    @abstractmethod
    def game_explorer(self) -> list[Action]:
        raise NotImplementedError

    def add_player(self, player: Player):
        self._players.append(player)

    def remove_player(self, player: Player):
        self._players.remove(player)

    def add_player(self, player: list[Player]):
        self._players.extend(player)

    @abstractmethod
    def game_state(self) -> GameState:
        raise NotImplementedError

    @abstractmethod
    def init_game_state(self) -> GameState:
        raise NotImplementedError

    @abstractmethod
    def get_winner(self) -> Player:
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
