from src.game.game import Game
from src.player.player import Player
from src.tournaments.tournament_engine import TournamentEngine


class Tournament:
    def __init__(self, id: int, tournament_engine: TournamentEngine, game: Game):
        self._players = []
        self._id = id
        self._tournament_engine = tournament_engine
        self._matches_to_perform = []
        self._matches_results = []
        self._log = []
        self._game = game

    @property
    def id(self):
        return self._id

    @property
    def players(self) -> list[Player]:
        return self._players

    @property
    def tournament_type(self):
        return self._tournament_engine.tournament_type

    @property
    def tournament_game(self) -> Game:
        return self._game.clone()

    def add_player(self, player: Player):
        self._players.append(player)

    def remove_player(self, player: Player):
        self._players.remove(player)

    def get_match_to_perform(self) -> Game | None:
        if len(self._matches_to_perform) > 0:
            return self._matches_to_perform.pop(0)
        return None

    def get_matches_results(self):
        result = [match for match in self._matches_results]
        self._matches_results = []
        return result

    def put_match_result(self, match_result: Game):
        self._matches_results.append(match_result)
        self._log.append(match_result)

    def __iter__(self):
        return self

    def __next__(self)->Game:
        return self._tournament_engine.next_match(self)

    def is_valid_configuration(self):
        return self._tournament_engine.is_valid_configuration(self._players.count())
