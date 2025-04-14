from ollama import Client
client = Client(host='http://localhost:11434')
prompt = 'D&D 5e encounter for 4 level-3 PCs in Crypt, undead themes. Max 50 words.'
for chunk in client.generate(model='mistral', prompt=prompt, stream=True):
    print(chunk['response'], end='', flush=True)
print()  # Newline
