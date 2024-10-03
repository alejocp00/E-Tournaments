from enum import Enum
import os
import importlib
import inspect

PLAYER_ENGINES_PATH = os.path.join(os.getcwd(), "implementations", "player_engines")+"/"
TOURNAMENT_ENGINES_PATH = os.path.join(os.getcwd(), "implementations", "tournament_engines")+"/"
GAME_ENGINES_PATH = os.path.join(os.getcwd(), "implementations", "game_engines")+"/"

PLAYER_MODULE_PREFIX = "implementations.player_engines."
TOURNAMENT_ENGINES_PATH_PREFIX = "implementations.tournament_engines."
GAME_ENGINES_PATH_PREFIX = "implementations.game_engines."

class ImplementationsTypes(Enum):
    Tournament = 1
    Game = 2
    Player = 3

def get_all_implementations_of(selector: ImplementationsTypes) -> list:
    from src.tournaments.tournament_engine import TournamentEngine
    from src.player.player_engine import PlayerEngine
    from src.game.game import Game

    path = ""
    module_start = ""

    if selector == ImplementationsTypes.Tournament:
        path = TOURNAMENT_ENGINES_PATH
        module_start = TOURNAMENT_ENGINES_PATH_PREFIX
    if selector == ImplementationsTypes.Game:
        path = GAME_ENGINES_PATH
        module_start = GAME_ENGINES_PATH_PREFIX
    if selector == ImplementationsTypes.Player:
        path = PLAYER_ENGINES_PATH
        module_start = PLAYER_MODULE_PREFIX

    engines = []

    for folder in os.listdir(path):
        if folder == "__pycache__":
            continue

        for file in os.listdir(path + folder):
            if file == folder + ".py":
                module_end = folder+"." + folder
                module = importlib.import_module(module_start + module_end)

                classes = inspect.getmembers(module, inspect.isclass)

                for name, engine in classes:
                    if inspect.isclass(engine) and (
                        issubclass(engine, TournamentEngine)
                        or issubclass(engine, PlayerEngine or issubclass(engine, Game))
                    ) and engine != TournamentEngine and engine != PlayerEngine and engine != Game:
                        engines.append((name,engine))

    return engines
