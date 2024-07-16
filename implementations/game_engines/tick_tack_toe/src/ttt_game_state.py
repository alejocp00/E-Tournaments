from src.game.action import Action
from src.player.player import Player
from src.game.game_state import GameState


class TTTGameState(GameState):
    def __init__(self, players: list[Player], current_player_index: int = 0):
        super().__init__(players, current_player_index)
        self._board = [[" " for _ in range(3)] for _ in range(3)]

    @property
    def board(self):
        return self._board

    def get_all_moves(self) -> list[Action]:
        player_token = "X" if self.current_player_index == 0 else "O"

        moves = []

        for i in range(3):
            for j in range(3):
                if self.board[i][j] == " ":
                    moves.append(Action(self.current_player.id, f"{i}{j}"))

        return moves
