from src.player.player_engine import PlayerEngine
from src.game.game_state import GameState
from game.action import Action


class Player:
    def __init__(self, name: str, player_engine: PlayerEngine, id: int):
        self._name = name
        self._victory_for_tournament = {}
        self._defeat_for_tournament = {}
        self._draw_for_tournament = {}
        self._points_for_tournament = {}
        self._rank_for_tournament = {}
        self._player_engine = player_engine
        self._id = id

    @property
    def name(self):
        return self._name

    @property
    def victory_for_tournament(self):
        return self._victory_for_tournament

    @property
    def defeat_for_tournament(self):
        return self._defeat_for_tournament

    @property
    def draw_for_tournament(self):
        return self._draw_for_tournament

    @property
    def id(self):
        return self._id

    @property
    def points_for_tournament(self):
        return self._points_for_tournament

    @property
    def rank_for_tournament(self):
        return self._rank_for_tournament

    @property
    def total_victories(self):
        return sum(self._victory_for_tournament.values())

    @property
    def total_defeats(self):
        return sum(self._defeat_for_tournament.values())

    @property
    def total_draws(self):
        return sum(self._draw_for_tournament.values())

    @property
    def total_points(self):
        return sum(self._points_for_tournament.values())

    @property
    def best_rank(self):
        return max(self._rank_for_tournament.values())

    def perform_a_move(self, game_state: GameState) -> Action:
        move = self._player_engine.get_next_action(game_state)

        return move

    def add_victory(self, tournament_id: int):
        self._victory_for_tournament[tournament_id] = (
            self._victory_for_tournament.get(tournament_id, 0) + 1
        )

    def add_defeat(self, tournament_id: int):
        self._defeat_for_tournament[tournament_id] = (
            self._defeat_for_tournament.get(tournament_id, 0) + 1
        )

    def add_draw(self, tournament_id: int):
        self._draw_for_tournament[tournament_id] = (
            self._draw_for_tournament.get(tournament_id, 0) + 1
        )

    def add_points(self, tournament_id: int, points: int):
        self._points_for_tournament[tournament_id] = (
            self._points_for_tournament.get(tournament_id, 0) + points
        )

    def add_rank(self, tournament_id: int, rank: int):
        self._rank_for_tournament[tournament_id] = rank

    def change_name(self, new_name: str):
        self._name = new_name
