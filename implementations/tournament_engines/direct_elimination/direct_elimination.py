from src.tournaments.tournament_engine import TournamentEngine
from src.tournaments.tournament import Tournament


class DirectElimination(TournamentEngine):

    PLAYER_IDLE = 0
    PLAYER_PAIRED = 1
    PLAYER_MATCHING = 2
    PLAYER_ELIMINATED = 3

    def __init__(self):
        super().__init__("Direct Elimination")
        self._players = []
        self._players_state = []
        self._idle_count = -1
        self._eliminated_count = 0
        self._engine_initialized = False
        self._winner = None
        self._is_ended = False
        

    def init_state(self, tournament: Tournament):
        self._players = tournament.players
        self._players_state = [DirectElimination.PLAYER_IDLE] * len(self._players)
        self._idle_count = int(self._idle_count)
        self._idle_count = len(self._players)
        self._engine_initialized = True

    def next_matches(self, tournament: Tournament):

        if not self._engine_initialized:
            self.init_state(tournament)

        self.__process_results(tournament)

        if self._eliminated_count == len(self._players) - 1:
            self._is_ended = True
            raise StopIteration

        # Todo: Poner para que se vayan creando las partidas de uno en uno y no en una lista
        pairs = self.__create_pairs()
        self._matches_to_perform = []
        for pair in pairs:
            game = tournament.tournament_game
            for i in pair:
                self._players_state[i] = DirectElimination.PLAYER_MATCHING
                game.add_player(self._players[i])
            self._matches_to_perform.append(game)

        return self._matches_to_perform

    def is_valid_configuration(self, players: int):
        return players > 2

    def __create_pairs(self):
        pairs = []
        remaining_idle = self._idle_count / 2
        total_to_match = self._idle_count

        for i in range(len(self._players)):
            if remaining_idle and i == total_to_match - 1:
                break
            
            if not self._players_state[i] == 0:
                continue
            else:
                self._players_state[i] = DirectElimination.PLAYER_PAIRED
                for j in range(len(self._players)):
                    if i < j and self._players_state[j] == 0:
                        self._players_state[j] = DirectElimination.PLAYER_PAIRED
                        pairs.append([i, j])
                        break
        
        # Fix: idle count no se está reflejando correctamente y se está convirtiendo en bool.
        self._idle_count = int(remaining_idle)
        return pairs

    def __process_results(self, tournament: Tournament):
        results = tournament.get_matches_results()

        for rounds_results in results:
            for result in rounds_results:
                winner = result.get_winner()
                players = result.players
                for player in players:
                    index = self._players.index(player)
                    if winner is not None:
                        if winner == player:
                            self._players_state[index] = DirectElimination.PLAYER_IDLE
                        else:
                            self._players_state[index] = DirectElimination.PLAYER_ELIMINATED
                            self._eliminated_count += 1
      #              else:
      #                  self._players_state[index] = DirectElimination.PLAYER_PAIRED
                # self._matches_to_perform.append(players)

    def get_winner(self, tournament):
        if self._winner is not None:
            return self._winner
        if not self._is_ended:
            return None
        
        for index,state in enumerate(self._players_state):
            if state == DirectElimination.PLAYER_IDLE:
                self._winner = self._players[index]
                break

        return self._winner