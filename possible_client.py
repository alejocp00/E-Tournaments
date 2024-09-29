import sys
from chord import ChordNode

import logging
import struct
import pickle
import socket
import time
import threading
import os

PORT = 1112
plays = []
sock = -1
game_instance = None
plays_rlock = threading.RLock()

#! Implement client logic to create a new node to the CHORD and new tournament with socket zmq and not socket
def main(m:int):
    c = ChordNode(m)
    c.run()
    commands = {
        "join": c.join,
        "lookup": c.lookup,
        "predecessor":c.find_predecessor,
        "successor":c.find_succesor,
        "exit": c.exit,
        "ft":c.get_finger_table,
        "ns":c.get_node_set,
        "ip":c.get_ip_table
    }
    while True:
        try:
            usr_input = input().split()
            if len(usr_input) == 0:
                continue
            arg_0 = usr_input[0]
            try:
                command = commands[arg_0]
            except KeyError:
                print("Unrecognized command")
                continue

            try:
                args = []
                if arg_0 == "join" and len(usr_input) > 1:
                    args.append(usr_input[1])
                elif len(usr_input) > 1:
                    args.append(int(usr_input[1]))
            except IndexError:
                print("Bad Arguments")
                continue
            
            print(command(*args))
            if arg_0 == "exit":
                break
        
        except KeyboardInterrupt:
            print("Exit")
            c.joined = False
            c.online = False
            exit(1)

#    global sock
#    global playcount
#    global plays
#    global plays_rlock
#    logging.basicConfig(filename='client.log', filemode='w', format='%(asctime)s - %(message)s')
#    client_down = cd()
#    sock,pro = sendrecv_multicast()   
#    if sock!=-1:   
#        if(type(pro) == cd):
#            if pro.resume:            
#                resp = ''
#                while True:
#                    resp = input('Do you want to continue the unfinished tournament? (y/n): ').lower()
#                    if resp == 'y' or resp == 'n':
#                        break
#                client_down.response = True if resp == 'y' else False
#                if(resp == 'y'):
#                    resp = ''
#                    while True:
#                        resp = input('Do you want to watch it since the last checkpoint? (y/n): ').lower()
#                        if resp == 'y' or resp == 'n':
#                            break
#                    client_down.state = True if resp == 'y' else False
#                    client_down.ip = socket.gethostbyname(socket.gethostname())
#                    #print(f'client_down.response={client_down.response} client_down.state={client_down.state} client_down.ip={client_down.ip}')
#            if(not client_down.response):
#                playcount = 0
#                plays = []
#                plays_rlock = threading.RLock()
#                start_game = sg()
#                tournaments = create_games()       
#                start_game.games = tournaments
#                start_game.ip = socket.gethostbyname(socket.gethostname())
#                data = pickle.dumps(start_game)
#            else:
#                logging.warning(f'enviando client response')
#                data = pickle.dumps(client_down)
#            
#        try:
#            sock.send(data)
#            x = pickle.loads(data)
#            if(type(x) == cd):
#                logging.warning(f'enviado cd state={x.state}')
#            #print(f'\nEnvie sg data={data}')
#            time.sleep(.5)
#            receiver(data)
#        except socket.error as e:
#            print(f'Error send/recv x multicast {e.errno}')

def sendrecv_multicast():
    try:
        message = pickle.dumps(socket.gethostbyname(socket.gethostname()))
        multicast_group = ('224.3.29.80', 10000)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(0.9)
        # Set the time-to-live for messages to 1 so they do not
        # go past the local network segment.
        ttl = struct.pack('b', 1)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)        
        while True:
            sock.sendto(message, multicast_group)
            while True:                        
                try:
                    data, server = sock.recvfrom(1024)
                    #print(f'recibi de ip {server[0]}')
                except socket.timeout:
                    print('Server timed out, no responses')
                    sock.settimeout(10)
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
                                
                        res=s.connect((ip, PORT))
                        if res==None:
                            print(f'Connected to server: {ip}')
                            logging.warning(f'Connected to server: {ip}')
                            return s,data
                        else:
                            print(f'Error Connected to server: {ip},  {res}')
                            sock.close()
                            break
                #return -1
    except socket.error as e:
        print('Error al enviar multicast ' + str(e.errno))

def show_plays():
    global plays
    global plays_rlock 
    global game_instance
    global sock
    playcount = 0
    while True:
        while playcount< len(plays):
            plays_rlock.acquire()
            play = plays[playcount]
            plays_rlock.release()
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
                        plays = []
                        plays_rlock = threading.RLock()
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

def receiver(tnmt):
    global sock
    global plays
    global plays_rlock 
    thread = threading.Thread(target=show_plays)
    thread.start()
    #print('entre en recv listo para recibir')
    confirm_package_recv = pr()
    while True:
        try:
            data = sock.recv(40960)
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
                    plays_rlock.acquire()
                    plays.extend(sms.list)
                    plays_rlock.release()                
                    confirm_package_recv.id = sms.id
                    data = pickle.dumps(confirm_package_recv)
                    q = sock.send(data)                    
                    a = len(sms.list)
                    logging.warning(f'sms.id={sms.id} len de sms = {a}')
                #time.sleep(1)
                    
        except socket.timeout:
            print('estoy esperando en el receiver')
            sock.settimeout(5)
        except socket.error as e: 
            print(f'Waiting...error: {e.errno}')
            sock.close()
            continue_game = sg()
            continue_game.continue_game = True
            print('Trying to connect a new server')
            while True:
                sock, _ = sendrecv_multicast()
                if(sock != None and sock != -1):
                    sms = pickle.dumps(continue_game)
                    try:
                        sock.send(sms)
                        time.sleep(0.5)
                        break
                    except socket.error as e:
                        print(f'socket error me conecte a otro servidor y le envie sms {e.errno}')
        except:
            print ('Error connect en recv y sigo en el ciclo')
            pass

def create_games():
        global game_instance
        print('\nWelcome to Games Tournaments Simmulator!!!')        
        tournament_type = None
        while True:
            tournament_type =  input('Type the type of the tournament ( elimination (e) dos_a_dos (d) ): ')
            if tournament_type in ['e', 'd']:
                break
            
        game_type = None
        while True:
            game_type =  input('Type the type of the game ( nim (n) tictactoe (t) ): ')
            if game_type in ['n', 't']:
                break
        
        player_list = []
        flag = False
        while True:
            while True:
                try:
                    number_players = int( input('Type how many players for tournament: ') )
                    break
                except: pass
            for i in range(1, int(number_players/2)+1, 1):
                if(2 ** i == number_players):
                    flag = True
                    break
            if(flag):
                break

        while(True):  
            player_names = input('Type names of each player: ').split(' ')
            if(len(player_names) == number_players):
                break

        while(True):
            player_types = input('Type the type of each player ( optimal (o) random (r) ): ').split(' ')
            if(len(player_types) == number_players):
                for j in range(number_players):
                    if player_types[j] == 'o' or player_types[j] == 'r' :
                        continue
                else:
                    break
        
        initial_state = 0

        if(game_type == 'n'):
            while True:    
                try:
                    initial_state = int(input('Type how many sticks for each game: ') )
                    break
                except: pass
        
        if game_type == 'n':
            game_instance = nim_game()
        else:
            game_instance = tic_tac_toe()
        
        for j in range(number_players):
            if(player_types[j] == 'o'):
                player_list.append(optimal_player(player_names[j], game_type))
            else:
                player_list.append(random_player(player_names[j], game_type))
        
        if tournament_type == 'e':
            tournament_instance = elimination(player_list, initial_state,  game_instance)
        else:
            tournament_instance = dosAdos(player_list, initial_state,  game_instance)
    
        return tournament_instance

if __name__ == "__main__":
    arg = sys.argv
    if len(arg) == 1:
        m = 5
    else:
        m = int(arg[1])
    main(m)