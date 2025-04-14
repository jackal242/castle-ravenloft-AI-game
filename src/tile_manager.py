import json

class TileManager:
    def __init__(self):
        try:
            with open("data/tiles.json") as f:
                self.tiles = json.load(f)
        except FileNotFoundError:
            self.tiles = [
                {"name": "Chapel", "type": "named", "themes": ["undead", "holy"]},
                {"name": "Crypt", "type": "named", "themes": ["undead", "dark"]},
                {"name": "Corridor", "type": "generic", "event_chance": 0.5}
            ]

    def get_tile(self, name):
        return next(t for t in self.tiles if t["name"].lower() == name.lower())
