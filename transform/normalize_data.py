import os
import pandas as pd
import json

# Diretório onde estão localizados os arquivos JSON
directory_path = 'output-merge-files/'

# Diretório de saída para os DataFrames normalizados
output_directory = 'output-normalized-data/'

# Cria o diretório de saída se não existir
if not os.path.exists(output_directory):
    os.makedirs(output_directory)

# Itera sobre os arquivos no diretório especificado
for file_name in os.listdir(directory_path):
    file_path = os.path.join(directory_path, file_name)
    data = pd.read_json(file_path)
   
    if file_name.startswith("df_album"):
        df_album = pd.DataFrame(data)
    elif file_name.startswith("df_artists"):
        df_artists = pd.DataFrame(data)
    elif file_name.startswith("df_images"):
        df_images = pd.DataFrame(data)
    elif file_name.startswith("df_tracks_result"):
        df_tracks = pd.DataFrame(data)

# Expande as listas de IDs de artistas e imagens em múltiplas linhas
df_tracks = df_tracks.explode('artists_ids').explode('images_ids')

# Renomeia as colunas para associar corretamente os IDs
df_tracks = df_tracks.rename(columns={'artists_ids': 'artist_id', 'images_ids': 'image_id'})

# Remove linhas duplicadas em cada DataFrame
df_album = df_album.drop_duplicates()
df_artists = df_artists.drop_duplicates()
df_images = df_images.drop_duplicates()
df_tracks = df_tracks.drop_duplicates()

# Cria DataFrames para relacionar faixas com artistas e imagens
df_artist_track = df_tracks[['track_id', 'artist_id']].drop_duplicates().reset_index(drop=True)
df_image_track = df_tracks[['track_id', 'image_id']].drop_duplicates().reset_index(drop=True)

# Remove as colunas de id: artist_id e image_id
df_tracks = df_tracks.drop(columns=['artist_id', 'image_id'])

# Remove linhas duplicadas em df_tracks
df_tracks = df_tracks.drop_duplicates()

# Salva os DataFrames no diretório de saída
df_album.to_json(os.path.join(output_directory, 'df_album.json'), orient='records', lines=False)
df_artists.to_json(os.path.join(output_directory, 'df_artists.json'), orient='records', lines=False)
df_images.to_json(os.path.join(output_directory, 'df_images.json'), orient='records', lines=False)
df_tracks.to_json(os.path.join(output_directory, 'df_tracks.json'), orient='records', lines=False)
df_artist_track.to_json(os.path.join(output_directory, 'df_artist_track.json'), orient='records', lines=False)
df_image_track.to_json(os.path.join(output_directory, 'df_image_track.json'), orient='records', lines=False)

print("DataFrames normalizados salvos em arquivos JSON.")
