from abc import abstractmethod, ABC

from src.tournaments.tournament import Tournament


class TournamentEngine(ABC):
    def __init__(self):
        self._tournament_type = "NOT SET"

    @property
    def tournament_type(self):
        return self._tournament_type

    @abstractmethod
    def next_match(self, tournament: Tournament):
        raise NotImplementedError
