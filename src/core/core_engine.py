import src.core.configuration as cfg

class CoreEngine():
    
    def __init__(self,config:cfg.Config) -> None:
        self._config = config
        self._log = {{}}

    @property
    def config(self)->cfg.Config:
        return self._config

    def start_tournament(self) -> None:
        tournament = cfg.Tournament(self._config.tournament_engine, self._config.game)
        
        for match in tournament:
            for action in match:
                # self._log[tournament.id][match.game_id] = action
                print(action)