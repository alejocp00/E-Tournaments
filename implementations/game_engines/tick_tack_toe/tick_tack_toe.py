from src.game.action import Action
from src.game.game_state import GameState
from src.player.player import Player
from src.game.game import Game
from implementations.game_engines.tick_tack_toe.src.utils import Tokens
from implementations.game_engines.tick_tack_toe.src.ttt_game_state import (
    TickTackToeGameState,
)


class TickTackToeGame(Game):
    def __init__(self):
        super().__init__("TickTackToe")

    def init_game_state(self):
        self._game_state = TickTackToeGameState(self.players, self.game_explorer)

    def game_state(self) -> GameState:
        return self._game_state

    def get_winner(self) -> Player | None:
        board = self.game_state.board

        for i in range(3):
            if board[i][0] == board[i][1] == board[i][2] and board[i][0] != " ":
                return self.players[0 if board[i][0] == Tokens.PLAYER_1_TOKEN else 1]
            if board[0][i] == board[1][i] == board[2][i] and board[0][i] != " ":
                return self.players[0 if board[0][i] == Tokens.PLAYER_1_TOKEN else 1]

        if board[0][0] == board[1][1] == board[2][2] and board[0][0] != " ":
            return self.players[0 if board[0][0] == Tokens.PLAYER_1_TOKEN else 1]
        if board[2][0] == board[1][1] == board[0][2] and board[2][0] != " ":
            return self.players[0 if board[2][0] == Tokens.PLAYER_1_TOKEN else 1]

        return None

    def __next__(self):
        if self._game_state.state == GameState.IDLE:
            self._game_state.state = GameState.IN_PROGRESS
        if self._game_state.state == GameState.FINISHED:
            raise StopIteration

        current_player = self._game_state.get_next_player()

        action = current_player.perform_a_move(self._game_state)

        self.perform_a_move(action)

        self._log.append(action)

        self._game_state.set_next_player()

        return action

    def perform_a_move(self, action: Action):
        token = action.action["token"]
        x = action.action["i"]
        y = action.action["j"]

        self._game_state.board[x][y] = token

    def get_all_data_as_string(self):
        text = ""

        for action in self.logs:
            text += str(action) + "\n"

        return text
