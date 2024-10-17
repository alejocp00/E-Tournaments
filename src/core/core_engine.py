import src.core.configuration as cfg

class CoreEngine():
    
    def __init__(self,config:cfg.Config) -> None:
        self._config = config
        # self._log = {{}}

    @property
    def config(self)->cfg.Config:
        return self._config

    def start_tournament(self) -> None:
        # Todo: tomar el id del torneo de algún lugar
        tournament = cfg.Tournament(0,self._config.tournament_engine, self._config.game)
        tournament.players = self._config.players_in_tournament
        
        for match in tournament:
            print(match)
            for action in match:
                # self._log[tournament.id][match.game_id] = action
                print(action)
        
        print(f"The Winner is: {tournament.get_winner()}")