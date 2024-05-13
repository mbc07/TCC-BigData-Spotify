# Obtém atributos de todas as faixas de uma playlist
# Dados obtidos são salvos em arquivos JSON, na pasta do script

import json
import os.path
import spotipy
import time
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.oauth2 import SpotifyOAuth

# Configure as credenciais
client_id = '0dba842d359e48b9be6523154f3df372'
client_secret = '8032d41cbfa14674ac9d45ac0a823331'
scope = "playlist-read-private,playlist-read-collaborative,user-follow-read,user-top-read,user-read-recently-played,user-library-read"
redirect_uri = "https://example.com/callback"

# Autenticação
client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager, auth_manager=SpotifyOAuth(scope=scope, client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri))

sleep_interval = 0
max_requests = 100
sent_requests = 0

def cooldown():
    global sent_requests
    global max_requests
    if sent_requests > max_requests:
        sent_requests = 0
        print("z", end='', flush=True)
        time.sleep(30)

playlists = []

if os.path.isfile('playlists.json'):
    with open('playlists.json', 'r', encoding="utf8") as fp:
        playlists = json.load(fp)
    print("JSON playlists.json carregado")
else:
    sys.exit("Arquivo não encontrado: playlists.json")

for name, id in playlists.items():
    tracks = []
    features = []
    if os.path.isfile(f'{name}_tracks.json'):
        # Recarrega resultados anteriores, se disponíveis
        with open(f'{name}_tracks.json', 'r', encoding="utf8") as fp:
            tracks = json.load(fp)
        print(f'JSON {name}_tracks.json carregado')
    else:
        print(f'Obtendo faixas da playlist "{name}"', end='', flush=True)
        cooldown()
        results = sp.playlist(id)
        sent_requests += 1
        time.sleep(sleep_interval)
        tracks.extend(results['tracks']['items'])
                
        # Salva resultado final
        with open(f'{name}_tracks.json', 'w') as fp:
            json.dump(tracks, fp)
        print(" ")
        
        
    if os.path.isfile(f'{name}_features.json'):
        # Recarrega resultados anteriores, se disponíveis
        with open(f'{name}_features.json', 'r', encoding="utf8") as fp:
            features = json.load(fp)
        print(f'JSON {name}_features.json carregado')
    else:
        print(f'Obtendo atributos da playlist "{name}"', end='', flush=True)
        for track in tracks:
            print(".", end='', flush=True)
            cooldown()
            results = sp.audio_features(track['track']['id'])
            sent_requests += 1
            time.sleep(sleep_interval)
            features.extend(results)

        # Salva resultado final
        with open(f'{name}_features.json', 'w') as fp:
            json.dump(features, fp)
        print(" ")
