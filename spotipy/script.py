import json
import pandas as pd
import hashlib
import os

def save_dataframes_to_json(dataframes, output_dir):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for df_name, df in dataframes.items():
        file_path = os.path.join(output_dir, f'{df_name}.json')
        with open(file_path, 'w') as file:
            file.write(df.to_json(orient='records', lines=False))

def get_prefix(file_name):
    if file_name.startswith("album_tracks_playlist_"):
        return "album_tracks_playlist"
    elif file_name.startswith("albums_playlist_"):
        return "album_playlist"
    elif file_name.startswith("features_album_tracks_playlist_"):
        return "features_album_tracks_playlist"
    elif file_name.startswith("features_playlist_"):
        return "features_playlist"
    elif file_name.startswith("playlist_"):
        return "playlist"
    else:
        return None

def generate_id(value):
    return hashlib.md5(str(value).encode()).hexdigest()

def data_from_json(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    
    # Remover campo 'crawler_retrieved_album_ids' se existir
    for item in data:
        if item is not None:
            item.pop('crawler_retrieved_album_ids', None)
    
    return data

def extract_data(data, parent_key=''):
    strings = {}
    lists_dicts = {}

    if isinstance(data, dict):
        for key, value in data.items():
            new_key = f"{parent_key}.{key}" if parent_key else key
            if isinstance(value, (str, int, float, bool, type(None))):
                strings[new_key] = value
            elif isinstance(value, (list, dict)):
                lists_dicts[new_key] = value

    return strings, lists_dicts

def process_lists_dicts(lists_dicts, prefix=''):
    dataframes = {}
    references = {}

    for key, value in lists_dicts.items():
        full_key = f"{prefix}.{key}" if prefix else key

        if isinstance(value, list):
            if all(isinstance(item, dict) for item in value):
                df_list = []
                ids_list = []
                for item in value:
                    item_id = item.get('id', generate_id(item))
                    ids_list.append(item_id)

                    strings, sub_lists_dicts = extract_data(item)
                    strings['id'] = item_id
                    df_list.append(strings)

                    if sub_lists_dicts:
                        sub_dfs, sub_refs = process_lists_dicts(sub_lists_dicts, full_key)
                        dataframes.update(sub_dfs)
                        references.update(sub_refs)

                if df_list:
                    dataframes[full_key] = pd.DataFrame(df_list)
                references[full_key] = ids_list
            else:
                item_id = generate_id(value)
                df_list = [{key: value, 'id': item_id}]

                if df_list:
                    dataframes[full_key] = pd.DataFrame(df_list)
                references[full_key] = item_id

        elif isinstance(value, dict):
            item_id = value.get('id', generate_id(value))

            strings, sub_lists_dicts = extract_data(value)
            strings['id'] = item_id
            dataframes[full_key] = pd.DataFrame([strings])

            if sub_lists_dicts:
                sub_dfs, sub_refs = process_lists_dicts(sub_lists_dicts, full_key)
                dataframes.update(sub_dfs)
                references.update(sub_refs)
            references[full_key] = item_id
    
    return dataframes, references

def unpack_response(directory_path):
    all_files_data = {}
    dataframes = {}
    child_dfs = {}

    # Iterar sobre todos os arquivos JSON no diretório
    for file_name in os.listdir(directory_path):
        if file_name != 'playlists.json':
            prefix = get_prefix(file_name)
            if prefix:
                file_path = os.path.join(directory_path, file_name)
                data = data_from_json(file_path=file_path)

                if prefix in ['album_tracks_playlist', 'playlist']:
                    genre = file_name.split('_')[-1].replace('.json', '')
                    for item in data:
                        if item is not None:
                            item['genre'] = genre

                if prefix not in all_files_data:
                    all_files_data[prefix] = []
                all_files_data[prefix].extend(data)

    for prefix, data_list in all_files_data.items():
        main_df_list = []
        for file_data in data_list:
            strings, lists_dicts = extract_data(file_data)
            sub_dfs, references = process_lists_dicts(lists_dicts)

            # Substituir listas e dicionários por IDs correspondentes
            for key, ids in references.items():
                key_name = key.split('.')[-1]
                if isinstance(ids, list):
                    strings[f'{key_name}_ids'] = ids
                else:
                    strings[f'{key_name}_id'] = ids

            main_df_list.append(strings)

            # Mesclar DataFrames filhos
            for key, df in sub_dfs.items():
                df_name = f"{prefix}_{key.split('.')[-1]}"
                if df_name in child_dfs:
                    child_dfs[df_name] = pd.concat([child_dfs[df_name], df], ignore_index=True)
                else:
                    child_dfs[df_name] = df

        # Criar DataFrame principal para o prefixo atual
        main_df = pd.DataFrame(main_df_list)
        dataframes[f'df_{prefix}'] = main_df

        for df_name, df in dataframes.items():
            df.dropna(subset=['id'], inplace=True)
            df.drop_duplicates(subset=['id'], inplace=True)

        for df_name, df in child_dfs.items():
            df.dropna(subset=['id'], inplace=True)
            df.drop_duplicates(subset=['id'], inplace=True)

    return dataframes, child_dfs

# MAIN

directory_path = 'playlist-features-sample'
main_dfs, child_dfs = unpack_response(directory_path=directory_path)

# Salvar DataFrames principais em 'output-main'
save_dataframes_to_json(main_dfs, output_dir='output-main-2')

# Salvar DataFrames filhos em 'output-child'
save_dataframes_to_json(child_dfs, output_dir='output-child-2')

print("DataFrames have been saved to JSON files.")
