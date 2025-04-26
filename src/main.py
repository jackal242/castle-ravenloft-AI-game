import argparse
import sys
from src.encounter_generator import EncounterGenerator
from src.tile_manager import TileManager

def main():
    parser = argparse.ArgumentParser(description="Castle Ravenloft Encounter Generator")
    parser.add_argument("--local-ai", action="store_true", help="Use local Ollama server for descriptions")
    parser.add_argument("--model", type=str, default="mistral", help="Ollama model to use with --local-ai (e.g., mistral, phi3)")
    parser.add_argument("--numplayers", type=int, default=4, help="Number of players")
    parser.add_argument("--level", type=int, default=5, help="Player level")
    parser.add_argument("--setting", type=str, default="ravenloft", help="Game setting (e.g., ravenloft, generic)")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging for file loading")
    args = parser.parse_args()

    try:
        tiles = TileManager(setting=args.setting, debug=args.debug)
        generator = EncounterGenerator(tile_manager=tiles, local_ai=args.local_ai, model=args.model, setting=tiles.setting, debug=args.debug)
    except Exception as e:
        print(f"Failed to initialize EncounterGenerator: {e}")
        sys.exit(1)

    mode = 'Local AI' if generator.local_ai else 'Data File'
    print(f"Castle Ravenloft Encounter Generator (Mode: {mode}, "
          f"{args.numplayers} players, level {args.level}, setting: {args.setting})")

    while True:
        available_tiles = tiles.get_available_tiles()
        print(f"Available tiles: {', '.join(available_tiles)} (add +skull for harder encounter)")
        tile_input = input("Enter tile (or 'quit'): ").strip()
        if tile_input.lower() == 'quit':
            break
        if tile_input == '?':
            continue  # Re-print available tiles on next loop
        # Parse +skull modifier
        skull = False
        if "+skull" in tile_input.lower():
            skull = True
            tile_input = tile_input.lower().replace("+skull", "").strip()
        tile_name = tiles.resolve_tile_name(tile_input)
        if tile_name is None:
            print("Invalid tile or ambiguous input. Please choose from the available tiles.")
            continue
        encounter = generator.generate(tile_name, args.numplayers, args.level, skull)
        print(encounter)
        print()

if __name__ == "__main__":
    main()
