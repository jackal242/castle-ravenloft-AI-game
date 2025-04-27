import socket
import httpx
from ollama import Client
from collections import Counter

class AIDescription:
    def __init__(self, model="gemma2"):
        self.client = None
        self.model = model
        self._connect()

    def _connect(self):
        try:
            # Check if server is reachable
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)
            result = sock.connect_ex(('localhost', 11434))
            sock.close()
            if result != 0:
                raise ConnectionError("Ollama server not running on localhost:11434")

            # Initialize client with reduced timeout
            self.client = Client(host='http://localhost:11434', timeout=httpx.Timeout(20.0))

            # Verify model exists
            response = self.client.list()
            available_models = []
            for model in response.get('models', []):
                name = getattr(model, 'model', '')
                base_name = name.split(':')[0] if ':' in name else name
                if base_name and base_name not in available_models:
                    available_models.append(base_name)
            if not available_models:
                raise ValueError("No models found in Ollama")
            if self.model not in available_models:
                raise ValueError(f"Model '{self.model}' not found. Available models: {', '.join(available_models)}")

            # Test connection
            self.client.generate(model=self.model, prompt='Ping', stream=False, options={'num_predict': 1})
            print(f"Ollama connected (using {self.model} model).")
        except Exception as e:
            print(f"Failed to connect to Ollama: {str(e)}")
            self.client = None

    def _format_description(self, text, line_length=80):
        """Insert newlines at the first space after line_length characters."""
        if not text:
            return text
        lines = []
        current_line = ""
        for word in text.split():
            if len(current_line) + len(word) + 1 > line_length and current_line:
                lines.append(current_line.strip())
                current_line = word
            else:
                current_line += (" " + word if current_line else word)
        if current_line:
            lines.append(current_line.strip())
        return "\n".join(lines)

    def _fallback_description(self, tile_name, themes, creature_names):
        """Generate a fallback description if AI fails."""
        # Count unique creatures for natural phrasing
        creature_counts = Counter(creature_names)
        creature_str_parts = []
        for creature, count in creature_counts.items():
            if count > 1:
                # Pluralize creature name (simple heuristic: add 's')
                creature_str_parts.append(f"{count} {creature}s")
            else:
                creature_str_parts.append(creature)
        creature_str = " and ".join(creature_str_parts) if len(creature_str_parts) > 1 else creature_str_parts[0] if creature_str_parts else "creatures"

        description = (
            f"The {tile_name} pulses with eerie energy. Shadows twist as {creature_str} "
            f"lurk, their eyes glinting with malice. The air thickens, heavy with menace, "
            f"as they creep forward, poised to strike in the dim, oppressive gloom."
        )
        # Ensure description is within 50 words
        description = " ".join(description.split()[:50])
        return self._format_description(description, line_length=80)

    def generate_description(self, tile_name, themes, creature_names, extra_instructions=None):
        if not self.client:
            return self._fallback_description(tile_name, themes, creature_names)

        prompt = (
            f"Describe a D&D 5e encounter in the {tile_name} with {', '.join(themes)} themes. "
            f"Include these monsters: {', '.join(creature_names)}. "
            f"Write one vivid paragraph of no more than 50 words describing the room and creatures as they appear. "
            f"Focus on atmosphere, senses, and monster behavior. Use present tense for an active, immersive narrative. "
            f"Do not list CR, XP, or select monsters. No external locations or narrative beyond the room. "
            f"Use 2014 D&D tone."
        )

        try:
            print("Generating AI description...", flush=True)
            response = self.client.generate(model=self.model, prompt=prompt, stream=False, options={'num_predict': 500})
            description = response['response'].strip()
            # Format description with line breaks
            formatted_description = self._format_description(description, line_length=80)
            print()  # Newline
            return formatted_description
        except Exception as e:
            print(f"AI description failed: {str(e)}. Using fallback description.")
            return self._fallback_description(tile_name, themes, creature_names)
