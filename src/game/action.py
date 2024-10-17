class Action:
    def __init__(self, player_id: int, player_name: str, action: dict):
        self.player_id = player_id
        self.player_name = player_name
        self.action = action

    def __str__(self):
        text = f"Player {self.player_id} ({self.player_name}) performs: {self.action}"
        return text