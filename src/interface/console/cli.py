from src.core.configuration import Config
from src.core.core_engine import CoreEngine
from colorama import Cursor, Fore, Back, Style
from os import system

from conexiones.gestors.protocol import pr,sgc,cd, sg

import logging
import pickle
import socket
import time
import threading
import os 

class CLI:
    def __init__(self) -> None:
        self._config = Config()
        self._core_engine = CoreEngine(self._config)
        self._state_text = ""
        self._change_settings = False
        
    def print_players(self) -> str:
        if self._config.players_in_tournament is not None and len(self._config.players_in_tournament) > 0:
            self._state_text += Fore.GREEN + "Players: " + Fore.RESET + "\n"
            for player in self._config.players_in_tournament:
                self._state_text += "\t" + str(player) +"\n"

    def print_game(self) -> str:
        if self._config.game is not None:
            self._state_text += Fore.GREEN + "Game: " + Fore.RESET + "\n"
            self._state_text += "\t" + str(self._config.game) + "\n"
            
    def print_tournament(self) -> str:
        if self._config.tournament_engine is not None:
            self._state_text += Fore.GREEN + "Tournament: " + Fore.RESET + "\n"
            self._state_text += "\t" + str(self._config.tournament_engine) + "\n"
            
    def select_configuration(self) -> None:
        if(self._core_engine.data_cd is not None):
            self.comunication_with_server(self._core_engine.data_cd)

        while True:
            
            # Print Players
            self.print_players()

            # Print Game
            self.print_game()

            # Print Tournament
            self.print_tournament()

            # Showing Menu
            options = ["Players","Game","Tournament","Exit"]

            # Check if any settings are already set
            for i in range(len(options)):
                if options[i] == "Players":
                    if self._config.already_set_players_in_game:
                        options[i] = "Change "
                    else:
                        options[i] = "Set "
                    options[i]+= "Players"
                elif options[i] == "Game":
                    if self._config.already_set_game:
                        options[i] = "Change "
                    else:
                        options[i] = "Set "
                    options[i] += "Game"
                elif options[i] == "Tournament":
                    if self._config.already_set_tournament_engine:
                        options[i] = "Change "
                    else:
                        options[i] = "Set "
                    options[i] += "Tournaments"

            # Check if all settings are set
            if self._config.is_valid_configuration():
                options[options.index("Exit")] = "Start with this settings"
                options.append("Exit")

            # Get input from user
            selected_option = self.option_selector("Select Option: ","Invalid Option", options)

            self._state_text = ""

            # Select option
            if "player" in options[selected_option].lower():
                self.set_players()
            elif "game" in options[selected_option].lower():
                self.set_game()
            elif "tournament" in options[selected_option].lower():
                self.set_tournament_engine()
            elif "start" in options[selected_option].lower():
                data = self._core_engine.start_tournament()
                self.comunication_with_server(data)
                input("Press Enter to restart...")
            elif "exit" in options[selected_option].lower():
                return

    def _clear_console(self) -> None:
        system("cls||clear")

    def option_selector(self,initial_prompt,error_message:str,options:list[str]) -> int:
        '''
        Selects an option from a list of options
        
        Parameters
        ----------
        initial_prompt : str
            Initial prompt to show the user
        error_message : str
            Message to show when an invalid option is selected
        options : list[str]
            List of options to select from
            
        Returns
        -------
        int
            Selected option
        '''

        selected_option = -1

        # Variables for handle errors
        exist_error = False
        error_input = ""
        # While option is not set, ask for input
        while selected_option < 0:
            # Clear the console
            self._clear_console()

            print(self._state_text)

            # Show options
            for i in range(len(options)):
                print(Fore.BLUE + str(i+1)+". " + Fore.RESET + options[i])

            # Prepare input text
            input_text = Fore.GREEN + initial_prompt + Fore.RESET

            # Check if there was an error
            if exist_error:
                input_text = Fore.RED + error_message + "\n" + "Wrong input: " + error_input + Fore.RESET + "\n" + input_text
                error_message = ""
                exist_error = False

            # Get input
            input_result = input(input_text)

            # Check validity
            if not input_result.isdigit() or int(input_result) < 1 or int(input_result) > len(options):
                # Clear the console
                exist_error = True
                error_input = input_result
            else:
                selected_option = int(input_result) - 1

        return selected_option

    def set_players(self):
        """ Select the players for the game
        """
        from src.core.importers import get_all_implementations_of, ImplementationsTypes
        from src.player.player import Player

        # Get number of players
        players = []
        engines = get_all_implementations_of(ImplementationsTypes.Player)
        one_more = True

        while one_more:
            name_of_player = input("Insert the name of player {}: ".format(len(players)+1))
            engine = self.option_selector("Select Player Engine: ","Invalid Option", [pair[0] for pair in engines])
            players.append(Player(name_of_player, engines[engine][1](),self._config.get_id_for_new_player()))

            one_more = self.option_selector("One more player?: ","Invalid Option", ["Yes","No"]) == 0

        self._config.players_in_tournament = players

    def set_game(self):
        from src.core.importers import get_all_implementations_of, ImplementationsTypes
        from src.game.game import Game

        games = get_all_implementations_of(ImplementationsTypes.Game)
        engine = self.option_selector("Select Game: ","Invalid Option", [pair[0] for pair in games])
        self._config.game = games[engine][1]()

    def set_tournament_engine(self):
        from src.core.importers import get_all_implementations_of, ImplementationsTypes
        from src.tournaments.tournament_engine import TournamentEngine

        engines = get_all_implementations_of(ImplementationsTypes.Tournament)
        engine = self.option_selector("Select Tournament Engine: ","Invalid Option", [pair[0] for pair in engines])
        self._config.tournament_engine = engines[engine][1]()

    def comunication_with_server(self, data):
        
        try:
            self._core_engine.sock.send(data)
            x = pickle.loads(data)
            if(type(x) == cd):
                logging.warning(f'enviado cd state={x.state}')
            #print(f'\nEnvie sg data={data}')
            time.sleep(.5)
            self.receiver(data)
        except socket.error as e:
            print(f'Error send/recv x multicast {e.errno}') 
        
    def show_plays(self):
    
        playcount = 0
        
        while True:
            while playcount< len(self._core_engine.plays):
                self._core_engine.plays_rlock.acquire()
                play = self._core_engine.plays[playcount]
                self._core_engine.plays_rlock.release()
                
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
                            self._core_engine.plays = []
                            self._core_engine.plays_rlock = threading.RLock()
                            self.select_configuration()
#                            tournaments = create_games()       
#                            start_game.games = tournaments
                            #start_game.ip = socket.gethostbyname(socket.gethostname())
                            #data = pickle.dumps(start_game)
                            #self.sock.send(data)
                        else:
                            os._exit(0)
                else:
                    # game_instance._players = play[0]
                    # game_instance._current_player_index = play[1]
                    # game_instance.config = play[3]
                    # game_instance.show_board()
                    print(f'jugada {playcount} : {play[0]}')
                    #print(f'playcount={playcount} player jugando: {play[0].player_name} otro player: {play[3].players[1 if play[0].player_id == 0 else 0].name}, {play[0]}')
                    #logging.warning(f'playcount={playcount} player1: {play[0][0].name} player2: {play[0][1].name}, {play[1:]}')
                playcount+=1  
                time.sleep(0.5)
            
            #
            #self.new = True
            #break
                   
    def receiver(self, tnmt):
    
        thread = threading.Thread(target=self.show_plays)
        thread.start()
        #print('entre en recv listo para recibir')
        confirm_package_recv = pr()
        while True:
            try:
                data = self._core_engine.sock.recv(40960)
                if (data):
                    sms = pickle.loads(data)                    
                    if(type(sms) == sgc):
                        try:
                            self._core_engine.sock.send(tnmt)
                            os.system('cls')
                            print('Estoy enviando nuevamente el torneo')
                        except socket.error as e:
                            print(f'Error send/recv x multicast {e.errno}')

                    else: 
                        self._core_engine.plays_rlock.acquire()
                        self._core_engine.plays.extend(sms.list)
                        self._core_engine.plays_rlock.release()                
                        confirm_package_recv.id = sms.id
                        data = pickle.dumps(confirm_package_recv)
                        q = self._core_engine.sock.send(data)                    
                        a = len(sms.list)
                        logging.warning(f'sms.id={sms.id} len de sms = {a}')
                    time.sleep(1)

            except socket.timeout:
                print('estoy esperando en el receiver')
                self._core_engine.sock.settimeout(5)
            except socket.error as e: 
                print(f'Waiting...error: {e.errno}')
                self._core_engine.sock.close()
                continue_game = sg()
                continue_game.continue_game = True
                print('Trying to connect a new server')
                while True:
                    self._core_engine.sock, _ = self._core_engine.sendrecv_multicast()
                    if(self._core_engine.sock != None and self._core_engine.sock != -1):
                        sms = pickle.dumps(continue_game)
                        try:
                            self._core_engine.sock.send(sms)
                            time.sleep(0.5)
                            break
                        except socket.error as e:
                            print(f'socket error me conecte a otro servidor y le envie sms {e.errno}')
            except:
                print ('Error connect en recv y sigo en el ciclo')
                pass
            
