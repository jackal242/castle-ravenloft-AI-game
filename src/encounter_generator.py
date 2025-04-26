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
        self.creatures = []
        self.theme_map = {}

        # Load creatures and themes at initialization
        creatures_file = f"data/settings/{self.setting}/creatures.json"
        themes_file = f"data/settings/{self.setting}/themes.json"
        try:
            if self.debug:
                print(f"Loading creatures from: {creatures_file}")
            with open(creatures_file, "r") as f:
                self.creatures = json.load(f)
            if self.debug:
                print(f"Successfully loaded creatures from: {creatures_file}")
        except Exception as e:
            print(f"Failed to load creatures: {e}. Using empty creature list.")
            self.creatures = []

        try:
            if self.debug:
                print(f"Loading themes from: {themes_file}")
            with open(themes_file, "r") as f:
                self.theme_map = json.load(f)
            if self.debug:
                print(f"Successfully loaded themes from: {themes_file}")
        except Exception as e:
            print(f"Failed to load themes: {e}. Using empty theme map.")
            self.theme_map = {}

    def generate(self, tile_name, players, level, skull=False):
        tile = self.tiles.get_tile(tile_name)
        if tile["type"] == "generic" and random.random() > tile.get("event_chance", 0.5):
            return f"No encounter in {tile_name}, just eerie silence."

        themes = tile.get("themes", ["dark"])

        try:
            xp_budget = self._get_xp_budget(players, level, skull)
            max_cr = max(1, level + 2)  # Allow tougher creatures
            min_cr = max(1, level - 2)  # Exclude very weak creatures
            valid_creatures = [c for c in self.creatures if min_cr <= float(c["cr"].replace("/", ".")) <= max_cr]
            if not valid_creatures:
                valid_creatures = [c for c in self.creatures if float(c["cr"].replace("/", ".")) <= max_cr]
            selected = self._select_monsters(valid_creatures, xp_budget, themes, self.theme_map, skull, tile["type"])
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
            1: 50, 2: 100, 3: 150, 4: 250, 5: 500, 6: 600, 7: 750, 8: 900,
            9: 1100, 10: 1200, 11: 1600, 12: 2000, 13: 2200, 14: 2500, 15: 2800,
            16: 3200, 17: 3900, 18: 4200, 19: 5000, 20: 5700
        }
        medium_xp = xp_per_player.get(level, 500) * players
        # Adjust for desired difficulty: Medium-to-Hard without skull, Hard-to-Deadly with skull
        base_multiplier = 1.5 if skull else 1.0
        return int(medium_xp * base_multiplier)

    def _select_monsters(self, creatures, xp_budget, themes, theme_map, skull, tile_type):
        selected = []
        current_xp = 0
        max_attempts = 20
        attempts = 0
        # Target 80-120% of XP budget for flexibility
        min_xp_target = int(xp_budget * 0.8)
        max_xp_target = int(xp_budget * 1.2)
        # Aim for 2-4 monsters, more with skull
        target_count = random.randint(3, 5) if skull else random.randint(2, 4)

        # Sort creatures by XP descending to prefer stronger ones
        creatures.sort(key=lambda x: int(x['xp']), reverse=True)

        while current_xp < min_xp_target and attempts < max_attempts and len(selected) < target_count:
            remaining_xp = max_xp_target - current_xp
            # For generic tiles, allow all creatures; for named, prefer thematic
            valid = creatures if tile_type == "generic" else []
            if tile_type != "generic":
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
            # Prefer higher-XP creatures, but allow random selection for variety
            valid.sort(key=lambda x: int(x['xp']), reverse=True)
            # Allow slight overshooting
            valid = [c for c in valid if current_xp + int(c['xp']) <= max_xp_target]
            if not valid:
                break
            # Weight selection toward higher XP
            top_half = valid[:max(1, len(valid)//2)]
            monster = random.choice(top_half)
            selected.append(monster)
            current_xp += int(monster['xp'])
            attempts += 1

        if not selected:  # Ensure at least one monster
            valid = [c for c in creatures if int(c['xp']) <= xp_budget]
            selected.append(random.choice(valid))

        return selected[:5]  # Cap at 5 monsters

    def _fallback_encounter(self, tile_name, players, level, tile):
        max_cr = max(1, level)
        valid_creatures = [c for c in self.creatures if float(c["cr"].replace("/", ".")) <= max_cr]
        if not valid_creatures:
            valid_creatures = self.creatures
        if valid_creatures:
            monster = random.choice(valid_creatures)
            return (f"Encounter in {tile_name} ({tile['type']}): {players} level-{level} PCs.\n"
                    f"- {monster['name']} (CR {monster['cr']}, {monster['xp']} XP)\n"
                    f"DC 12 Wisdom save avoids fear.\nReward: Potion of healing\nTotal XP: {monster['xp']}")
        return (f"Encounter in {tile_name} ({tile['type']}): {players} level-{level} PCs.\n"
                f"- Mimic (CR 2, 450 XP)\n"
                f"DC 12 Wisdom save avoids fear.\nReward: Potion of healing\nTotal XP: 450")
