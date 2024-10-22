class sd: #server down
    def __init__(self) -> None:
        self.active = False
        self.server_down = []
        self.sender = None
        self.sender_id = None
        self.already_sent = False
        self.resumed_games = []
        self.rep_leader = []
    
    def default(self):
        self.__init__()

class sgc: #start game continue
    def __init__(self) -> None:
        self.active = False        

class sg: #start game
    def __init__(self) -> None:
        self.active = False
        self.games = None
        self.ip = None
        self.continue_game = False
        

class dg: # distribute games
    def __init__(self) -> None:
        self.active = False
        self.games = None
        self.active_games = 0
        self.already_sent = False
        self.client_ip = None

class gr: #game replica
    def __init__(self) -> None:
        self.active = False
        self.update = []
        self.already_sent = False

class stl: #send to leader
    def __init__(self) -> None:
        self.play = None
        self.repl = None
        self.already_sent = False
        self.send = None
        self.pause = False
        self.tnmt_per_client = {}   
    
    def default(self):
        self.repl = None
        self.play = None
        self.tnmt_per_client = {}
            
class cd: #client down
    def __init__(self) -> None:
        self.resume = False
        self.state = False
        self.response = False
        self.ip = None

        
class pr: #confirm client package received
    def __init__(self) -> None:
        self.id = 0
        
class ps: #package sent to client
    def __init__(self) -> None:
        self.id = 0
        self.list = []