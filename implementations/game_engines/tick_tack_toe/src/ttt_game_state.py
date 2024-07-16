from src.game.action import Action
from src.player.player import Player
from src.game.game_state import GameState
from implementations.game_engines.tick_tack_toe.src.utils import Tokens


class TTTGameState(GameState):
    def __init__(self, players: list[Player], current_player_index: int = 0):
        super().__init__(players, current_player_index)
        self._board = [[Tokens.EMPTY_TOKEN for _ in range(3)] for _ in range(3)]

    @property
    def board(self):
        return self._board

    def get_all_moves(self) -> list[Action]:
        player_token = (
            Tokens.PLAYER_1_TOKEN
            if self.current_player_index == 0
            else Tokens.PLAYER_2_TOKEN
        )

        moves = []

        for i in range(3):
            for j in range(3):
                if self.board[i][j] == Tokens.EMPTY_TOKEN:
                    moves.append(
                        Action(
                            self.current_player.id,
                            {"i": i, "j": j, "token": player_token},
                        )
                    )

        return moves

    def set_next_player(self):
        self.current_player_index = (self.current_player_index + 1) % 2
        self._player_turn_queue.append(self.current_player_index)
