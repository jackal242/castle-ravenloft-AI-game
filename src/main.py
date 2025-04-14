import sys
import argparse
from src.encounter_generator import EncounterGenerator
from src.tile_manager import TileManager

def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Castle Ravenloft Encounter Generator")
    parser.add_argument('--local_ai', action='store_true', help="Use local AI (Ollama)")
    parser.add_argument('--numplayers', type=int, default=4, help="Number of players (default: 4)")
    parser.add_argument('--level', type=int, default=3, help="Average player level (default: 3)")
    args = parser.parse_args()

    local_ai = args.local_ai
    players = args.numplayers
    level = args.level
    mode = "Local AI" if local_ai else "Data File"
    print(f"Castle Ravenloft Encounter Generator (Mode: {mode}, {players} players, level {level})")
    tiles = TileManager()
    generator = EncounterGenerator(local_ai=local_ai)
    tile_names = tiles.get_tile_names()
    print(f"Available tiles: {', '.join(tile_names)}")
    while True:
        tile = input("\nEnter tile (or 'quit'): ").strip()
        if tile.lower() == 'quit':
            break
        if not tile:  # Retry on empty input
            continue
        # Case-insensitive check
        if not any(tile.lower() == name.lower() for name in tile_names):
            print("Invalid tile.")
            continue
        print(generator.generate(tile, players, level))

if __name__ == "__main__":
    main()
