import json
import os

class TileManager:
    def __init__(self):
        self.tiles = self.load_tiles()

    def load_tiles(self):
        try:
            with open("data/tiles.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return [
                {"name": "Chapel", "type": "named", "themes": ["undead"], "event_chance": 0.8},
                {"name": "Crypt", "type": "named", "themes": ["undead"], "event_chance": 0.8},
                {"name": "Corridor", "type": "generic", "themes": ["dark"], "event_chance": 0.5}
            ]

    def get_tile(self, name):
        for tile in self.tiles:
            if tile["name"].lower() == name.lower():
                return tile
        return {"name": name, "type": "generic", "themes": ["dark"], "event_chance": 0.5}

    def get_tile_names(self):
        return [tile["name"] for tile in self.tiles]
