class round:
    def __init__(self) -> None:
        self.games = []
        self.time = 0
        self.winners = []

class tournament_server:
    def __init__(self) -> None:
        self.round = round()
        self.plays = 0
        self.tournament = None
        self.state_winners_sent=1 #-1 ronda 0 replicada ronda 1 enviada al cliente ronda
        self.finished=False
        self.client_down=False
        self.play_count = 0