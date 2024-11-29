# SPDX-License-Identifier: MIT

# Obtém faixas/artistas mais populares do usuário autenticado
# https://developer.spotify.com/documentation/web-api/reference/get-users-top-artists-and-tracks

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from spotipy.oauth2 import SpotifyOAuth

# Configure as credenciais
client_id = '066e8b7fdb554727b6cd9bc2b10551a5'
client_secret = '3b08c73a70714e35a414fcfe3699b53f'
scope = "user-top-read"
redirect_uri = "https://example.com/callback"

# Autenticação
client_credentials_manager = SpotifyClientCredentials(client_id=client_id, client_secret=client_secret)
sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager, auth_manager=SpotifyOAuth(scope=scope, client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri))

# Defina o número total de faixas que deseja coletar
total_tracks = 500
limit = 50  # O máximo que o Spotify permite por solicitação

offset = 0
tracks = []

while len(tracks) < total_tracks:
    # Faça a solicitação para obter as próximas faixas
    response = sp.current_user_top_tracks(limit=limit, offset=offset, time_range='short_term')
    
    # Adicione as faixas à lista de faixas
    tracks.extend(response['items'])
    
    # Atualize o offset para a próxima página de resultados
    offset += limit
    
    # Verifique se todos as faixas solicitadas já foram coletadas
    if len(response['items']) < limit:
        break

# Itere sobre as faixas e faça o que for necessário com os dados
for track in tracks:
    print("Nome da Música:", track['name'])
    print("Artista(s):", ", ".join([artist['name'] for artist in track['artists']]))
    print("Popularidade:", track['popularity'])
    print("")
