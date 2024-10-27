import src.core.configuration as cfg

from conexiones.gestors.protocol import *
import logging
import struct
import pickle
import socket
import time
import threading

class CoreEngine():
    
    def __init__(self,config:cfg.Config) -> None:
        self._config = config
        self.PORT = 1112
        self.plays = []
        self.sock = -1
        self.game_instance = None
        self.plays_rlock = threading.RLock()
        self.data_cd = None
        
        logging.basicConfig(filename='client.log', filemode='w', format='%(asctime)s - %(message)s')
        client_down = cd()
        self.sock,pro = self.sendrecv_multicast()
        
        if self.sock!=-1:   
            if(type(pro) == cd):
                if pro.resume:            
                    resp = ''
                    while True:
                        resp = input('Do you want to continue the unfinished tournament? (y/n): ').lower()
                        if resp == 'y' or resp == 'n':
                            break
                    client_down.response = True if resp == 'y' else False
                    if(resp == 'y'):
                        resp = ''
                        while True:
                            resp = input('Do you want to watch it since the last checkpoint? (y/n): ').lower()
                            if resp == 'y' or resp == 'n':
                                break
                        client_down.state = True if resp == 'y' else False
                        client_down.ip = socket.gethostbyname(socket.gethostname())
                        #print(f'client_down.response={client_down.response} client_down.state={client_down.state} client_down.ip={client_down.ip}')
                    if(client_down.response):
                    
                        logging.warning(f'enviando client response')
                        self.data_cd = pickle.dumps(client_down)

                        #try:
                        #    self.sock.send(data)
                        #    x = pickle.loads(data)
                        #    if(type(x) == cd):
                        #        logging.warning(f'enviado cd state={x.state}')
                        #    #print(f'\nEnvie sg data={data}')
                        #    time.sleep(.5)
                        #    self.receiver(data)
                        #except socket.error as e:
                        #    print(f'Error send/recv x multicast {e.errno}')
        # self._log = {{}}

    @property
    def config(self)->cfg.Config:
        return self._config

    def start_tournament(self) -> None:
        
        start_game = sg()
        
        tournament = cfg.Tournament(0,self._config.tournament_engine, self._config.game)
        tournament.players = self._config.players_in_tournament 
              
        start_game.games = tournament
        start_game.ip = socket.gethostbyname(socket.gethostname())
        data = pickle.dumps(start_game)
        
           
#        for match in tournament:
#            print(match)
#            for action in match:
#                # self._log[tournament.id][match.game_id] = action
#                print(action)
#                for a in action:
#                    print(a)

        
#        print(f"The Winner is: {tournament.get_winner()}")
        return data
                 
    def sendrecv_multicast(self):
        try:
            message = pickle.dumps(socket.gethostbyname(socket.gethostname()))
            multicast_group = ('224.3.29.80', 10000)
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.sock.settimeout(0.9)
            # Set the time-to-live for messages to 1 so they do not
            # go past the local network segment.
            ttl = struct.pack('b', 1)
            self.sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)        
            while True:
                self.sock.sendto(message, multicast_group)
                while True:                        
                    try:
                        data, server = self.sock.recvfrom(1024)
                        #print(f'recibi de ip {server[0]}')
                    except socket.timeout:
                        print('Server timed out, no responses')
                        self.sock.settimeout(10)
                        break
                    except socket.error as e:
                        print('Error al recv de multicast ' + str(e.errno))
                        time.sleep(5)
                        break
                    else:
                        #print('en send multicast received {!r} from {}'.format( data, server))
                        if(server != None): 
                            data = pickle.loads(data)                                         
                            ip = server[0]

                            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)            

                            res=s.connect((ip, self.PORT))
                            if res==None:
                                print(f'Connected to server: {ip}')
                                logging.warning(f'Connected to server: {ip}')
                                return s,data
                            else:
                                print(f'Error Connected to server: {ip},  {res}')
                                self.sock.close()
                                break
                    #return -1
        except socket.error as e:
            print('Error al enviar multicast ' + str(e.errno))


