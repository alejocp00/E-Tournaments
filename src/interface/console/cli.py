from src.core.configuration import Config
from colorama import Cursor, Fore, Back, Style
from os import system

class CLI:
    def __init__(self) -> None:
        self._config = Config()
        # TODO: Poblar constructor

    def select_configuration(self) -> None:
        # Todo: Show Actual settings

        # Showing Menu
        options = ["Players","Game","Tournament","Exit"]
        
        # Check if any settings are already set
        for i in range(len(options)):
            if options[i] == "Players":
                if self._config.already_set_players_in_game():
                    options[i] = "Change "
                else:
                    options[i] = "Set "
            elif options[i] == "Game":
                if self._config.already_set_game():
                    options[i] = "Change "
                else:
                    options[i] = "Set "
            elif options[i] == "Tournament":
                if self._config.already_set_tournament_engine():
                    options[i] = "Change "
                else:
                    options[i] = "Set "

        # Check if all settings are set
        if self._config.is_valid_configuration():
            options[options.index("Exit")] = "Start with this settings"
            options.append("Exit")
        
        # Get input from user
        selected_option = self.option_selector("Select Option: ","Invalid Option", options)
        
        # Select option
        if "player" in options[selected_option].lower():
            self._config.set_players()
        elif "game" in options[selected_option].lower():
            self._config.set_game()
        elif "tournament" in options[selected_option].lower():
            self._config.set_tournament_engine()
        elif "start" in options[selected_option].lower():
            self._config.start_tournament() # Todo: Who starts the tournament?
        elif "exit" in options[selected_option].lower():
            return
        
        
        # Check if all settings are set
        if self._config.is_valid_configuration():
            message = "" # Todo: Show Actual settings
            message += Fore.GREEN + "All settings are set. Did you want to start the tournament or change some settings?" + Fore.RESET
            options = ["Start Tournament","Change Settings"]
            selected_option = self.option_selector(message,"Invalid Option", options)
            
            if options[selected_option] == "Start Tournament":
                self._config.start_tournament() # Todo: Who starts the tournament?
            elif options[selected_option] == "Change Settings":
                self.select_configuration()
            

    def _clear_console(self) -> None:
        system("cls||clear")
    def option_selector(self,initial_prompt,error_message:str,options:list[str],) -> int:
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
        # Clear the console
        self._clear_console()

        selected_option = -1

        # While option is not set, ask for input
        while selected_option < 0:
            # Variables for handle errors
            exist_error = False
            error_input = ""
            
            
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
                selected_option = int(input_result)

        return selected_option
