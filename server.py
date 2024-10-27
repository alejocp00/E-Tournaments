import socket
import random
import hashlib
import struct
import threading
import pickle
import time
import logging
import copy
from conexiones.gestors.protocol import *
from conexiones.gestors.socket_thread import socket_thread
from src.tournaments.tournament_server import tournament_server

PORT = 1111
PORTCLIENT = 1112

# This class will be the server engine, where you add a new node if a new tournament is created, look up for the replica and other requests
class server:
    
    def __init__(self, bits) -> None:
        self.ip = socket.gethostbyname(socket.gethostname())
        self.id = self.get_id(bits)
        self.bits = bits
        
        self.succesor = [] #id, ip
        self.succesor_rlock = threading.RLock()
        
        self.predecesor = [] #id, ip
        self.predecesor_rlock = threading.RLock()
        
        self.leader = None
        self.leader_rlock = threading.RLock()
        
        self.leader_id = None
        
        self.sd = sd()
        self.sd_rlock = threading.RLock()
        
        self.sg = sg()
        self.sg_rlock = threading.RLock()

        self.dg = dg()
        self.dg_rlock = threading.RLock()
        
        self.gr = gr()
        self.gr_rlock = threading.RLock()
        
        self.stl = stl()
        
        self.cd = cd()
        
        self.sgc = sgc()
        self.ps = {}
        self.pr = {}

        self.finger_table = {((self.id+(2**i))%2**bits) : 0 for i in range(bits)} #node : start
        self.finger_table_rlock = threading.RLock()
        
        self.succesor_table = {self.id : self.ip}
        self.succesor_table_rlock = threading.RLock()
        
        self.connection_server = {}
        self.connection_client = {}
        
        self.connections_out = {}
        self.connections_out_rlock = threading.RLock()
        
        self.connections_in = {}
        self.connections_in_rlock = threading.RLock()

        self.multicast_closed = False

        self.lock = threading.Lock()            
        
        self.game_threads = []
        self.game_pause = False
        self.game_list = []
        
        self.game_replicas = {}
        self.game_replicas_rlock = threading.RLock()
        
        self.send_leader = []
        self.send_leader_rlock = threading.RLock()        
        self.send_leader_count = 0
        self.server_out = 0
        
        self.play_clients = {}
        self.play_clients_rlock = threading.RLock()

        self.sock_client=None        
        self.lock_client = threading.Lock()    
        
        self.tnmt_per_client = {}
        self.tnmt_per_client_replica = {}
        self.tnmt_per_client_rlock  = threading.RLock()
        
        self.stl_rlock  = threading.RLock()
        
        self.chkp_repl = 0 #checkpoint
        self.chkp_play = 0
        
        self.rep = []
        self.rep_rlock  = threading.RLock()
    
    def receive_multicast(self):
        try:
            multicast_group = '224.3.29.80'
            server_address = ('', 10000)
            # Create the socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            # Bind to the server address
            sock.bind(server_address)
            # Tell the operating system to add the socket to the multicast group on all interfaces.
            group = socket.inet_aton(multicast_group)
            mreq = struct.pack('4sL', group, socket.INADDR_ANY)        
            sock.setsockopt(socket.IPPROTO_IP,  socket.IP_ADD_MEMBERSHIP, mreq)
        except socket.error as e:
            print(f'Error al crear server multicast {e.errno}')
            return
        print(f'SERVER READY')
        sock.settimeout(10)
        while True:
                try:
                    data, address = sock.recvfrom(4096)
                except socket.timeout:  

                    if self.leader == None or (self.id == list(self.succesor_table.keys())[-1] and self.id != self.leader_id and not len(self.succesor)):  
                        if len(self.succesor_table)==1: 
                            self.leader = self.ip
                            self.leader_id = self.id
                            self.predecesor = []
                            self.succesor = []
                            logging.warning('en receive_multicast. solo quedo en succesor_table 1 servidor')
                        else:
                            a = list(self.succesor_table.keys())[-1]
                            if(self.id == a):
                                next_id = next(iter(self.succesor_table.keys()))
                                if(self.succesor_table[next_id] not in self.connections_out):
                                    res=self.connect_to(self.succesor_table[next_id])
                                    self.succesor_rlock.acquire()
                                    self.succesor = [next_id, self.succesor_table[next_id]]
                                    self.succesor_rlock.release()
                                    logging.warning(f'---------------en receive_multicast me conecte (retorne del conect_to {res}) al nodo de id mas bajo para cerrar anillo: {next_id}')

                            elif(self.id == next(iter(self.succesor_table.keys()))):
                                prev_id = list(self.succesor_table.keys())[-1]
                                self.predecesor_rlock.acquire()
                                self.predecesor = [prev_id, self.succesor_table[prev_id]]
                                self.predecesor_rlock.release()
                                logging.warning(f'---------------en receive_multicast soy el id mas pequeno y se me conecta el mayor, su id es: {prev_id}')

                        self.update_tables()
                        # print(f'en recv multicas self.succesor_table= {self.succesor_table}')
                        # print(f'en recv multicas self.finger_table={self.finger_table}')
                except  :
                    logging.warning('en rev multicas except')
                    pass
                else:          
                    if (data):
                        data = pickle.loads(data)
                        if(type(data) == int): #servidor solicitando entrar
                            data = self.receive_server(data, address, sock)
                        else: #cliente solicitando entrar
                            if (self.ip == self.leader and not self.game_pause):
                                self.sg.ip = data
                                if(data in self.tnmt_per_client):
                                    logging.warning(f'self.tnmt_per_client[data].finished={self.tnmt_per_client[data].finished}')
                                logging.warning(f'self.tnmt_per_client={self.tnmt_per_client} ')
                                if(data in self.tnmt_per_client and not self.tnmt_per_client[data].finished):
                                    logging.warning(f'poniendo cd en true')
                                    self.cd.resume = True
                                sms = pickle.dumps(self.cd)
                                sock.sendto(sms, address)
                                self.cd.resume = False
                                logging.warning(f'en recv mult le envie mi ip al cliente {address}, data={data}')

    def update_tables(self):
        self.update_finger_table()
        if self.leader == None or self.game_pause:
            self.leader_rlock.acquire()    
            self.leader = list(self.succesor_table.values())[-1]
            self.leader_id = list(self.succesor_table.keys())[-1]
            self.leader_rlock.release()
        self.finger_connections() 
        
        if self.ip==self.leader:
            if self.sock_client==None:
                thread_rec = threading.Thread(target=self.create_server_client,name='create_server_client')
                thread_rec.start()
                show_thread = threading.Thread(target=self.update_play_clients,name='update_play_clients')
                show_thread.start()
                print('SERVER LEADER')
                
        else:
            if  self.leader not in self.connections_in:
                self.tnmt_per_client_replica = {}                        
                self.send_leader_replica = []
            if self.sock_client!=None:
                self.sock_client.close()
                print('>>>>> dejé de ser server leader <<<<<')
        
    def receive_server(self,data, address, sock):  
                    self.stl.pause
                    self.succesor_rlock.acquire()
                    self.predecesor_rlock.acquire()
                    if self.ip==address[0]: 
                        pass                
                    elif (len(self.succesor) == 0 and data > self.id):
                        logging.warning(f'en receive_multicast. No tengo sucesor y self.id = {self.id} < {data} = data')
                        my_id = pickle.dumps([self.id, self.succesor_table, False, self.leader, self.leader_id])
                        sock.sendto(my_id, address)
                        time.sleep(.5)
                        logging.warning(f'en receive multicast estoy enviando a {address[0]} succesor_table {self.succesor_table}')
                        res=self.connect_to(address[0])
                        if res==None:
                            self.succesor_rlock.acquire()
                            self.succesor = [data, address[0]]
                            self.succesor_rlock.release()
                            logging.warning(f'-------------------Me conecte a {address[0]} : {data}')
                        else:
                            logging.warning(f'-------------------NOOO Me conecte a {address[0]} : {data} retorne {res}')
                            pass

                    elif(len(self.predecesor) == 0 and data < self.id):
                        logging.warning(f'en receive_multicast. No tengo predecesor y self.id = {self.id} > {data} = data')                        
                        my_id = pickle.dumps([self.id, self.succesor_table, True, None, self.leader, self.leader_id])
                        sent= sock.sendto(my_id, address)
                        self.predecesor_rlock.acquire()
                        self.predecesor = [data, address[0]]
                        self.predecesor_rlock.release()
                        logging.warning(f'Le digo a {address[0]} : {data} que se conecte a mi ({sent} bytes)')
                    
                    elif(len(self.succesor) and data > self.id and self.id > self.succesor[0]):
                        logging.warning(f'en receive_multicast. Mi sucesor es menor que yo self.id = {self.id} < {self.succesor[0]} = sucesor y data mayor que yo')
                        if self.succesor[1] in self.connections_out:
                            self.connections_out[self.succesor[1]].active = False
                        res=self.connect_to(address[0])
                        if res==None:
                            self.succesor_rlock.acquire()
                            self.succesor = [data, address[0]]
                            self.succesor_rlock.release()
                            logging.warning(f'-------------------Me conecte a {address[0]} : {data}')
                        else:
                            logging.warning(f'-------------------NOOOOO Me conecte a {address[0]} : {data} retorne {res}')
                            pass
                        
                    elif(len(self.predecesor) and data > self.predecesor[0] and self.id < self.predecesor[0]):
                        logging.warning(f'en receive_multicast. Mi predecesor es mayor que yo self.id = {self.id} < {self.predecesor[0]} = predecesor y data mayor que yo')
                        if self.predecesor[1] in self.connections_in:
                            self.connections_in[self.predecesor[1]].active = False
                        my_id = pickle.dumps([self.id, self.succesor_table, True, self.predecesor, self.leader, self.leader_id])
                        sock.sendto(my_id, address)
                        self.predecesor_rlock.acquire()
                        self.predecesor = [data, address[0]]
                        self.predecesor_rlock.release()
                        logging.warning(f'Le digo a {address[0]} : {data} que se conecte a mi')
                    
                    elif(len(self.succesor) and self.succesor[0] < self.id and data < self.succesor[0]):
                        res=self.connect_to(address[0])
                        if res==None:
                            if self.succesor[1] in self.connections_out:
                                self.connections_out[self.succesor[1]].active = False
                            self.succesor_rlock.acquire()
                            self.succesor = [data, address[0]]
                            self.succesor_rlock.release()
                            logging.warning(f'-------------------Me conecte a {address[0]} : {data}')
                        else:
                            logging.warning(f'-------------------NOOOOO Me conecte a {address[0]} : {data} retorne {res}')
                            pass
                    
                    elif(len(self.predecesor) and self.predecesor[0] > self.id and data < self.id):
                        logging.warning(f'en receive_multicast. Mi predecesor es mayor que yo self.id = {self.id} < {self.predecesor[0]} = predecesor y data mayor que yo')
                        if self.predecesor[1] in self.connections_in:
                            self.connections_in[self.predecesor[1]].active = False
                        my_id = pickle.dumps([self.id, self.succesor_table, True, self.predecesor, self.leader, self.leader_id])
                        sock.sendto(my_id, address)
                        self.predecesor_rlock.acquire()
                        self.predecesor = [data, address[0]]
                        self.predecesor_rlock.release()
                        logging.warning(f'Le digo a {address[0]} : {data} que se conecte a mi')
                        
                    elif(data < self.id and data > self.predecesor[0]):
                        logging.warning(f'en receive_multicast. {data} es menor ( < ) que mi id : {self.id} y mayor que e de mi predecesor : {self.predecesor[0]}')
                        my_id = pickle.dumps([self.id, self.succesor_table, True, self.predecesor, self.leader, self.leader_id])
                        self.connections_in_rlock.acquire()
                        if self.predecesor[1] in self.connections_in:
                            self.connections_in[self.predecesor[1]].active = False 
                        self.connections_in_rlock.release()
                        sock.sendto(my_id, address) 
                        self.predecesor_rlock.acquire()
                        self.predecesor = [data, address[0]]
                        self.predecesor_rlock.release()
                        logging.warning(f'Le digo a {address[0]} : {data} que se conecte a mi')
                    
                        
                    elif(data > self.id and data < self.succesor[0]):
                        logging.warning(f'en receive_multicast. {data} es mayor que mi id : {self.id} y menor que e de mi sucesor : {self.succesor[0]}')
                        self.connections_out_rlock.acquire()
                        if self.succesor[1] in self.connections_out:
                            self.connections_out[self.succesor[1]].active = False
                        self.connections_out_rlock.acquire()
                        res=self.connect_to(address[0])
                        if res==None:
                            self.succesor_rlock.acquire()
                            self.succesor = [data, address[0]]
                            self.succesor_rlock.release()
                            logging.warning(f'------------------Me conecte a : {address[0]} : {data}  ')
                        else:
                            logging.warning(f'------------------NOOOOOO Me conecte a {address[0]} : {data} retorne {res}')
                            pass
                    else:
                        logging.warning('en receive_multicast. El que entro {address[0]} no tiene nada que ver conmigo')
                        pass

                    self.succesor_rlock.release()
                    self.predecesor_rlock.release()                    
                    self.succesor_table_rlock.acquire()   
                    self.succesor_table[data] = address[0]
                    self.succesor_table = dict(sorted(self.succesor_table.items(), key=lambda item:item[0]))
                    self.succesor_table_rlock.release()   
                    self.stl.pause = False
                    logging.warning(f'termine de ejecutar el receive-m y succeso_table es {self.succesor_table}')
                    return None

    def send_multicast(self):
        message = pickle.dumps(self.id)
        multicast_group = ('224.3.29.80', 10000)
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.settimeout(0.9)
        ttl = struct.pack('b', 1)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)

        try:
            while True:
                sent=sock.sendto(message, multicast_group) # Send data to the multicast group
                if sent!=0:
                    break
            print(f'Multicast Sent')
            while True:
                try:
                    data, server = sock.recvfrom(1024)
                except socket.timeout:
                    logging.warning('NADIE MAS RESPONDE al send multicast--timed out, no more responses')
                    sock.close()
                    break
                except socket.error as e:
                    logging.warning('Error en send multicast ' + str(e.errno))
                    sock.close()
                    break
                else:
                    logging.warning('en send multicast received {!r} from {}'.format( data, server))
                    
                    if(server != None): 
                        data = pickle.loads(data)                                         
                        ip = server[0]
                        if(data[2]):
                            res=self.connect_to(ip)
                            logging.warning(f'en send_multicast. -------------------Me conecte a {ip} : {data} retorne {res}')
                            self.succesor_rlock.acquire()
                            self.succesor = [data[0], ip]
                            self.succesor_rlock.release()
                            sock.close()  
                            
                            if(data[3] != None):
                                self.predecesor_rlock.acquire()
                                self.predecesor = data[3]
                                self.predecesor_rlock.release() 
                        else:
                            logging.warning(f'Se me conecto {ip} con id = {data[0]} que es menor que el mio')
                            self.predecesor_rlock.acquire()
                            self.predecesor = [data[0], ip]
                            self.predecesor_rlock.release() 

                        self.succesor_rlock.acquire()
                        self.succesor_table = self.succesor_table | data[1]
                        self.succesor_table = dict(sorted(self.succesor_table.items(), key=lambda item:item[0]))
                        self.succesor_rlock.release()                   
                        
                        if(data[4] != None):
                            self.leader = data[4]
                            self.leader_id = data[5]

                        break
        except socket.error as e:
            logging.warning('Error al enviar multicast en send_multicast ' + str(e.errno))
            sock.close()
        except:
            logging.warning('en send_multicast. Error pde ser de connect_to')
            sock.close()
        finally:
            logging.warning('closing socket send multicast')
            pass
    
    def create_server(self):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if sock==-1:
                print('Error al crear el socket ')
                exit()
            if sock.bind((socket.gethostbyname(socket.gethostname()), PORT))==-1:
                print('Error en el bind')
                exit()
            logging.warning('creando server ip: ' + socket.gethostbyname(socket.gethostname()))
            if sock.listen(5)==-1:
                print('Error al activar el listen')
                exit()
            while True:
                client_socket, client_address = sock.accept()                
                ip=client_address[0]
                self.connections_in_rlock.acquire()
                self.connections_in[ip]= socket_thread(client_socket, True)
                self.connections_in_rlock.release()                
                logging.warning(f"******************Acepte conexion de: {ip}!")      
                while self.leader==None:
                    pass         
                thread_rec = threading.Thread(target=self.receiver,name='create_server'+ip, args=(ip, ))
                thread_rec.start()
        except:
            #print('Error al crear server en except')
            pass
     #1       

    def create_server_client(self):
            self.sock_client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            if self.sock_client==-1:
                print('Error al crear el socket client')
                exit()
            if self.sock_client.bind((socket.gethostbyname(socket.gethostname()), PORTCLIENT))==-1:
                print('Error en el bind client')
                exit()
            logging.warning('creando server client ip: ' + socket.gethostbyname(socket.gethostname()))
            if self.sock_client.listen(5)==-1:
                print('Error al activar el listen client')
                exit()
            while True:
                client_socket, client_address = self.sock_client.accept()                
                ip=client_address[0]
                self.connections_in_rlock.acquire()
                self.connections_in[ip]= socket_thread(client_socket, True)
                self.connections_in_rlock.release()                
                logging.warning(f"******************Acepte conexion del cliente: {ip}!")                           
                thread_rec = threading.Thread(target=self.receiver,name='recv_create_server_clien'+ip, args=(ip, ))
                thread_rec.start()
                
                #thread_rec.join()

    def send_server(self, ip):
        play_count = self.chkp_repl
        send_leader_count = self.chkp_play   #si send_server orig se inicializa con 0, si no a partir del ultimo chkp
        b=len(self.send_leader)
        logging.warning(f'QQQQQQ Al entrar en send server play_count = {play_count} send_leader_count={send_leader_count} self.send_leader_count={self.send_leader_count} len sen{b}')
        times = 0
        lon = 0
        len_send_leader = 0
        server_out = 0

        sock = self.connections_out[ip].sock
        try:
            sock.settimeout(5)
            while self.connections_out[ip].active:
                with self.lock:
                    sms = None #mensaje en string
                    sm = None  #mensaje en bytes
                    if(len(self.succesor) > 0 and ip == self.succesor[1] and not self.sd.already_sent and (self.sd.active or len(self.sd.server_down) > 0)):
                        sms = self.sd
                        self.sd.already_sent = True
                        logging.warning(f'estoy enviando sms xq alguien se cayo: {self.sd}')
                    elif(self.dg.active and len(self.succesor) and ip == self.succesor[1] and not self.dg.already_sent ):
                        sms = self.dg
                        self.dg.already_sent = True
                        self.dg.active_games =len(self.game_threads)
                        a = len(self.dg.games)
                        logging.warning(f'/////--------Estoy enviando mensaje DG len(self.dg.games)={a} a ip {ip}')
                    elif ((self.leader_id != None  and ip == self.find_node(self.leader_id)) or (self.ip==self.leader and len(self.succesor) > 0 and ip == self.succesor[1]))  and not self.stl.pause :
                        if len(self.rep)==len(self.connection_server)-1:  self.rep=[]
                        if not len(self.rep):
                            self.stl.default()
                            if play_count<len(self.gr.update) and not self.game_pause:
                                self.gr_rlock.acquire()
                                lon =  len(self.gr.update)
                                self.stl.repl = self.gr.update[play_count:lon] 
                                self.gr_rlock.release()
                                sms = self.stl
                                self.chkp_repl = play_count
                            
                            if self.ip!=self.leader:
                                self.send_leader_rlock.acquire()
                                len_send_leader=len(self.send_leader)    
                                if send_leader_count<len_send_leader:
                                    self.stl.play = self.send_leader[send_leader_count:len_send_leader]
                                    sms = self.stl
                                    self.chkp_play = send_leader_count
                                self.send_leader_rlock.release()
                                    
                            if self.ip==self.leader :
                                if len(self.tnmt_per_client)>0 :  #es lider y ya tiene torneos asociados
                                    self.stl.tnmt_per_client = self.tnmt_per_client                                    
                                    sms = self.stl
                    elif not self.stl.pause and (self.stl.repl!=None):
                        logging.warning(f'entre en el rep con ip:{ip}')
                        if ip not in self.rep:
                            self.stl.play = None
                            self.rep.append(ip)
                            sms = self.stl                        
                    if sms == None:
                        times += 1                        
                        if times == 1000000:
                            sms = 'pasivo'

                    try:
                        if sms != None:
                            sm = pickle.dumps(sms)
                            sock.send(sm)  #msg.encode('UTF-8')
                            
                            if(type(sms) == sd and self.ip != self.sd.sender):                                
                                self.sd.default()
                            elif type(sms) == dg:
                                logging.warning(f'send server DG enviado a ip {ip}')    
                                self.dg.active = False
                                self.dg.already_sent = False
                            elif type(sms) == stl:                                 

                                if self.stl.repl!=None: 
                                    play_count = lon                         
                                    for i in self.stl.repl:
                                        logging.warning(f'&.&.& sender envio stl.rep a ip={ip}  j1:{i[0][0][0].name} j2:{i[0][0][1].name} jugada:{i[0][1:]}  ')
                                    #    pass
                                if self.stl.play!=None:     
                                    logging.warning(f'&.&.& sender envio stl.play leader={self.leader} send_leader_count={send_leader_count} len_send_leader={len_send_leader}')
                                    for i in self.stl.play:
                                        logging.warning(f'&.&.& sender envio stl.play a ip={ip}  j1:{i[0][0][0].name} j2:{i[0][0][1].name} jugada:{i[0][1:]}  ')
                                    #    pass
                                    send_leader_count = len_send_leader 

                                self.stl.default()    
                            times=0 #se realizo envio
                            time.sleep(.2)

                    except socket.error as e: 
                        if ip != self.succesor[1]:
                            logging.warning('lock en send_server error ip != self.succesor[1]')
                            self.game_pause = True 
                            if type(sms) == stl:
                                self.stl.pause = True 
                        else:
                            self.game_pause = True 
                            if type(sms) == stl:
                                self.stl.pause = True 
                            logging.warning('lock en send_server error {} de {}  '.format(e.errno, ip))
                            self.connections_out[ip].active=False
                            self.succesor_table.pop(self.succesor[0]) 
                            self.sd.server_down.append(self.succesor)
                            self.sd.resumed_games.append(self.succesor[1])
                            succ_keys = list(self.succesor_table.keys())
                            pos = succ_keys.index(self.id)
                            logging.warning(f'lock en send_server antes de entrar al for leader={self.leader}')
                            for i in range((pos + 1)%len(succ_keys), len(succ_keys) + pos, 1):
                                    idd = succ_keys[i%len(succ_keys)]
                                    logging.warning(f'lock en send_server entre  al for {self.id}=={idd}')
                                    if self.id==idd:
                                        res = 1                                        
                                        self.predecesor = []
                                        self.succesor = []

                                        if self.ip != self.leader:
                                            if sms!=None and type(sms)==stl:
                                                play_count = self.chkp_repl
                                                send_leader_count = self.chkp_play
                                                self.send_leader_count = self.chkp_play 
                                            res=self.replica_leader() #el no era el leader cuando se quedo solo
                                            logging.warning(f'en lock error send server desde play_count={play_count} send_leader_count={send_leader_count} len send leader={len(self.send_leader)}')                                            
                                        self.update_tables()
                                        
                                        if res: #reanudando torneo y poniendo en send leader lo que quedo por enviar en stl
                                            for i in self.sd.server_down:
                                                if(i[1] in self.connections_in and i[1] in self.sd.resumed_games):
                                                    logging.warning(f'Voy a empezar a reanudar juegos de {i[1]} connc_out={self.connections_out}')
                                                    self.start_replicas(i[1])
                                                    self.connections_in.pop(i[1])
                                                    self.sd.resumed_games.remove(i[1])
                                                    
                                        self.stl.pause = False
                                        self.game_pause = False
                                        self.sd.default()
                                        if ip in self.connections_out:
                                            self.connections_out[ip].active=False
                                    else:
                                        ipp = self.succesor_table[idd]
                                        logging.warning(f'en send_server. Me voy a conectar a {ipp}----------------------')
                                        res = self.connect_to(ipp)

                                        if (res==None):
                                            if sms!=None and type(sms)==stl:
                                                    play_count = self.chkp_repl
                                                    send_leader_count = self.chkp_play
                                            previous_leader = self.leader
                                            logging.warning(f'en send_server -------Me conecte a {ipp} leader={self.leader} play_count={play_count} send_leader_count={send_leader_count}')
                                            
                                            self.succesor = [idd, ipp]
                                            self.update_tables()
                                            self.sd.sender = self.ip
                                            self.sd.sender_id = self.id
                                            self.sd.active = True
                                            
                                            if self.ip == self.leader and self.ip!=previous_leader:
                                                self.send_leader_count = self.chkp_play 
                                            
                                            if self.tnmt_per_client!=None and len(self.tnmt_per_client)>0:
                                                self.game_pause = False
                                                self.stl.pause = False
                                            
                                            if(self.dg.active):
                                                a = len(self.dg.games)
                                                logging.warning(f'sock error con DG.active=true {self.dg.client_ip} en ip {ip} y len sms.games={a}')
                                                for index, i in enumerate(self.dg.games):
                                                    print(f'sock error de send server con DG.act del client {self.dg.client_ip} game_list[{index}] es: player1={i[0]._players[0].name}, player2={i[0]._players[1].name}')
                                                    pass
                                                
                                                self.distribute_games(self.dg.games, self.dg.client_ip,self.dg.active_games)
                                                sock = self.connections_out[ipp].sock
                                                sm = pickle.dumps(self.dg)
                                                sock.send(sm)
                                                self.dg.active = False
                                                self.dg.already_sent = False
                                                
                                            break
                                        else:                        
                                            logging.warning(f'en send_server. No pude conectarme a : {ipp}, error {res}, voy pal sgte idd es {idd}  ')
                                            if ip in self.connections_out:
                                                self.connections_out[ip].active=False
                                            self.sd.server_down.append([idd, ipp])
                                            self.sd.resumed_games.append(ipp)
                            for i in self.sd.server_down:
                                self.succesor_table.pop(i[0])
                        break
        
        except KeyError as e:
            logging.warning(f'send server except keyerror {KeyError} , sali del procedimiento ip {ip}  connec ot {self.connections_out} connec in ={self.connections_in}')                        
            pass
        
        if ip in self.connections_out:
            self.connections_out_rlock.acquire()
            self.connections_out.pop(ip)
            self.connections_out_rlock.release()
            self.connection_server.pop(ip)
            sock.close()
    
    def receiver(self, ip):
        sock = self.connections_in[ip].sock
        try:
            while self.connections_in[ip].active:
                try:
                    data = sock.recv(4096)
                    if(data):
                        try:
                            sms = pickle.loads(data)
                        except:
                            #print(f'Error en recv pickle. continuo data:{len(data)}')
                            pass

                        if(type(sms) == sd):
                            logging.warning(f'========= Me llego {sms}')
                            if(sms.sender == self.ip):
                                self.sd_rlock.acquire()
                                self.sd.default()
                                self.sd_rlock.release()                                                                
                                logging.warning(f'Ya todos actualizaron self.send_leader_count={self.send_leader_count} self.chkp_play={self.chkp_play}')

                                if len(sms.rep_leader) > 0:
                                    logging.warning(f'Ya todos self.ip={self.ip} leader={self.leader} sms.rep_leader[0]={sms.rep_leader[0]}')
                                    self.tnmt_per_client_replica = sms.rep_leader[0]
                                    if(self.ip == self.leader):
                                        logging.warning(f'Ya todos antes de replica_leader self.send_leader_count ={self.send_leader_count} self.send_leader[self.chkp_play]={self.send_leader[self.chkp_play]} len send {len(self.send_leader)}')
                                        self.replica_leader()
                                    self.stl.pause = False 
                                    self.game_pause = False
                                logging.warning(f'en recv SD sender {sms.sender} leader={self.leader} !!!!!!!!!YA TODOS ACTUALIZARON!!!! desp self.send_leader_count ={self.send_leader_count} self.chkp_play={self.chkp_play}')
                            else:
                                self.stl.pause = True 
                                self.game_pause = True
                                
                                for i in sms.server_down:
                                    logging.warning(f'Voy a empezar a reanudar juegos de {i[1]} leader={self.leader} conn in {self.connections_in}') 
                                    if(i[1]==self.leader):
                                        if(i[1] in self.connections_in):
                                            self.sd.rep_leader = [self.tnmt_per_client_replica] #CORRECTO
                                            logging.warning(f'en recv sd i[1] in self.connections_in salve torneo {self.tnmt_per_client_replica}')
                                            # for i in self.tnmt_per_client: 
                                            #     for k in self.tnmt_per_client[i].round.games:
                                            #         logging.warning(f'replica leader j1 : {k[0]._players[0].name}, j2: {k[0]._players[1].name} jug:{k[1:]}')
                                            #     for j in self.tnmt_per_client[i].round.winners:
                                            #         logging.warning('replica leader  WINNER ---> '+ j[0].name )
                                        elif len(sms.rep_leader) > 0: 
                                            self.tnmt_per_client_replica = sms.rep_leader[0]
                                        
                                    if(i[1] in self.connections_in):
                                        if i[1] in sms.resumed_games: 
                                            logging.warning(f'Voy a empezar a reanudar juegos')
                                            self.start_replicas(i[1]) 
                                            sms.resumed_games.remove(i[1])
                                        self.connections_in.pop(i[1])
                                self.sd_rlock.acquire()
                                self.sd.resumed_games = sms.resumed_games
                                self.sd.sender = sms.sender #ip del que mando el mensaje
                                self.sd.sender_id = sms.sender_id
                                self.sd.server_down.extend(sms.server_down)
                                self.sd_rlock.release()
                                self.predecesor_rlock.acquire()
                                if(self.predecesor in sms.server_down):
                                    self.predecesor = [sms.sender_id, sms.sender]
                                self.predecesor_rlock.release()
                                logging.warning(f'en recv SD sender de {sms.sender} !!!!!!!!!¨ANTES DE ACTUALIZAR game_pause={self.game_pause}')
                                self.update_succesor_table(sms.server_down)
                                self.update_tables()
                                
                                if(self.ip == self.leader):
                                    logging.warning(f'Ya todos en la parte de abajo self.ip == self.leader self.chkp_play={self.chkp_play} ')
                                    self.replica_leader()
                                    
                                self.stl.pause = False 
                                self.game_pause = False
                                logging.warning(f'self.predecesor: {self.predecesor}')
                                logging.warning(f'self.succesor_table: {self.succesor_table}')
                                logging.warning(f'ACTUALICE TODAS LAS COSAS!!!!!!!!!self.send_leader_count={self.send_leader_count} len send leader={len(self.send_leader)}')
                            self.sd.already_sent = False

                        elif type(sms) == sg:
                            #print(f'Received from Client: {ip} Continue game: {sms.continue_game}')
                            #el lider envia los juegos a los servidores
                            if not sms.continue_game:
                                #print(f'voy a crear hilo send_client {ip} y llama a distribute')

                                if(ip in self.tnmt_per_client):
                                    self.play_clients[ip]=[]
                                    self.pr[ip] = []
                                    self.ps[ip] = ps()                                    
                               
                                self.tnmt_per_client[ip] = tournament_server() 
                                self.tnmt_per_client[ip].tournament = sms.games
                                games = []
                                matchs = []
                                for match in self.tnmt_per_client[ip].tournament:
                                    matchs = match
                                    break
                                k= 0
                                for i in range(len(matchs)):
                                    r = matchs[i]
                                    games.append([r, k])
                                    k +=2
                                self.tnmt_per_client[ip].plays = len(games)
                                self.tnmt_per_client[ip].round.games = copy.deepcopy(games)
                                logging.warning(f'DDDDDDDDDDDDDDDevuelto de matching ip={ip} self.tnmt_per_client[ip].plays={self.tnmt_per_client[ip].plays} juegos')
                                if(ip not in self.connection_client):
                                    self.connection_client[ip] = threading.Thread(target=self.send_client,name='send_client'+ip, args=(ip,))
                                    self.connection_client[ip].start()
                                #self.distribute_games(games, sms.ip, 0)
                                distrib = threading.Thread(target=self.distribute_games,name='distribinic'+ip, args=(games, sms.ip,0,))
                                distrib.start()
                            else:
                                logging.warning('voy a continuar el juego que se quedo a mitad tmnt:={self.tnmt_per_client}')      
                                if ip not in self.connection_client:        
                                    self.connection_client[ip] = threading.Thread(target=self.send_client,name='send_client_continue'+ip, args=(ip,))
                                    self.connection_client[ip].start()

                        elif(type(sms) == dg):
                            self.dg_rlock.acquire()
                            distrib = threading.Thread(target=self.distribute_games,name='distrib'+ip, args=(sms.games, sms.client_ip,sms.active_games,))
                            distrib.start()
                            self.dg_rlock.release()
                            a = len(sms.games)
                            logging.warning(f'ssssssssRecibi mensaje DG de {sms.client_ip} en ip {ip} y sms.active ={sms.active } len sms.games={a}')


                        elif(type(sms) == stl):
                            if ip == self.leader:                                    
                                self.tnmt_per_client_replica = sms.tnmt_per_client 
                            elif sms.play!=None:
                                self.send_leader_rlock.acquire()
                                self.send_leader.extend(sms.play)
                                self.send_leader_rlock.release()
                                for i in sms.play:
                                    logging.warning(f'&&& &&& recv stl de ip={ip} stl sms.play j1:{i[0][0][0].name} j2:{i[0][0][1].name} jugada:{i[0][1:]}  stl.repl:{sms.repl}')
                                    pass
                                
                            if sms.repl!=None:                                
                                if ip!=self.leader:
                                    self.send_leader_rlock.acquire()
                                    self.send_leader.extend(sms.repl)
                                    self.send_leader_rlock.release()
                                    for i in sms.repl:
                                        logging.warning(f'&& & &&& recv de stl sms.repl de ip={ip} stl sms.repl j1:{i[0][0][0].name} j2:{i[0][0][1].name} jugada:{i[0][1:]}  ')
                                        pass
                                self.game_replicas_rlock.acquire()
                                if(ip not in self.game_replicas):
                                    self.game_replicas[ip] = []
                                self.game_replicas[ip].extend(sms.repl)
                                self.game_replicas_rlock.release()

                        elif type(sms) == pr:
                            self.pr[ip].append(sms.id)
                        
                        elif(type(sms) == cd):
                            logging.warning(f'response={sms.response} state={sms.state} ip={sms.ip}')
                            logging.warning(f'connection_client={self.connection_client}')
                            if sms.ip not in self.connection_client:        
                                self.connection_client[ip] = threading.Thread(target=self.send_client,name='send_client_continue'+ip, args=(ip,))
                                self.connection_client[ip].start()
                                
                            if(sms.state):
                                #print(f'cd sms.state={sms.state}')
                                #print(f'finished={self.tnmt_per_client[ip].finished}')
                                self.tnmt_per_client[sms.ip].play_count = 0
                            else:
                                logging.warning(f'entre en cd state=false')
                                #print(f'recibi cd nombre hilo= {self.connection_server[ip].name} is_alive={self.connection_server[ip].is_alive} client[sms.ip].play_count={self.tnmt_per_client[sms.ip].play_count}')
                                time.sleep(.5)
                            self.tnmt_per_client[sms.ip].client_down = False
                            
                        sms = None    
                except socket.timeout: 
                    logging.warning('en receiver timeout, espero 0.2 seg y sigo')          
                    time.sleep(0.2)
                    continue

                except socket.error as e: 
                    logging.warning(f'en receiver. Se cayo {ip} socket,error={e.errno} connection_in = {self.connections_in}'  )
                    if ip in self.connections_in:
                        self.connections_in_rlock.acquire()
                        self.connections_in[ip].active = False    
                        self.connections_in_rlock.release()
                    break
        except KeyError:
            logging.warning(f'receiver except keyerror {KeyError} , sali del procedimiento ip {ip}  connec ot {self.connections_out} connec in ={self.connections_in}')                                
            pass
        #print(f'en recv sali de {ip}')
        if ip in self.connections_in: #se pregunta pq puede que haya entrado un mensaje antes de active false y el pop se hizo alante
            sock.close()
        logging.warning(f'en receiver. Deje de recibir de {ip}')
    
    def connect_to(self, ip):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)                
            res=s.connect((ip, PORT))
            logging.warning(f'resultado de la connect: {res} ip {ip}')
            if res == None:
                self.connections_out_rlock.acquire()
                self.connections_out[ip]= socket_thread(s, True)
                self.connections_out_rlock.release()
                self.connection_server[ip] = threading.Thread(target=self.send_server, args=(ip,))
                self.connection_server[ip].start()
                logging.warning(f'en conect_to connect_out es {self.connections_out}')
            return res
        except socket.error as e:
            print (f'en connect_to error - {e.errno}')
            return e.errno

    def send_client(self, ip):
            logging.warning(f'vvvvvvventre en send client,  ip={ip}  connec_in= {self.connections_in} self.send_leader_count = {self.send_leader_count} len send lead={len(self.send_leader)}')
            package_send = 0
            time = 0
            if ip in self.tnmt_per_client:
                logging.warning(f'en send  client finis={self.tnmt_per_client[ip].finished} down:{self.tnmt_per_client[ip].client_down} self.send_leader_count = {self.send_leader_count} len send lead={len(self.send_leader)}')
            if ip not in self.ps:
                self.ps[ip]=ps()
                self.pr[ip]=[]
            while True:            
                if(ip in self.tnmt_per_client and not self.tnmt_per_client[ip].client_down and not self.tnmt_per_client[ip].finished):
                    time = 0
                    try:
                        sock = self.connections_in[ip].sock
                        sms = None
                        if(self.sgc.active):
                            sms = pickle.dumps(self.sgc)       

                        elif (ip in self.play_clients):
                            lon=len(self.play_clients[ip])                    
                            if self.tnmt_per_client[ip].play_count < lon:
                                package_send += 1
                                self.ps[ip].id = package_send
                                self.ps[ip].list = self.play_clients[ip][self.tnmt_per_client[ip].play_count:lon]
                                sms = pickle.dumps(self.ps[ip])
                                #logging.warning(f'en send client ip={ip} a enviar package_send={package_send} play_count={self.tnmt_per_client[ip].play_count} de len:{lon}')

                        if (sms != None):
                            sent = sock.send(sms)  #msg.encode('UTF-8')
                            a = pickle.loads(sms)
                            if(type(a) == sgc):
                                self.sgc.active = False
                            else:
                                while self.ps[ip].id>0 and self.ps[ip].id not in self.pr[ip] and not self.tnmt_per_client[ip].client_down:
                                    #logging.warning(f'en send client ps')
                                    pass                                                                
                                for i in self.ps[ip].list:
                                    if type(i) == str:
                                        space=4
                                        if i.find('WINNER --') > -1:
                                            self.tnmt_per_client[ip].finished=True
                                            print(f'FINISH ip={ip}')
                                            space=2
                                        verify_winners_sent = i.split( ' ' )
                                        winners_tosent=len(verify_winners_sent)-space
                                        logging.warning(f' {i} tiene {winners_tosent} ganadores  ')
                                    else:
                                        logging.warning(f' enviado en send client ip= {ip} j1:{i[3].players[0].name} j2:{i[3].players[1].name} jug: {i[0]} sender_leader_count={self.send_leader_count}')
                                        pass
                                
                                self.tnmt_per_client[ip].play_count =lon                   
                        else:
                            if not self.tnmt_per_client[ip].finished:
                                if(ip in self.tnmt_per_client)  and not self.tnmt_per_client[ip].client_down and not self.game_pause: # and self.tnmt_per_client[ip].state_winners_sent:
                                    self.tnmt_per_client[ip].round.time += 1
                                    if self.tnmt_per_client[ip].round.time >= 5000000: #buscar juegos que no hayan comenzado para lanzarlos
                                        logging.warning(f'voy a unfinished_game ip={ip} self.send_leader_count = {self.send_leader_count} len send lead={len(self.send_leader)}')
                                        self.unfinished_game(ip)
                                        self.tnmt_per_client[ip].round.time = 0
                    except socket.error as e:  
                        self.tnmt_per_client[ip].client_down = True
                else:
                    time += 1
                    if time >= 1000000000000:
                        print('limpiando cliente {ip}')
                        sock.close()
                        self.connections_in.pop(ip)
                        self.tnmt_per_client.pop(ip)
                        self.play_clients.pop(ip)
                        self.game_replicas.pop(ip)
                        self.pr.pop(ip)
                        self.ps.pop(ip)
                        return
                
    def update_succesor_table(self, server_down):
        self.succesor_table_rlock.acquire()
        for i in server_down:
            if(i[0] in self.succesor_table):
                self.succesor_table.pop(i[0])
                logging.warning(f'succesor table = {self.succesor_table} despues de eliminar i[0] = {i[0]}')
        self.succesor_table_rlock.release()
    
    def finger_connections(self):
        for i in self.finger_table:
            res=None
            if (self.finger_table[i] not in self.connections_out and self.finger_table[i] != self.ip):
                res=self.connect_to(self.finger_table[i])
                logging.warning(f'--------------me conecte a {self.finger_table[i]} por finger table res={res}')
            return res
    
    def update_finger_table(self):
        self.finger_table_rlock.acquire()
        for i in self.finger_table:
            for index, j in enumerate(self.succesor_table):
                if index == 0:
                    pos = j
                if(i <= j):
                    self.finger_table[i] = self.succesor_table[j]
                    break
            else:
                self.finger_table[i] = self.succesor_table[pos]
        self.finger_table_rlock.release()
    
    def find_node(self, node):
        for i in self.finger_table:
            if node >= i:
                return self.finger_table[i]
        id = list(self.finger_table.keys())[-1]
        ip = self.finger_table[id]
        return ip
    
    def get_id(self, key_length):
        key = str(socket.gethostbyname(socket.gethostname())) + str(random.randint(0, 10000000))
        hash_func = hashlib.sha1
        hash_value = int(hash_func(key.encode()).hexdigest(), 16)
        return hash_value % (2 ** key_length)
    
    def set_play_clients(self, send_play):
        ip = send_play[1]   #la jugada corresponde a esta ip

        if ip in self.connections_in and  ip in self.tnmt_per_client:
            if ip not in self.play_clients:
                self.play_clients[ip] = []
                #print(f'play_client esta vacio ip:{ip} y self.tnmt_per_client = {self.tnmt_per_client}')

            for i in self.tnmt_per_client[ip].round.games :
                if send_play[3].players[0].name == i[0]._players[0].name  and  send_play[3].players[1].name == i[0]._players[1].name:
                    break
            else:
                return 1
            
            self.play_clients[ip].append(send_play)
            self.tnmt_per_client[ip].round.time = 0
            
            logging.warning(f'++++++ set_play_clients añadido {send_play[3].players} al cliente {ip}, J1:{send_play[3].players[0].name} J2:{send_play[3].players[1].name} jugada={send_play[0]} sender_leader_count={self.send_leader_count} {ip in self.play_clients}')
            if send_play[3].get_winner()[0].name != 'Unfinished':
             #       send_play[0][0][send_play[0][1]].points += 1
                    self.tnmt_per_client[ip].tournament.put_match_result(send_play[3])
                    self.tnmt_per_client[ip].round.winners.append([send_play[3].get_winner(),[send_play[3].players[0].name, send_play[3].players[1].name]])
                    total_winners = len(self.tnmt_per_client[ip].round.winners)
                    winners = ''
                    for i in self.tnmt_per_client[ip].round.winners:
                        if i[0][0].name == 'Draw':
                            send_play[3].solve_draw()
                            i[0] = send_play[3].get_winner()
                        winners = winners +  i[0][1].name  + ', '
                    if( total_winners == self.tnmt_per_client[ip].plays):                        
                        logging.warning(f'++++++++++++self.winner, termino una vuelta  ganadores ')

                        if total_winners==1:
                        #or not self.tnmt_per_client[ip].tournament.round:
                        #    if not self.tnmt_per_client[ip].tournament.round:
                        #        self.tnmt_per_client[ip].tournament.players = [k[0] for k in self.tnmt_per_client[ip].round.winners]
                            for _ in self.tnmt_per_client[ip].tournament:
                                continue            
                            win = self.tnmt_per_client[ip].tournament.get_winner()  
                            
                            logging.warning(f'set play WINNER --->  {win}  cliente {ip} ')
                            if win.name is None:
                                win =  win[1][0]
                            self.play_clients[ip].append('WINNER --->  ' + win.name)
                            return 1
                        else:
                            #self.tnmt_per_client[ip].tournament.players = [k[0] for k in self.tnmt_per_client[ip].round.winners]
                            #winners = ''
                            #for i in self.tnmt_per_client[ip].tournament.players:
                            #    
                            #    winners = winners +  i[1].name  + ', '
                            self.play_clients[ip].append('ROUND FINISHED, ganadores ' + winners)

                            logging.warning(f'ROUND FINISHED, ganadores {winners} self.send.count={self.send_leader_count} len self.send..count={len(self.send_leader)} ')
                            logging.warning(f'CANTIDAD DE GANADORES {len(self.tnmt_per_client[ip].tournament.players)}')
                            
                            games = []
                            matchs = []
                            for match in self.tnmt_per_client[ip].tournament:
                                matchs = match
                                break
                            k= 0
                            for i in range(len(matchs)):
                                r = matchs[i]
                                games.append([r, k])
                                k +=2
                            
                            self.tnmt_per_client[ip].round.games = copy.deepcopy(games)
                            b = len(games)
                            logging.warning(f'CANTIDAD DE JUEGOS {b}')
                            self.tnmt_per_client[ip].plays = 0
                            self.tnmt_per_client[ip].plays = len(games)
                            self.tnmt_per_client[ip].round.winners = []
                            logging.warning(f'lllllllllll voy a llamar a distribute games en set_play_client')
                            self.distribute_games(games, ip, len(self.game_threads))
                    else:
                        logging.warning(f'Annadi ganador a {send_play[3].get_winner()} jugada:{send_play[0]}')
                        pass
            return 1
        return 0

    def distribute_games(self, game_list, client_ip, active_predecesor_games):
        with threading.Lock():
            if(len(game_list)):
                logging.warning(f'en distrib game listado de juegos a distribuir ip={client_ip}')
                # for index, i in enumerate(game_list):
                #     logging.warning(f'en distrib game recibi list de {client_ip} game_list[{index}]: player1={i[0]._players[0].name}, player2={i[0]._players[1].name}')
                #     pass

                if self.ip==self.leader and len(self.succesor)==0 and len(self.predecesor)==0:
                    logging.warning('wwwwwwwww soy l lider y estoy solo, abro todos los juegos que reciba')
                    for i in game_list:
                        self.game_threads.append(threading.Thread(target=self.start_game, args=(i[0], client_ip, i[1], )))
                        self.game_threads[-1].start()
                else:
                    take_game = False
                    len_game_threads = len(self.game_threads)
                    if self.ip==self.leader:
                        if len_game_threads <= active_predecesor_games:
                            logging.warning(f'SIIIIIIII cogi juego en el LEADER {len_game_threads} <= {active_predecesor_games}')
                            take_game = True
                        else:
                            logging.warning(f'soy leader pero no cogi pq {len_game_threads} <= {active_predecesor_games}')
                            pass                        
                    elif len_game_threads < active_predecesor_games:
                        logging.warning(f'SIIII cogi juego en un server que NO es lider {len_game_threads} < {active_predecesor_games}')
                        take_game = True
                    else:
                        logging.warning(f'NOOOOO cojo juego, que siga para otro server pq  mis juegos {len_game_threads} >= {active_predecesor_games}')
                        pass
                                        
                    if take_game:                        
                        game = game_list[0][0] 
                        game_id = game_list[0][1]
                        self.game_list.append([game,client_ip])                        
                        logging.warning(f'----del cliente={client_ip} en el distribute_game cogi jugador1={game_list[0][0]._players[0].name}, jugador2={game_list[0][0]._players[1].name}')
                        self.game_threads.append(threading.Thread(target=self.start_game, args=(game, client_ip, game_id, )))
                        self.game_threads[-1].start()
                        game_list.pop(0)                    
                    if len(game_list)==0:
                        self.dg.active = False
                        self.dg.games = []
                    else:
                        self.dg.games = game_list
                        self.dg.client_ip = client_ip
                        self.dg.active = True             
                        self.dg.already_sent=False
                        self.dg.active_games=len(self.game_threads)

                    b = len(self.dg.games)
                    logging.warning(f'  ===== en distrib game dejo en self.dg.games {b} juegos ')
            else:
                logging.warning('Ya se acabo de repartir juegos')
                pass
    
    def start_game(self, game, client_ip, game_id):        
        logging.warning(f'*****Voy a empezar a jugar cliente {client_ip} j1:{game._players[0].name}, j2:{game._players[1].name}')
        game.init_game_state()
        while game.get_winner()[0].name == 'Unfinished': 
            game.__next__()
            if(len(game._log)):
                x = game._log[-1]                
                cpy = copy.deepcopy(game)
                play = [x, client_ip, game_id, cpy]
                self.gr_rlock.acquire()
                self.gr.update.append(play) #protocolo para la replica
                self.gr_rlock.release()                
                if self.ip==self.leader:
                    self.send_leader_rlock.acquire()
                    self.send_leader.append(play) #protocolo para la replica
                    self.send_leader_rlock.release()
                    #logging.warning(f'guarde en send leader del client_ip {client_ip} j1:{x[0][0].name} j2:{x[0][1].name} Jugada: {x[1:]} sender_leader_count={self.send_leader_count} len send server={len(self.send_leader)}')
                #logging.warning(f'ejecute turno en ip={client_ip} j1:{x[0][0].name} j2:{x[0][1].name} y la jug: {x[1:]} si leader:{self.leader} send_leader_count={self.send_leader_count}') #tiene la ultima jugada
                time.sleep(0.5)
        if game.get_winner()[1] is not None:
            print(f'Juego terminado gano: {game.get_winner()[1]} entre  jugador1={game._players[0].name}, jugador2={game._players[1].name}')
            logging.warning(f'Juego terminado gano: {game.get_winner()[1]}  jugador1={game._players[0].name}, jugador2={game._players[1].name}')
        else :
            print(f'Juego empatado  entre  jugador1={game._players[0].name}, jugador2={game._players[1].name}')
        self.game_threads.pop(0)
        
    def restart_tnmt(self):
        self.tnmt_per_client={}
        self.tnmt_per_client_replica = {}
        self.send_leader_count = 0
        self.send_leader = []
        self.gr.update = []
        self.sgc.active = True
        self.pr=[]

    def start_replicas(self, ip):
        print(f'estoy en start replicas {ip}')
        if ip in self.game_replicas:
            mark_ids = []
            reps = list(self.game_replicas[ip])
            for i in range(len(reps)-1, -1, -1):

                if([reps[i][2], reps[i][1]] not in mark_ids):
                    logging.warning(f'start replicas   j1:{reps[i][0][0][0].name} j2:{reps[i][0][0][1].name} jugada: {reps[i][0][1:]}')
                    mark_ids.append([reps[i][2],reps[i][1]])
                    self.resume_game(reps[i])
    
    def resume_game(self, game):
        
        game[0][0] #players
        game[0][1] #current_player index
        game[0][2] #move
        game[0][3] #stick count
        game[0][4] #winner
        game[1] #client_ip
        game[2] #game_id
        game[3] #game copy

        logging.warning('Estoy reanudando un juego')
        if(game[0][4] == ''):
            x_game = game[3].copy()                
            x_game._players = game[0][0]
            x_game._current_player_index = game[0][1] + 1   
            x_game.config = game[0][3]
            x_game.winner = game[0][4]    
            self.game_list.append([x_game,game[1]])
            logging.warning(f'>>>>>>>> voy a llamar a start_game J1: {x_game._players[0].name} J2: {x_game._players[1].name} jugada:{game[0][1:]}')
            self.game_threads.append(threading.Thread(target=self.start_game, args=(x_game, game[1], game[2], )))
            self.game_threads[-1].start()
            
        elif(game[0][4] == 'Tie'):
            x_game = game[3].copy()
            x_game._players = game[0][0]
            self.game_list.append([x_game,game[1]])
            logging.warning(f'>>>>>>>> voy a llamar a start_game tabla J1: {x_game._players[0].name} J2: {x_game._players[1].name} jugada:{game[0][1:]}')
            self.game_threads.append(threading.Thread(target=self.start_game, args=(x_game, game[1], game[2], )))
            self.game_threads[-1].start()
        
        else: #es un ganador pero tengo que ver si ya se mostro, si pertenece al round activo...
            a = game[0][0]
            logging.warning(f'RRRREPLICA CON LA ULTIMA JUGA DE UN JUEGO ganador: {game[0][4]} entre j1:{a[0].name} j2:{a[1].name} jugada:{game[0][1:]}')
            self.verify_add_send_leader(game)
            
    def replica_leader(self):    
        logging.warning(f'replica leader tnmt_per_client_replica={self.tnmt_per_client_replica} tnmt_per_client ={self.tnmt_per_client}')
        if self.tnmt_per_client_replica!=None: 
            self.tnmt_per_client = self.tnmt_per_client_replica
            for i in self.tnmt_per_client:
                self.tnmt_per_client[i].play_count = 0
            self.tnmt_per_client_replica = {}

            logging.warning(f'replica leader mostrar los winner y games len(self.tnmt_per_client)={len(self.tnmt_per_client)} game_pause{self.game_pause} ')
            # for i in self.tnmt_per_client: 
            #     for k in self.tnmt_per_client[i].round.games:
            #         logging.warning(f'replica leader j1 : {k[0]._players[0].name}, j2: {k[0]._players[1].name}')
            #     for j in self.tnmt_per_client[i].round.winners:
            #         logging.warning('replica leader  WINNER ---> '+ j[0].name )
            
            self.verify_rest_send_leader()
            return 1
        else:
            logging.warning('En replica leader reinicia el torneo')
            self.restart_tnmt()
            self.sgc.active = True
            return 0
        
    def verify_rest_send_leader(self):
            self.send_leader_count = self.chkp_play
            len_send_leader = len(self.send_leader)
            logging.warning(f'En verify_rest_send_leader {self.send_leader_count} < {len_send_leader} ?')
            if self.send_leader_count < len_send_leader:
                self.send_leader_rlock.acquire()
                to_pop = []
                for i in range(self.chkp_play,len_send_leader):
                    if self.pop_send_leader(self.send_leader[i]):
                        game=self.send_leader[i]
                        logging.warning(f'pop send leader eliminar j1: {game[0][0][0].name } j2:{game[0][0][1].name} jugada:{game[0][1:]}')
                        to_pop.append(i)
                                
                for i in range(len(to_pop)-1, -1, -1):
                    self.send_leader.pop(to_pop[i])   
                    if i<= self.send_leader_count:
                        self.send_leader_count -= 1 
                self.send_leader_rlock.release()   
            
    def update_play_clients(self):
        while True:
            while self.send_leader_count<len(self.send_leader) and not self.game_pause:
                x = self.set_play_clients(self.send_leader[self.send_leader_count])
                self.send_leader_count += x
                    
    def add_replicas(self, play, ip):
        for i in play:
            if(i[0][4] == ''):
                self.game_replicas[ip].append(i)
            else:
                for j in self.game_replicas[ip]:
                    if(j[2] == i[2]):
                        self.game_replicas[ip].remove(j)    
                
    def verify_add_send_leader(self, game):
        logging.warning(f'entreEEEE en verify add send leader con ganador: {game[0][4]}  con j1: {game[0][0][0].name } j2:{game[0][0][1].name} jugada:{game[0][0][1:]}len send lead:{len(self.send_leader)}')
        player = None
        if self.ip == self.leader:
            for i in self.tnmt_per_client[game[1]].round.winners :
                if i[0].name == game[0][4] and game[0][0][0].name == i[1][0] and game[0][0][1].name == i[1][1]:
                    break
            else:
                for i in self.tnmt_per_client[game[1]].round.games :
                    if (game[0][0][0].name == i[0]._players[0].name or game[0][0][0].name == i[0]._players[1].name  ) and (game[0][0][1].name == i[0]._players[0].name or game[0][0][1].name == i[0]._players[1].name):
                        player = 1
        if player!=None:               
            if (game not in self.send_leader):
                logging.warning(f'entreEEEE a anadir jugada de send_leader_replica a send_leader con j1:{game[0][0][0].name } j2:{game[0][0][1].name} jugada:{game[0][0][1:]}')
                self.send_leader_rlock.acquire()
                self.send_leader.append(game)
                self.send_leader_rlock.release()  
        
    def pop_send_leader(self, game):
        logging.warning(f'entre en pop send leader  j1:{game[0][0][0].name} j2:{game[0][0][1].name} jugada:{game[0][1:]}')
        ip = game[1]
        if ip in self.tnmt_per_client:
            if game[0][4] != '':                
                for i in self.tnmt_per_client[ip].round.winners :
                    if i[0].name == game[0][4] and game[0][0][0].name == i[1][0] and game[0][0][1].name == i[1][1]:
                        logging.warning(f'entre en pop send leader {i[0].name} es winner')
                        return 1
                
            for i in self.tnmt_per_client[ip].round.games :
                if game[0][0][0].name == i[0]._players[0].name and  game[0][0][1].name == i[0]._players[1].name:
                    return 0
        return 1
        
    def add_elem_send_leader(self,i):
        self.send_leader_rlock.acquire()
        for j in self.send_leader:
            if(i[0][0][0].name == j[0][0][0].name and i[0][0][1].name == j[0][0][1].name and i[0][1:] == j[0][1:] and i[1] == j[1]):
                logging.warning(f'add_send_leade() encontre NO anado j == j1:{j[0][0][0].name} j2:{j[0][0][1].name} jugada:{j[0][1:]} cliente:{j[1]}')
                break
        else:
            self.send_leader.append(i)
            logging.warning(f'add_send_leader() no encontre anado  j1:{i[0][0][0].name } j2:{i[0][0][1].name} jug={i[0][1:]}')
            self.send_leader_rlock.release()  
            return 1
        self.send_leader_rlock.release()  
        return 0

    def compare_player_winner(self, ip, game):
        for i in self.tnmt_per_client[ip].round.winners:            
            if (game[0]._players[0].name == i[0].name or game[0]._players[1].name == i[0].name) and [game[0]._players[0].name, game[0]._players[1].name] == i[1]:
                #logging.warning(f'compare winner encontro {i[0].name}')
                return 1
        return 0        
    
    def unfinished_game(self,ip):
        logging.warning(f'juegos incompletos {len(self.tnmt_per_client[ip].round.winners)} winners y {len(self.tnmt_per_client[ip].round.games)}')
        winners = ''
        for i in self.tnmt_per_client[ip].round.winners:
            winners = winners +  i[0].name  + ', '
        logging.warning(f'juegos incompletos  round.winners {winners} ')
        game_list = []
        for i in self.tnmt_per_client[ip].round.games:
            #logging.warning(f'juegos incompletos juego de games de la ip={ip} j1:{i[0]._players[0].name} j2:{i[0]._players[1].name}')  
            if self.compare_player_winner(ip, i):
                pass
            else:
                for j in self.game_list: #buscando en la lista de juegos de la pc
                    if  i[0]._players[0].name == j[0]._players[0].name and i[0]._players[1].name == j[0]._players[1].name and ip==j[1]: 
                        logging.warning(f'juegos incompletos el juego se ejecuta en esta pc busco gr.update j1:{i[0]._players[0].name} j2:{i[0]._players[1].name}ip={ip} ')                        
                        x = len(self.gr.update) - 10 if len(self.gr.update) > 10 else -1
                        for k in range(len(self.gr.update)-1, -1, -1):  #buscar en gr.update la ultima jugada y anadirla al send leader                            
                            if i[0]._players[0].name == self.gr.update[k][0][0][0].name and i[0]._players[1].name == self.gr.update[k][0][0][1].name and ip == self.gr.update[k][1]:
                                logging.warning(f'juegos incompletos encontro en gr update[k]: j1:{self.gr.update[k][0][0][0].name} j2:{self.gr.update[k][0][0][1].name} jug:{self.gr.update[k][0][1:]}')
                                self.resume_game(self.gr.update[k])
                                break
                        break   
                else:
                    logging.warning(f'juegos incompletos ver replica j1:{i[0]._players[0].name} j2:{i[0]._players[1].name}')  
                    if ip in self.game_replicas:
                        reps = list(self.game_replicas[ip])
                        #logging.warning(f'juegos incompletos ver si esta en replica j1:{i[0]._players[0].name} j2:{i[0]._players[1].name}')  
                        for k in range(len(reps)-1, -1, -1):    #buscar en las replicas ultima jugada
                            if(i[0]._players[0].name == reps[k][0][0].name and i[0]._players[1].name == reps[k][0][1].name and ip == reps[k][0][1]):
                                logging.warning(f'juegos incompletos encontre replica j1:{i[0]._players[0].name} j2:{i[0]._players[1].name} jugada:{reps[k]}')
                                self.resume_game(reps[k])        
                                break                                
                        else: #no esta en la replica tampoco
                            logging.warning(f'juegos incompletos no hubo jugadas en replica j1:{i[0]._players[0].name} j2:{i[0]._players[1].name}')  
                            game_list.append(i)
                    else: #no esta en la replica tampoco
                        logging.warning(f'unfinished games buscar en send leader j1:{i[0]._players[0].name} j2:{i[0]._players[1].name}')
                        x = len(self.send_leader) - 10 if len(self.send_leader) > 10 else -1
                        for k in range(len(self.send_leader)-1, x, -1):    
                            if(i[0]._players[0].name == self.send_leader[k][3].players[0].name and i[0]._players[1].name == self.send_leader[k][3].players[1].name and self.send_leader[k][1] == ip):
                                self.send_leader_count = k
                                logging.warning(f'unfinished games encontre en send leader j1:{i[0]._players[0].name} j2:{i[0]._players[1].name}')
                                self.resume_game(self.send_leader[k])
                                break
                        else:
                            game_list.append(i)
                    
        if len(game_list)>0:
            b = len(game_list)
            logging.warning(f'juegos incompletos hice distribute dentro de incompleta {b}')
            self.distribute_games(game_list, ip,len(self.game_threads))



def main():
    logging.basicConfig(filename='server.log', filemode='w', format='%(asctime)s - %(message)s')#, filemode='w', format='%(message)s')
    s = server(160)
    thread = threading.Thread(target=s.create_server)
    thread.start()    
    s.send_multicast()    
    thread2 = threading.Thread(target=s.receive_multicast)
    thread2.start()
    
main()