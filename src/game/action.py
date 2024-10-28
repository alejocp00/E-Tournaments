class Action:
    def __init__(self, player_id: int, player_name: str, action: dict):
        self.player_id = player_id
        self.player_name = player_name
        self.action = action

    def __str__(self):
        text = f"Player {self.player_id} ({self.player_name}) performs: {self.action}"
        return text
    
    def __eq__(self, value: object) -> bool:
        if not isinstance(value,Action):
            return False
        
        for key in self.action:
            if not key in value.action:
                return False
            
            if not self.action[key] == value.action[key]:
                return False
            
        return True
    
    def __ne__(self, value: object) -> bool:
        return not self.__eq__(value)
        
    def __hash__(self) -> int:
        return hash(self.action.keys())