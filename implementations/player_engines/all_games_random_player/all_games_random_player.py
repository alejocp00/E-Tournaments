import random
from src.game.action import Action
from src.game.game_state import GameState
from src.player.player_engine import PlayerEngine


class AllGamesRandomPlayer(PlayerEngine):

    def __init__(self):
        super().__init__("All Games Random Player")

    def get_next_action(self, game_state: GameState) -> Action:
        return random.choice(game_state.get_all_moves())
