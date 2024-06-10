import json
import pandas as pd
import hashlib
import os

# Essa função gera uma hash hexadeciamel para value
def generate_id(value):
    return hashlib.md5(str(value).encode()).hexdigest()

# Essa função retorna os dados de um arquivo -- NÃO TRANSFORMA EM DATAFRAME MAIS AQUI
def json_to_dataframe(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
    
    # Remover campo 'crawler_retrieved_album_ids' se existir
    for item in data:
        if item is not None:
            item.pop('crawler_retrieved_album_ids', None)
    
    return data

# Esta função faz a divisão entre dados que são lista/dicionário com outros tipos de dados
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

# Esta função trata casos de listas e dicionários recursivamente, retornando os novos dataframes e os ids
def process_lists_dicts(lists_dicts, prefix=''):
    dataframes = {}
    references = {}

    for key, value in lists_dicts.items():
        full_key = f"{prefix}.{key}" if prefix else key

        if isinstance(value, list):
            df_list = []
            ids_list = []
            for item in value:
                item_id = generate_id(item)
                ids_list.append(item_id)
                if isinstance(item, dict):
                    strings, sub_lists_dicts = extract_data(item)
                    strings['ID'] = item_id
                    df_list.append(strings)
                    sub_dfs, sub_refs = process_lists_dicts(sub_lists_dicts, full_key)
                    dataframes.update(sub_dfs)
                    references.update(sub_refs)
                else:
                    df_list.append({full_key: item, 'ID': item_id})
            if df_list:
                dataframes[full_key] = pd.DataFrame(df_list)
            references[full_key] = ids_list

        elif isinstance(value, dict):
            item_id = generate_id(value)
            strings, sub_lists_dicts = extract_data(value)
            strings['ID'] = item_id
            dataframes[full_key] = pd.DataFrame([strings])
            sub_dfs, sub_refs = process_lists_dicts(sub_lists_dicts, full_key)
            dataframes.update(sub_dfs)
            references.update(sub_refs)
            references[full_key] = item_id
    
    return dataframes, references

def unpack_response(directory_path):
    all_files_data = []

    # Iterar sobre todos os arquivos JSON no diretório
    for file_name in os.listdir(directory_path):
        if file_name != 'playlists.json':
            file_path = os.path.join(directory_path, file_name)
            data = json_to_dataframe(file_path=file_path)
            all_files_data.extend(data)

    main_df_list = []
    child_dfs = {}
    for file_data in all_files_data: 
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
            df_name = f"df_{key.split('.')[-1]}"
            if df_name in child_dfs:
                child_dfs[df_name] = pd.concat([child_dfs[df_name], df], ignore_index=True)
            else:
                child_dfs[df_name] = df

    # Criando o DataFrame principal com as strings
    main_df = pd.DataFrame(main_df_list)

    # Definindo DataFrames como variáveis globais
    globals().update(child_dfs)

    return main_df, child_dfs

# MAIN

directory_path = 'playlist-features-sample'
main_df, child_dfs = unpack_response(directory_path=directory_path)

# Exibindo DataFrames gerados
print("Main DataFrame:")
print(main_df, end="\n\n")

for df_name, df in child_dfs.items():
    print(f"DataFrame {df_name}:")
    print(df, end="\n\n")

print(main_df.columns)
