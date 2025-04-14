import socket
import httpx
from ollama import Client

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

            # Initialize client
            self.client = Client(host='http://localhost:11434', timeout=httpx.Timeout(200.0))

            # Verify model exists
            response = self.client.list()
            # print(f"DEBUG: Ollama list response: {response}")
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

    def generate_description(self, tile_name, themes, creature_names):
        if not self.client:
            raise RuntimeError("Ollama client not initialized")

        prompt = (
            f"Describe a D&D 5e encounter in Castle Ravenloft's {tile_name} with {', '.join(themes)} themes. "
            f"Include these monsters: {', '.join(creature_names)}. "
            f"Write one vivid paragraph (~50 words) describing the room and creatures as they appear. "
            f"Focus on atmosphere, senses, and monster behavior. Do not list CR, XP, or select monsters. "
            f"No external locations or narrative beyond the room. Use 2014 D&D tone."
        )

        try:
            print("Generating AI description...", flush=True)
            response = self.client.generate(model=self.model, prompt=prompt, stream=False, options={'num_predict': 100})
            description = response['response'].strip()
            print()  # Newline
            return description
        except Exception as e:
            raise RuntimeError(f"Ollama failed: {str(e)}")
