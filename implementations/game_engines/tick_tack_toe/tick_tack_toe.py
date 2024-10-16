from src.game.game import Game
from implementations.game_engines.tick_tack_toe.src.utils import Tokens
import implementations.game_engines.tick_tack_toe.src.ttt_game_state as TickTackToeGameState


class TickTackToeGame(Game):
    def __init__(self):
        super().__init__("TickTackToe")

    def init_game_state(self):
        self._game_state = TickTackToeGameState.TTTGameState(self.players, self.game_explorer)

    def game_state(self) -> TickTackToeGameState.GameState:
        return self._game_state

    def get_winner(self) -> TickTackToeGameState.Player | None:
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
        if self._game_state.state == TickTackToeGame.IDLE:
            self._game_state.state = TickTackToeGame.IN_PROGRESS
        if self._game_state.state == TickTackToeGame.FINISHED:
            raise StopIteration

        current_player = self._game_state.get_next_player()

        action = current_player.perform_a_move(self._game_state)

        self.perform_a_move(action)

        self._log.append(action)

        self._game_state.set_next_player()

        return action

    def perform_a_move(self, action: TickTackToeGameState.Action):
        token = action.action["token"]
        x = action.action["i"]
        y = action.action["j"]

        self._game_state.board[x][y] = token

    def get_all_data_as_string(self):
        text = ""

        for action in self.logs:
            text += str(action) + "\n"

        return text
