import src.core.configuration as cfg

from conexiones.lib.protocol import *
import logging
import struct
import pickle
import socket
import time
import threading
import os 

class CoreEngine():
    
    def __init__(self,config:cfg.Config) -> None:
        self._config = config
        self.PORT = 1112
        self.plays = []
        self.sock = -1
        self.game_instance = None
        self.plays_rlock = threading.RLock()
        
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
#                if(client_down.response):
#                    
#                    logging.warning(f'enviando client response')
#                    data = pickle.dumps(client_down)
#
#            try:
#                self.sock.send(data)
#                x = pickle.loads(data)
#                if(type(x) == cd):
#                    logging.warning(f'enviado cd state={x.state}')
#                #print(f'\nEnvie sg data={data}')
#                time.sleep(.5)
#                self.receiver(data)
#            except socket.error as e:
#                print(f'Error send/recv x multicast {e.errno}') 
        # self._log = {{}}

    @property
    def config(self)->cfg.Config:
        return self._config

    def start_tournament(self) -> None:
        # Todo: tomar el id del torneo de algún lugar
        
        playcount = 0
        start_game = sg()
        
        tournament = cfg.Tournament(0,self._config.tournament_engine, self._config.game)
        tournament.players = self._config.players_in_tournament 
              
        start_game.games = tournament
        start_game.ip = socket.gethostbyname(socket.gethostname())
        data = pickle.dumps(start_game)
    
    #arreglar comunicacion con el servidor para que ejecute torneo
        try:
            self.sock.send(data)
            x = pickle.loads(data)
            if(type(x) == cd):
                logging.warning(f'enviado cd state={x.state}')
            #print(f'\nEnvie sg data={data}')
            time.sleep(.5)
            self.receiver(data)
        except socket.error as e:
            print(f'Error send/recv x multicast {e.errno}') 

    
        for match in tournament:
            print(match)
            for action in match:
                # self._log[tournament.id][match.game_id] = action
                print(action)
        
        print(f"The Winner is: {tournament.get_winner()}")
        
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

    def show_plays(self):
    
        playcount = 0
        while True:
            while playcount< len(self.plays):
                self.plays_rlock.acquire()
                play = self.plays[playcount]
                self.plays_rlock.release()
                if type(play) == str:
                    print(f'playcount={playcount} {play}')
                    logging.warning(f'playcount={playcount} {play}')
                    if play.find('WINNER --') > -1:
                        resp = ''
                        while True:
                            resp = input('Do you want to run another tournament? (y/n): ').lower()
                            if resp == 'y' or resp == 'n':
                                break
                        # os.system('cls')
                        if(resp == 'y'):
                            playcount = 0
                            self.plays = []
                            self.plays_rlock = threading.RLock()
                            start_game = sg()
                            tournaments = create_games()       
                            start_game.games = tournaments
                            start_game.ip = socket.gethostbyname(socket.gethostname())
                            data = pickle.dumps(start_game)
                            sock.send(data)
                        else:
                            os._exit(0)
                else:
                    # game_instance._players = play[0]
                    # game_instance._current_player_index = play[1]
                    # game_instance.config = play[3]
                    # game_instance.show_board()
                    print(f'playcount={playcount} player1: {play[0][0].name} player2: {play[0][1].name}, {play[1:]}')
                    #logging.warning(f'playcount={playcount} player1: {play[0][0].name} player2: {play[0][1].name}, {play[1:]}')
                playcount+=1  
                time.sleep(0.5)
    
    def receiver(self, tnmt):
    
        thread = threading.Thread(target=self.show_plays)
        thread.start()
        #print('entre en recv listo para recibir')
        confirm_package_recv = pr()
        while True:
            try:
                data = self.sock.recv(40960)
                #print(f'desp data sock')
                if (data):
                    sms = pickle.loads(data)                    
                    if(type(sms) == sgc):
                        try:
                            sock.send(tnmt)
                            os.system('cls')
                            print('Estoy enviando nuevamente el torneo')
                        except socket.error as e:
                            print(f'Error send/recv x multicast {e.errno}')

                    else: 
                        self.plays_rlock.acquire()
                        self.plays.extend(sms.list)
                        self.plays_rlock.release()                
                        confirm_package_recv.id = sms.id
                        data = pickle.dumps(confirm_package_recv)
                        q = self.sock.send(data)                    
                        a = len(sms.list)
                        logging.warning(f'sms.id={sms.id} len de sms = {a}')
                    #time.sleep(1)

            except socket.timeout:
                print('estoy esperando en el receiver')
                self.sock.settimeout(5)
            except socket.error as e: 
                print(f'Waiting...error: {e.errno}')
                self.sock.close()
                continue_game = sg()
                continue_game.continue_game = True
                print('Trying to connect a new server')
                while True:
                    self.sock, _ = sendrecv_multicast()
                    if(self.sock != None and sock != -1):
                        sms = pickle.dumps(continue_game)
                        try:
                            self.sock.send(sms)
                            time.sleep(0.5)
                            break
                        except socket.error as e:
                            print(f'socket error me conecte a otro servidor y le envie sms {e.errno}')
            except:
                print ('Error connect en recv y sigo en el ciclo')
                pass
