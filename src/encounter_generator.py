import random
import json
from src.tile_manager import TileManager

class EncounterGenerator:
    def __init__(self, local_ai=False):
        self.tiles = TileManager()
        self.client = None
        self.local_ai = local_ai
        if local_ai:
            try:
                import httpx
                from ollama import Client
                print("Checking Ollama connection...")
                self.client = Client(host='http://localhost:11434', timeout=httpx.Timeout(30.0))
                self.client.generate(model='mistral', prompt='Ping', stream=False, options={'num_predict': 1})
                print("Ollama connected (using Mistral model).")
            except Exception as e:
                print(f"No Ollama server: {e}. Falling back to data mode.")
                self.local_ai = False

    def generate(self, tile_name, players, level):
        tile = self.tiles.get_tile(tile_name)
        if tile["type"] == "generic" and random.random() > tile.get("event_chance", 0.5):
            return f"No encounter in {tile_name}, just eerie silence."

        themes = ", ".join(tile.get("themes", ["dark"]))

        if not self.local_ai or not self.client:
            try:
                with open("data/creatures.json", "r") as f:
                    creatures = json.load(f)
                # Target XP budget based on DMG encounter guidelines
                xp_budget = self._get_xp_budget(players, level)
                max_cr = max(1, level + 1)
                valid_creatures = [c for c in creatures if float(c["cr"].replace("/", ".")) <= max_cr]
                if not valid_creatures:
                    valid_creatures = creatures
                selected = self._select_monsters(valid_creatures, xp_budget)
                encounter_text = "\n".join(f"- {c['name']} (CR {c['cr']}, {c['xp']} XP)" for c in selected)
                total_xp = sum(int(c['xp']) for c in selected)
                return (f"Encounter in {tile_name} ({tile['type']}): {players} level-{level} PCs.\n"
                        f"{encounter_text}\nTotal XP: {total_xp}")
            except Exception as e:
                print(f"Creature data failed: {e}. Using fallback.")
                return self._fallback_encounter(tile_name, players, level, tile)

        # Local AI mode
        prompt = (
            f"D&D 5e combat encounter for {players} level-{level} PCs in Castle Ravenloft's {tile_name}, "
            f"{themes} themes. List monsters from: Giant Spider, Dire Wolf, Swarm of Bats, Shadow Mastiff, Phase Spider, "
            f"Kobold, Goblin, Green Hag, Night Hag, Barovian Cultist, Grick, Cloaker, Mimic, Otyugh, Animated Armor, Gargoyle, "
            f"Rug of Smothering, Giant Centipede, Carrion Crawler, Stirge, Will-o'-Wisp, Skeleton, Ghast, Wight. "
            f"Include CR and XP (DMG: CR 1/8=25, CR 1/4=50, CR 1/2=100, CR 1=200, CR 2=450, CR 3=700, CR 4=1100). "
            f"Format as a list with each monster on a new line: '- <Monster> (CR <number>, <XP> XP)'. Max 3 monsters. "
            f"End with 'Total XP: <sum>'. 2014 rules. Max 50 words. No narrative, no external locations."
        )

        try:
            print("Generating encounter...", flush=True)
            encounter_text = ""
            for chunk in self.client.generate(model='mistral', prompt=prompt, stream=True, options={'num_predict': 100}):
                encounter_text += chunk['response']
            encounter_text = encounter_text.strip()
            print()  # Newline
            # Clean up and standardize format
            lines = encounter_text.split('\n')
            cleaned_lines = []
            total_xp = 0
            for line in lines:
                if line.strip().startswith('-') or 'Total XP:' in line:
                    cleaned_lines.append(line.strip())
                if 'Total XP:' in line:
                    try:
                        total_xp = int(re.search(r'Total XP:\s*(\d+)', line).group(1))
                    except:
                        total_xp = 0
            encounter_text = '\n'.join(cleaned_lines)
            if not any('Total XP:' in line for line in cleaned_lines):
                print("Warning: Invalid XP in response.")
                raise ValueError("Invalid XP")
            return (f"Encounter in {tile_name} ({tile['type']}): {players} level-{level} PCs.\n"
                    f"{encounter_text}")
        except Exception as e:
            print(f"Ollama failed: {e}. Using fallback.")
            return self._fallback_encounter(tile_name, players, level, tile)

    def _get_xp_budget(self, players, level):
        # DMG XP thresholds for a "Medium" encounter per player
        xp_per_player = {
            1: 25, 2: 50, 3: 75, 4: 125, 5: 250, 6: 300, 7: 350, 8: 450,
            9: 550, 10: 600, 11: 800, 12: 1000, 13: 1100, 14: 1250, 15: 1400
        }
        medium_xp = xp_per_player.get(level, 250) * players
        # Aim for Medium to Hard encounter (1.5x Medium XP)
        return int(medium_xp * 1.5)

    def _select_monsters(self, creatures, xp_budget):
        selected = []
        current_xp = 0
        max_attempts = 10
        attempts = 0
        while current_xp < xp_budget and attempts < max_attempts:
            remaining_xp = xp_budget - current_xp
            # Filter creatures that don't overshoot the budget too much
            valid = [c for c in creatures if int(c['xp']) <= remaining_xp * 1.2]
            if not valid:
                break
            monster = random.choice(valid)
            selected.append(monster)
            current_xp += int(monster['xp'])
            attempts += 1
        if not selected:  # Ensure at least one monster
            selected.append(random.choice(creatures))
        return selected[:3]  # Cap at 3 monsters

    def _fallback_encounter(self, tile_name, players, level, tile):
        try:
            with open("data/creatures.json", "r") as f:
                creatures = json.load(f)
            max_cr = max(1, level)
            valid_creatures = [c for c in creatures if float(c["cr"].replace("/", ".")) <= max_cr]
            if not valid_creatures:
                valid_creatures = creatures
            monster = random.choice(valid_creatures)
            return (f"Encounter in {tile_name} ({tile['type']}): {players} level-{level} PCs.\n"
                    f"- {monster['name']} (CR {monster['cr']}, {monster['xp']} XP)\n"
                    f"DC 12 Wisdom save avoids fear.\nReward: Potion of healing\nTotal XP: {monster['xp']}")
        except Exception:
            return (f"Encounter in {tile_name} ({tile['type']}): {players} level-{level} PCs.\n"
                    f"- Mimic (CR 2, 450 XP)\n"
                    f"DC 12 Wisdom save avoids fear.\nReward: Potion of healing\nTotal XP: 450")
