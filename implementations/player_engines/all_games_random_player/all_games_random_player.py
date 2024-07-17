import random
from src.game.game_state import GameState
from src.player.player_engine import PlayerEngine


class AllGamesRandomPlayer(PlayerEngine):

    def __init__(self):
        super().__init__("All Games Random Player")

    def perform_a_move(self, game_state: GameState) -> object:
        return random(game_state.get_all_moves())
