import random
import json
import os
from src.tile_manager import TileManager

class EncounterGenerator:
    def __init__(self, tile_manager, local_ai=False, model="mistral", setting="ravenloft", debug=False):
        self.tiles = tile_manager
        self.local_ai = local_ai
        self.model = model
        self.setting = setting
        self.debug = debug

    def generate(self, tile_name, players, level, skull=False):
        tile = self.tiles.get_tile(tile_name)
        if tile["type"] == "generic" and random.random() > tile.get("event_chance", 0.5):
            return f"No encounter in {tile_name}, just eerie silence."

        themes = tile.get("themes", ["dark"])

        try:
            creatures_file = f"data/settings/{self.setting}/creatures.json"
            themes_file = f"data/settings/{self.setting}/themes.json"
            if self.debug:
                print(f"Loading creatures from: {creatures_file}")
                print(f"Loading themes from: {themes_file}")
            with open(creatures_file, "r") as f:
                creatures = json.load(f)
            if self.debug:
                print(f"Successfully loaded creatures from: {creatures_file}")
            with open(themes_file, "r") as f:
                theme_map = json.load(f)
            if self.debug:
                print(f"Successfully loaded themes from: {themes_file}")
            xp_budget = self._get_xp_budget(players, level, skull)
            max_cr = max(1, level + 1)
            min_cr = max(1, level // 2)  # Minimum CR for challenge
            valid_creatures = [c for c in creatures if min_cr <= float(c["cr"].replace("/", ".")) <= max_cr]
            if not valid_creatures:
                valid_creatures = [c for c in creatures if float(c["cr"].replace("/", ".")) <= max_cr]
            selected = self._select_monsters(valid_creatures, xp_budget, themes, theme_map, skull, tile["type"])
            encounter_text = "\n".join(f"- {c['name']} (CR {c['cr']}, {c['xp']} XP)" for c in selected)
            total_xp = sum(int(c['xp']) for c in selected)
        except Exception as e:
            print(f"Creature data failed: {e}. Using fallback.")
            return self._fallback_encounter(tile_name, players, level, tile)

        if self.local_ai:
            try:
                from src.ai_description import AIDescription
                ai = AIDescription(model=self.model)
                creature_names = [c['name'] for c in selected]
                description = ai.generate_description(tile_name, themes, creature_names)
                return (f"Encounter in {tile_name} ({tile['type']}): {players} level-{level} PCs.\n"
                        f"{encounter_text}\nTotal XP: {total_xp}\n\nDescription:\n{description}")
            except Exception as e:
                print(f"AI description failed: {e}. Skipping description.")
                return (f"Encounter in {tile_name} ({tile['type']}): {players} level-{level} PCs.\n"
                        f"{encounter_text}\nTotal XP: {total_xp}")

        return (f"Encounter in {tile_name} ({tile['type']}): {players} level-{level} PCs.\n"
                f"{encounter_text}\nTotal XP: {total_xp}")

    def _get_xp_budget(self, players, level, skull):
        # DMG XP thresholds for a "Medium" encounter per player
        xp_per_player = {
            1: 25, 2: 50, 3: 75, 4: 125, 5: 250, 6: 300, 7: 350, 8: 450,
            9: 550, 10: 600, 11: 800, 12: 1000, 13: 1100, 14: 1250, 15: 1400,
            16: 1600, 17: 2000, 18: 2100, 19: 2400, 20: 2800
        }
        medium_xp = xp_per_player.get(level, 250) * players
        # Medium-to-Hard (1.5x) without skull, Hard-to-Deadly (2.0x) with skull
        multiplier = 2.0 if skull else 1.5
        return int(medium_xp * multiplier)

    def _select_monsters(self, creatures, xp_budget, themes, theme_map, skull, tile_type):
        selected = []
        current_xp = 0
        max_attempts = 15
        attempts = 0
        # Target 90-100% of XP budget
        min_xp_target = int(xp_budget * 0.9)
        max_xp_target = int(xp_budget * 1.0)
        # Prefer 2-3 monsters, fallback to 1 if budget is tight
        target_count = random.randint(2, 3) if xp_budget >= 1000 else 1
        target_count = random.randint(2, 3) if skull else target_count

        # Shuffle creatures for variety
        random.shuffle(creatures)

        while current_xp < min_xp_target and attempts < max_attempts and len(selected) < target_count:
            remaining_xp = max_xp_target - current_xp
            # For generic tiles, prioritize variety over strict theme matching
            valid = creatures if tile_type == "generic" else []
            if tile_type != "generic":
                # Prefer thematic creatures for non-generic tiles
                thematic_creatures = []
                for creature in creatures:
                    for theme in themes:
                        if creature["name"] in theme_map.get(theme, []):
                            thematic_creatures.append(creature)
                            break
                valid = [c for c in thematic_creatures if int(c['xp']) <= remaining_xp]
                if not valid:
                    valid = [c for c in creatures if int(c['xp']) <= remaining_xp]
            else:
                valid = [c for c in creatures if int(c['xp']) <= remaining_xp]

            if not valid:
                break
            # Sort by XP to prefer monsters that fill the budget
            valid.sort(key=lambda x: int(x['xp']), reverse=True)
            # Pick a monster that keeps us within max_xp_target
            valid = [c for c in valid if current_xp + int(c['xp']) <= max_xp_target]
            if not valid:
                break
            monster = random.choice(valid)
            selected.append(monster)
            current_xp += int(monster['xp'])
            attempts += 1

        if not selected:  # Ensure at least one monster
            valid = [c for c in creatures if int(c['xp']) <= xp_budget]
            selected.append(random.choice(valid))

        return selected[:3]  # Cap at 3 monsters

    def _fallback_encounter(self, tile_name, players, level, tile):
        creatures_file = f"data/settings/{self.setting}/creatures.json"
        if self.debug:
            print(f"Loading creatures for fallback from: {creatures_file}")
        try:
            with open(creatures_file, "r") as f:
                creatures = json.load(f)
            if self.debug:
                print(f"Successfully loaded creatures from: {creatures_file}")
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
