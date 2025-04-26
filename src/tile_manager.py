import json
import os

class TileManager:
    def __init__(self, setting="ravenloft", debug=False):
        self.tiles = []
        self.setting = setting
        self.debug = debug
        self.load_tiles()

    def load_tiles(self):
        tile_file = f"data/settings/{self.setting}/tiles.json"
        if self.debug:
            print(f"Attempting to load tiles from: {tile_file}")
        if not os.path.exists(tile_file):
            if self.debug:
                print(f"Setting '{self.setting}' not found, falling back to ravenloft")
            tile_file = "data/settings/ravenloft/tiles.json"
        try:
            with open(tile_file, "r") as f:
                self.tiles = json.load(f)
            if self.debug:
                print(f"Successfully loaded tiles from: {tile_file}")
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
