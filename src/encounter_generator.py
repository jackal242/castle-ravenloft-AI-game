import random
import httpx
from ollama import Client
from src.tile_manager import TileManager

class EncounterGenerator:
    def __init__(self):
        self.tiles = TileManager()
        self.client = Client(host='http://localhost:11434', timeout=httpx.Timeout(10.0))
        try:
            print("Checking Ollama connection...")
            self.client.generate(model='gemma2:2b', prompt='Ping', stream=False, options={'num_predict': 1})
            print("Ollama connected.")
        except Exception as e:
            print(f"Warning: Ollama not connected: {e}. Using fallback mode.")

    def generate(self, tile_name, players, level):
        tile = self.tiles.get_tile(tile_name)
        if tile["type"] == "generic" and random.random() > tile.get("event_chance", 0.5):
            return f"No encounter in {tile_name}, just eerie silence."

        themes = ", ".join(tile.get("themes", ["dark"]))
        prompt = (
            f"D&D 5e encounter for {players} level-{level} PCs in Castle Ravenloft's {tile_name}, "
            f"{themes} themes. Combat with undead monsters only. List monsters, CR, XP (DMG: CR 1=200, CR 2=450, CR 3=700). "
            f"2014 rules. Max 50 words, end with 'Total XP: <number>'. No external locations."
        )

        try:
            print("Generating encounter...", flush=True)
            encounter_text = ""
            for chunk in self.client.generate(model='gemma2:2b', prompt=prompt, stream=True, options={'num_predict': 50}):
                print(chunk['response'], end='', flush=True)
                encounter_text += chunk['response']
            encounter_text = encounter_text.strip()
            print()  # Newline
            if "Total XP:" not in encounter_text:
                print("Warning: Invalid XP in response.")
                raise ValueError("Invalid XP")
            return (f"Encounter in {tile_name} ({tile['type']}): {players} level-{level} PCs.\n"
                    f"{encounter_text}")
        except Exception as e:
            print(f"\nWarning: Ollama failed: {e}. Using fallback.")
            return (f"Encounter in {tile_name} ({tile['type']}): {players} level-{level} PCs.\n"
                    f"Fight a Ghast (CR 2, 450 XP) in {tile_name}. DC 12 Wisdom save avoids fear.\n"
                    f"Reward: Potion of healing\nTotal XP: 450")
