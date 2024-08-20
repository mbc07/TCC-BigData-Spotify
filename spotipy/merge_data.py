import os
import pandas as pd
import json

def process_files(config, additional_data=None):
    # Carrega o arquivo JSON e seleciona as colunas especificadas
    data = pd.read_json(config['input_file'])
    df = pd.DataFrame(data)
    df = df[config['select_columns']]
    
    # Renomeia colunas, se especificado na configuração
    if 'rename_columns' in config:
        df = df.rename(columns=config['rename_columns'])

    # Realiza junção com outro DataFrame, se necessário
    if 'join_config' in config:
        join_file = config['join_config']['input_file']
        join_columns = config['join_config']['select_columns']
        join_on = config['join_config']['on']
        
        join_data = pd.read_json(join_file)
        join_df = pd.DataFrame(join_data)
        
        # Verifica se colunas necessárias estão presentes no DataFrame de junção
        missing_columns = [col for col in join_columns if col not in join_df.columns]
        if missing_columns:
            raise KeyError(f"Colunas selecionadas ausentes no arquivo: {missing_columns}")
        
        join_df = join_df[join_columns]
        
        # Renomeia colunas do DataFrame de junção, se necessário
        if 'rename_join_columns' in config['join_config']:
            join_df = join_df.rename(columns=config['join_config']['rename_join_columns'])
        
        # Verifica se a coluna de junção existe no DataFrame principal
        if join_on not in df.columns:
            raise KeyError(f"Coluna para join on '{join_on}' não está no dataframe")
        
        # Exibe colunas disponíveis para debug
        print(f"Columns in main DataFrame: {df.columns.tolist()}")
        print(f"Columns in join DataFrame: {join_df.columns.tolist()}")
        
        # Realiza a junção
        df = pd.merge(df, join_df, on=join_on, how='left')
    
    return df

def concat_files(config_file):
    # Carrega configurações a partir de um arquivo JSON
    with open(config_file, 'r') as file:
        config_list = json.load(file)

    output_dfs = {}

    for config in config_list:
        df = process_files(config)
        output_file = config['output_file']

        output_dir = os.path.dirname(output_file)
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Acumula DataFrames para concatenação futura
        if output_file in output_dfs:
            output_dfs[output_file].append(df)
        else:
            output_dfs[output_file] = [df]

    for output_file, dfs in output_dfs.items():
        # Concatena DataFrames se houver mais de um
        if len(dfs) > 1:
            result_df = pd.concat(dfs, ignore_index=True)
        else:
            result_df = dfs[0]
        result_df.to_json(output_file, orient='records', lines=False)

concat_files('config.json')
print("Arquivos processados e salvos com sucesso.")

# Melhorando a parte final para usar uma função genérica de leitura e merge
def merge_dataframes(df_paths, on_column):
    dfs = [pd.read_json(path) for path in df_paths]
    merged_df = dfs[0]
    for df in dfs[1:]:
        merged_df = pd.merge(merged_df, df, on=on_column)
    return merged_df

# Lista de caminhos para os arquivos JSON e a coluna de junção
df_paths = ['output-merge-files/df_tracks.json', 'output-merge-files/df_tracks_features.json']
merged_df = merge_dataframes(df_paths, 'track_id')
merged_df.to_json('output-merge-files/df_tracks_result.json', orient='records', lines=False)
