from abc import abstractmethod, ABC

# from src.tournaments.tournament import Tournament
from src.game.game import Game
from src.player.player import Player


class TournamentEngine(ABC):

    def __init__(self, tournament_type: str):
        self._tournament_type = tournament_type

    @property
    def tournament_type(self):
        return self._tournament_type

    @abstractmethod
    def next_match(self, tournament):
        raise NotImplementedError

    @abstractmethod
    def is_valid_configuration(self, players: int):
        raise NotImplementedError

    def __str__(self) -> str:
        return self._tournament_type