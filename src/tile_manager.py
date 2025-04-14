import json
import os

class TileManager:
    def __init__(self):
        self.tiles = []
        self.load_tiles()

    def load_tiles(self):
        try:
            with open("data/tiles.json", "r") as f:
                self.tiles = json.load(f)
        except FileNotFoundError:
            print("Tiles file not found, using defaults.")
            self.tiles = [
                {"name": "Chapel", "type": "named", "themes": ["undead"], "event_chance": 0.8},
                {"name": "Crypt", "type": "named", "themes": ["undead"], "event_chance": 0.8},
                {"name": "Corridor", "type": "generic", "themes": ["dark"], "event_chance": 0.5}
            ]

    def get_tile(self, tile_name):
        for tile in self.tiles:
            if tile["name"].lower() == tile_name.lower():
                return tile
        return {"name": tile_name, "type": "generic", "themes": ["dark"], "event_chance": 0.5}

    def get_available_tiles(self):
        return sorted([tile["name"] for tile in self.tiles])

    def resolve_tile_name(self, tile_input):
        tile_input = tile_input.lower()
        matches = [tile["name"] for tile in self.tiles if tile_input in tile["name"].lower()]
        if len(matches) == 1:
            return matches[0]
        return None  # No match or multiple matches
