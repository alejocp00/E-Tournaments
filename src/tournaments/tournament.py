from src.player.player import Player
from src.tournaments.tournament_engine import TournamentEngine


class Tournament:
    def __init__(self, id: int, tournament_engine: TournamentEngine):
        self._players = []
        self._id = id
        self._tournament_engine = tournament_engine

    @property
    def id(self):
        return self._id

    @property
    def players(self):
        return self._players

    @property
    def tournament_type(self):
        return self._tournament_engine.tournament_type

    def add_player(self, player: Player):
        self._players.append(player)

    def remove_player(self, player: Player):
        self._players.remove(player)

    def __iter__(self):
        return self

    def __next__(self):
        return self._tournament_engine.next_match(self)
