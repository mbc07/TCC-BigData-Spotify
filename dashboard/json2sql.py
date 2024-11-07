import argparse
import json
import os
import re
import sys

def load_json(path):
    result = []
    with open(path, 'r', encoding='utf8') as file:
        result = json.load(file)
    return result

def save_sql(data, path):
    with open(path, 'w', encoding='utf8') as file:
        for item in data:
            file.write(item + '\n')

def json_to_sql(data, table_name):
    sql_commands = []
    has_date_column = False

    if isinstance(data, list) and all(isinstance(item, dict) for item in data):
        columns = data[0].keys()
        
        if args.verbose:
            print("Processando {} colunas de {} itens...".format(len(columns), len(data)))

        for item in data:
            values = []
            for key, value in item.items():
                if value is None:
                    values.append("NULL")
                elif key == 'release_date':
                    has_date_column = True
                    values.append(f"normalize_date('{str(value).replace("'", "''")}')")
                else:
                    values.append(f"'{str(value).replace("'", "''")}'")
            
            sql = f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES ({', '.join(values)});"
            sql_commands.append(sql)
    
    if has_date_column:
        if args.verbose:
            print("Coluna de tipo DATE detectada, adicionando função normalize_date() no SQL...")
            
        sql_normalize_date = []
        sql_normalize_date.append("CREATE OR REPLACE FUNCTION normalize_date(partial_date TEXT)")
        sql_normalize_date.append("RETURNS DATE AS $$")
        sql_normalize_date.append("BEGIN")
        sql_normalize_date.append("    IF LENGTH(partial_date) = 7 THEN")
        sql_normalize_date.append("        RETURN TO_DATE(partial_date || '-01', 'YYYY-MM-DD');")
        sql_normalize_date.append("    ELSIF LENGTH(partial_date) = 4 THEN")
        sql_normalize_date.append("        RETURN TO_DATE(partial_date || '-01-01', 'YYYY-MM-DD');")
        sql_normalize_date.append("    ELSE")
        sql_normalize_date.append("        RETURN TO_DATE(partial_date, 'YYYY-MM-DD');")
        sql_normalize_date.append("    END IF;")
        sql_normalize_date.append("END;")
        sql_normalize_date.append("$$ LANGUAGE plpgsql;")
        sql_normalize_date.append("")
        
        sql_normalize_date.extend(sql_commands)
        return sql_normalize_date
        
    else:
        return sql_commands


#==================================================================================================
#----------------------------------- PROGRAMA PRINCIPAL (MAIN) ------------------------------------

parser = argparse.ArgumentParser(allow_abbrev=False, description='Json2Sql [v1.1]', epilog='Converte dados de arquivos JSON em comandos SQL')

parser.add_argument('-i', '--in-dir', metavar=('DIR'), default='.', help='local contendo o(s) arquivo(s) a serem processados (padrão: pasta atual)')
parser.add_argument('-o', '--out-dir', metavar=('DIR'), default='.', help='local onde o(s) arquivo(s) gerado(s) serão salvos (padrão: pasta atual)')
parser.add_argument('-p', '--parse-jsons', nargs='+', metavar=('FILE'), help='obtém todas as faixas contidas na(s) playlist(s) listada(s) no(s) arquivo(s) especificado(s)')
parser.add_argument('-v', '--verbose', default=False, action='store_true', help='mostra mensagens de status e depuração durante a execução das conversões')

args = parser.parse_args()

# Normaliza caminhos de pasta passados pela linha de comando
args.in_dir = os.path.abspath(args.in_dir)
args.out_dir = os.path.abspath(args.out_dir)

if args.parse_jsons:
    for file in args.parse_jsons:
        source = load_json(os.path.join(args.in_dir, file))
        table_name = re.sub('\\.[jJ][sS][oO][nN]$', '', os.path.basename(file))
        sql_commands = json_to_sql(source, table_name)
        save_sql(sql_commands, os.path.join(args.out_dir, '{}.sql'.format(table_name)))
        print('{} convertido para {} com sucesso'.format(os.path.basename(file), '{}.sql'.format(table_name)))

else:
    parser.print_help()
    sys.exit(1)
