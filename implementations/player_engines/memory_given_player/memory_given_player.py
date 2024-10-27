from enum import Enum
import random
from game.game_state import GameState
from src.player.player_engine import PlayerEngine
from src.game.action import Action
from src.game.game import GameEndCondition

class ActionResult(Enum):
    Victory = 0
    Defeat = 1
    Draw = 2

class ActionRecord:
    def __init__(self) -> None:
        self._victories = 0
        self._defeats = 0
        self._draws = 0
        self._total = 0

    @property
    def victories(self) -> int:
        return self._victories

    @victories.setter
    def victories(self, value: int) -> None:
        self.update_total(self._victories,value)
        self._victories = value

    @property
    def defeats(self) -> int:
        return self._defeats

    @defeats.setter
    def defeats(self, value: int) -> None:
        self.update_total(self._defeats,value)
        self._defeats = value
    @property
    def draws(self) -> int:
        return self._draws

    @draws.setter
    def draws(self, value: int) -> None:
        self.update_total(self._draws,value)
        self._draws = value

    @property
    def total(self) -> int:
        return self._total

    def update_total(self,old,value):
        self._total -=old
        self._total +=value

    def victory_rate(self) -> float:
        return self._victories / self._total
    
    def defeat_rate(self) -> float:
        return self._defeats / self._total
    
    def draw_rate(self) -> float:
        return self._draws / self._total
    
    def get_sorted_rates(self) -> list[tuple[ActionResult,float]]:
        return [
            (ActionResult.Victory, self.victory_rate()),
            (ActionResult.Draw, self.draw_rate()),
            (ActionResult.Defeat, self.defeat_rate())
        ].sort(key=lambda x: x[1], reverse=True)

class MemoryGivenPlayer(PlayerEngine):
    def __init__(self, engine_name: str):
        self._engine_name = engine_name
        self.historial: dict[Action, ActionRecord] = {}
    
    def memo_action(self, action):
        if action not in self.historial:
            self.historial[action] = ActionRecord()
    
    # Todo: Es necesario que el game state tenga winner
    # Todo: Es necesario un método para todos los jugadores que sea para que se corra al finalizar el juego
    def update_end_game_result(self, game_state: GameState):
        if game_state.winner == self:
            self.historial[game_state.previous_action].victories += 1
        elif game_state.winner == None:
            self.historial[game_state.previous_action].draws += 1
        else:
            self.historial[game_state.previous_action].defeats += 1
    
    def get_next_action(self, game_state: GameState) -> Action:
        
        current_possibles_actions = game_state.get_all_moves()
        auxiliar_current_posibles_actions = [action for action in current_possibles_actions]
            
        # Get a list with the best actions to perform
        
        actions_to_perform:list[tuple[Action,float]] = []
        
        for action in self.historial:
            # Check if the action has reals rates
            if self.historial[action].total == 0:
                continue
            
            action_rates = self.historial[action].get_sorted_rates()
            
            # If the hight result is victory, take that
            if action_rates[0][0] == ActionResult.Victory:
                actions_to_perform.append((action, action_rates[0][1]))
            # If the hight result is draw, check if the second best is victory
            elif action_rates[0][0] == ActionResult.Draw and action_rates[1][0] == ActionResult.Victory:
                actions_to_perform.append((action,action_rates[1][1]))
            else:
                current_possibles_actions.remove(action)
                
        if actions_to_perform:
            action = max(actions_to_perform, key=lambda x: x[1])[0]
        elif current_possibles_actions:
            action = random.choice(current_possibles_actions)
        else:
            action = random.choice(auxiliar_current_posibles_actions)


        self.memo_action(action)
        return action