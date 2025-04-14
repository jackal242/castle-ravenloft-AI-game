from src.encounter_generator import EncounterGenerator

def main():
    try:
        generator = EncounterGenerator()
    except RuntimeError as e:
        print(f"Error: {e}")
        return
    print("Castle Ravenloft Encounter Generator")
    print("Available tiles: Chapel, Crypt, Corridor")
    while True:
        tile = input("\nEnter tile (or 'quit'): ").strip()
        if tile.lower() == 'quit':
            break
        players = input("Number of players (default 4): ").strip() or "4"
        level = input("Average level (default 3): ").strip() or "3"
        try:
            players = int(players)
            level = int(level)
            if players < 1 or level < 1:
                raise ValueError
            encounter = generator.generate(tile, players, level)
            print("\n" + encounter + "\n")
        except ValueError:
            print("Please enter valid numbers (1 or higher).")
        except KeyError:
            print(f"Unknown tile: {tile}. Try Chapel, Crypt, Corridor.")

if __name__ == "__main__":
    main()
