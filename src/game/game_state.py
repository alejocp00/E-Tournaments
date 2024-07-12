from src.player.player import Player
from src.game.move import Action


class GameState:

    def __init__(
        self,
        players: list[Player],
        game_explorer: callable[list[Action]],
        current_player_index: int = 0,
    ):
        self._players = players
        self._current_player_index = current_player_index
        self._player_turn_queue = [current_player_index]
        self._game_explorer = game_explorer

    @property
    def current_player_index(self):
        return self._current_player_index

    @property
    def current_player(self):
        return self._players[self.current_player_index]

    @property
    def players(self):
        return self._players

    @property
    def player_turn_queue(self):
        return self._player_turn_queue

    def get_all_moves(self) -> list[Action]:
        return self._game_explorer()
