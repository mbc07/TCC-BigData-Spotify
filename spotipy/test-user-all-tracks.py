# Teste de estresse da API, obtém todas as faixas de cada álbum de cada artista seguido pelo usuário
# Dados obtidos são salvos em arquivos JSON, na pasta do script

import json
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

sent_requests = 0

# Obtém todos os artistas seguidos
artists = []
with open('artists.json', 'w') as fp:
    results = sp.current_user_followed_artists(limit=50)
    sent_requests += 1
    artists.extend(results['artists']['items'])

    while True:
        print("Obtendo artistas...")
        artists.extend(results['artists']['items'])
        json.dump(results['artists']['items'], fp)   # Salva resultado parcial
        if results['artists']['next']:
            if sent_requests > 200:
                sent_requests = 0
                print('Cooldown')
                time.sleep(30)

            results = sp.next(results['artists'])
            sent_requests += 1
        else:
            break
            
# Subtitui resultados parciais com resultados finais
with open('artists.json', 'w') as fp:
    json.dump(artists, fp)

# Obtém todos os álbuns
albums = []
with open('albums.json', 'w') as fp:
    for artist in artists:
        print("Obtendo álbuns...")
        results = sp.artist_albums(artist['id'], album_type='album', limit=50)
        sent_requests += 1
        while True:
            albums.extend(results['items'])
            json.dump(results['items'], fp)   # Salva resultado parcial
            if results['next']:
                if sent_requests > 200:
                    sent_requests = 0
                    print('Cooldown')
                    time.sleep(30)
                results = sp.next(results)
            else:
                break

# Subtitui resultados parciais com resultados finais
with open('albums.json', 'w') as fp:
    json.dump(albums, fp)

# Obtém todas as faixas dos álbuns
album_tracks = []
with open('album_tracks.json', 'w') as fp:
    for album in albums:
        print("Obtendo faixas dos álbuns...")
        results = sp.album_tracks(album['id'], limit=50)
        sent_requests += 1
        while True:
            album_tracks.extend(results['items'])
            json.dump(results['items'], fp)   # Salva resultado parcial
            if results['next']:
                if sent_requests > 200:
                    sent_requests = 0
                    print('Cooldown')
                    time.sleep(30)
                results = sp.next(results)
            else:
                break

# Subtitui resultados parciais com resultados finais
with open('album_tracks.json', 'w') as fp:
    json.dump(album_tracks, fp)

# Compila lista com ID das faixas
track_ids = []
for track in album_tracks:
    track_ids.append(track['id'])

# Obtém detalhes de todas as faixas
tracks = []
with open('tracks.json', 'w') as fp:
    for i in range(0, len(track_ids), 50):
        if sent_requests > 200:
            sent_requests = 0
            print('Cooldown')
            time.sleep(30)

        print("Obtendo detalhes das faixas...")
        results = sp.tracks(track_ids[i:i+50])
        sent_requests += 1
        tracks.extend(results['tracks'])
        json.dump(results['tracks'], fp)   # Salva resultado parcial

# Subtitui resultados parciais com resultados finais
with open('tracks.json', 'w') as fp:
    json.dump(tracks, fp)
