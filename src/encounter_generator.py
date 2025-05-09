import random
import json
import os
from src.tile_manager import TileManager
from collections import Counter

class EncounterGenerator:
    def __init__(self, tile_manager, local_ai=False, model="gemma2:2b ", setting="ravenloft", debug=False):
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
            selected = self._select_monsters(self.creatures, xp_budget, themes, self.theme_map, skull, tile["type"])
            # Group and count creatures
            creature_counts = Counter((c['name'], c['cr'], c['xp']) for c in selected)
            # Sort by count (descending), then by name for ties
            sorted_counts = sorted(creature_counts.items(), key=lambda x: (-x[1], x[0][0]))
            encounter_text = "\n".join(f"{count} - {name} (CR {cr}, {xp} XP)" 
                                     for ((name, cr, xp), count) in sorted_counts)
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
        base_multiplier = 1.5 if skull else 1.0
        return int(medium_xp * base_multiplier)

    def _select_monsters(self, creatures, xp_budget, themes, theme_map, skull, tile_type):
        selected = []
        current_xp = 0
        max_attempts = 50
        min_xp_target = int(xp_budget * 0.8)  # e.g., 1600 for 2000 budget
        max_xp_target = int(xp_budget * 1.1)  # e.g., 2200 for 2000 budget
        max_monsters = 15
        attempts = 0
        selected_types = set()

        # Determine target number of unique creatures
        target_unique = random.choices(
            [1, 2, 3, 4, 5],
            weights=[0.50, 0.41, 0.05, 0.03, 0.01],
            k=1
        )[0]

        # Get thematic creatures
        thematic_names = set()
        for theme in themes:
            thematic_names.update(theme_map.get(theme, []))
        thematic_creatures = [c for c in creatures if c["name"] in thematic_names]
        if not thematic_creatures:
            thematic_creatures = creatures
            if self.debug:
                print(f"No thematic creatures for themes {themes}, falling back to all creatures.")

        if self.debug:
            print(f"Thematic creatures for {tile_type}: {[c['name'] for c in thematic_creatures]}")
            print(f"Target unique creatures: {target_unique}")

        # Handle different cases based on target_unique
        if target_unique <= 2:  # Single or pair of big creatures
            big_creatures = [c for c in thematic_creatures if int(c['xp']) >= 200]  # Lowered threshold
            if big_creatures:
                for _ in range(target_unique):
                    if current_xp >= min_xp_target or len(selected) >= max_monsters:
                        break
                    remaining_xp = max_xp_target - current_xp
                    valid = [c for c in big_creatures if int(c['xp']) <= remaining_xp and
                            (c['name'] in selected_types or len(selected_types) < target_unique)]
                    if not valid:
                        valid = [c for c in creatures if int(c['xp']) <= remaining_xp and
                                int(c['xp']) >= 200 and
                                (c['name'] in selected_types or len(selected_types) < target_unique)]
                        if not valid:
                            break
                    weights = [max(1, int(c['xp'])) for c in valid]  # Favor higher XP
                    monster = random.choices(valid, weights=weights, k=1)[0]
                    selected.append(monster)
                    selected_types.add(monster['name'])
                    current_xp += int(monster['xp'])
                    attempts += 1
                    if self.debug:
                        print(f"Selected {monster['name']} ({monster['xp']} XP), current total: {current_xp} XP")

        else:  # Group of 3, 4, or 5 creatures
            # Always start with a small group of creatures
            small_creatures = [c for c in thematic_creatures if int(c['xp']) <= 200]
            if small_creatures:
                group_size = min(random.randint(3, 6), max_monsters - len(selected))
                small_group = []
                for _ in range(group_size):
                    valid = [c for c in small_creatures if
                            (c['name'] in selected_types or len(selected_types) < target_unique)]
                    if not valid:
                        break
                    weights = [max(1, 1000 - int(c['xp'])) for c in valid]
                    monster = random.choices(valid, weights=weights, k=1)[0]
                    small_group.append(monster)
                    selected_types.add(monster['name'])
                selected.extend(small_group)
                current_xp += sum(int(c['xp']) for c in small_group)
                if self.debug:
                    print(f"Added group of small creatures: {[c['name'] for c in small_group]}, total XP: {current_xp}")

            # Continue adding to reach XP budget
            while current_xp < min_xp_target and len(selected) < max_monsters and attempts < max_attempts:
                remaining_xp = max_xp_target - current_xp
                valid = [c for c in thematic_creatures if int(c['xp']) <= remaining_xp and
                        (c['name'] in selected_types or len(selected_types) < target_unique)]
                if not valid:
                    if self.debug:
                        print(f"No valid thematic creatures with XP <= {remaining_xp}, switching to all creatures.")
                    valid = [c for c in creatures if int(c['xp']) <= remaining_xp and
                            (c['name'] in selected_types or len(selected_types) < target_unique)]
                    if not valid:
                        break
                weights = [max(1, 500 - int(c['xp']) / 2) for c in valid]  # Favor medium XP
                monster = random.choices(valid, weights=weights, k=1)[0]
                selected.append(monster)
                selected_types.add(monster['name'])
                current_xp += int(monster['xp'])
                attempts += 1
                if self.debug:
                    print(f"Selected {monster['name']} ({monster['xp']} XP), current total: {current_xp} XP")

        # Final check to ensure XP budget is met
        while current_xp < min_xp_target:
            remaining_xp = max_xp_target - current_xp
            valid = [c for c in thematic_creatures if int(c['xp']) <= remaining_xp and
                    (c['name'] in selected_types or len(selected_types) < target_unique)]
            if not valid:
                valid = [c for c in creatures if int(c['xp']) <= remaining_xp]
            if not valid:
                break
            weights = [max(1, int(c['xp'])) for c in valid]  # Favor high XP
            monster = random.choices(valid, weights=weights, k=1)[0]
            selected.append(monster)
            selected_types.add(monster['name'])
            current_xp += int(monster['xp'])
            if self.debug:
                print(f"Added final monster to meet XP: {monster['name']} ({monster['xp']} XP), total: {current_xp} XP")

        if not selected or current_xp < min_xp_target / 2:  # Ensure at least half the budget
            valid = [c for c in creatures if int(c['xp']) <= xp_budget and int(c['xp']) >= 200]
            if valid:
                monster = random.choice(valid)
                selected.append(monster)
                if self.debug:
                    print(f"Added fallback monster: {monster['name']} ({monster['xp']} XP)")

        return selected

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
