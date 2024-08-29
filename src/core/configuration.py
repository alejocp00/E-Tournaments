from src.player.player import Player
from src.tournaments.tournament import Tournament
from src.game.game import Game
from src.tournaments.tournament_engine import TournamentEngine
from src.player.player_engine import PlayerEngine

class Config:
    def __init__(self):
        self._players_in_game : list[Player] = []
        self._tournament_engine : TournamentEngine | None = None
        self._game : Game | None = None
        self._already_set_players_in_game = False
        
    @property
    def players_in_game(self):
        return self._players_in_game
    
    @players_in_game.setter
    def players_in_game(self, players_in_game : list[Player]):
        self._players_in_game = players_in_game

    def add_player(self, player : Player):
        self._players_in_game.append(player)

    @property
    def tournament_engine(self):
        return self._tournament_engine
    
    @tournament_engine.setter
    def tournament_engine(self, tournament_engine : TournamentEngine):
        self._tournament_engine = tournament_engine

    @property
    def game(self):
        return self._game

    @game.setter
    def game(self, game : Game):
        self._game = game

    @property
    def already_set_tournament_engine(self)->bool:
        return  self._tournament_engine is not None
    
    @property
    def already_set_game(self)->bool:
        return  self._game is not None
    
    @property
    def already_set_players_in_game(self)->bool:
        return  self._already_set_players_in_game

    def is_valid_game(self)-> bool:
        # Todo: add game validation. For now, it's always valid
        # The idea of game validation is to check if the selected tournament allow the game
        return True
    
    def is_valid_tournament(self)->bool:
        # Todo: add tournament validation. For now, it's always valid
        # The idea of tournament validation is to check if the selected game allow the tournament
        return True
    
    def is_valid_player_amount(self)->bool:
        # Todo: add player amount validation. For now, it's always valid
        # The idea of player amount validation is to check if the selected tournament with the selected game allow the player amount
        return True
    
    def is_valid_configuration(self)->bool:
        return self.is_valid_game() and self.is_valid_tournament() and self.is_valid_player_amount()