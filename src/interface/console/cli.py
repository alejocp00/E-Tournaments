from src.core.configuration import Config
from src.core.core_engine import CoreEngine
from colorama import Cursor, Fore, Back, Style
from os import system

class CLI:
    def __init__(self) -> None:
        self._config = Config()
        self._core_engine = CoreEngine(self._config)
        self._state_text = ""
        self._change_settings = False
        # TODO: Poblar constructor

    def print_players(self) -> str:
        if self._config.players_in_game is not None and len(self._config.players_in_game) > 0:
            self._state_text += Fore.GREEN + "Players: " + Fore.RESET + "\n"
            for player in self._config.players_in_game:
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
                self._core_engine.start_tournament()
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

        self._config.players_in_game = players

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
