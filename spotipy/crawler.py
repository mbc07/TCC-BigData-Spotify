import argparse
import json
import os
import re
import spotipy
import sys

from requests.exceptions import ReadTimeout
from spotipy.cache_handler import CacheHandler
from spotipy.oauth2 import SpotifyOAuth


#==================================================================================================
#--------------------------------------- VARIÁVEIS GLOBAIS ----------------------------------------

# To Do: substituir variáveis globais por classes de objetos
# Controle de requisições
sent_requests = 0
max_requests = 100
requests_delay = 0
cooldown_delay = 30

# Controle de credenciais
clients = []
current_client = -1


#==================================================================================================
#--------------------------------------- CLASSES E FUNÇÕES ----------------------------------------

# Estende a classe de cache do Spotipy para trabalhar com o JSON de credenciais de acesso
class CustomCacheHandler(CacheHandler):
    def get_cached_token(self):
        try:
            return clients[current_client]['token'][0]
        except:
            return None

    def save_token_to_cache(self, token_info):
        try:
            clients[current_client]['token'][0] = token_info
        except:
            clients[current_client]['token'].append(token_info)
        save_json(clients, args.credentials)


# (Re)carrega credenciais a partir do JSON informado no parâmetro -c da linha de comando
def reload_credentials():
    global clients

    clients = load_json(args.credentials)
    if len(clients) == 0:
        raise RuntimeError('Falha ao carregar credenciais, verifique se o arquivo "{}" é válido.'.format(args.credentials))

    if args.verbose:
        print('{} credenciais de acesso carregadas'.format(len(clients)))

    reload_api()


# (Re)carrega instância do Spotipy. A nova instância utilizará o próximo cliente disponível na lista de credenciais atualmente carregadas
def reload_api():
    global sp
    global current_client

    if len(clients) == 0:
        reload_credentials()
    elif current_client >= len(clients)-1:
        current_client = 0
    else:
        current_client += 1

    client_id = clients[current_client]['client_id']
    client_secret = clients[current_client]['client_secret']
    redirect_uri = clients[current_client]['redirect_uri']
    scope = clients[current_client]['scope']
    cache_handler = CustomCacheHandler()

    auth_manager = SpotifyOAuth(client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri, scope=scope, cache_handler=cache_handler)
    sp = spotipy.Spotify(auth_manager=auth_manager)


# Verifica o número de requisições efetuadas e pausa temporariamente a execução, se necessário
def check_request_limits():
    global sent_requests
    global max_requests
    global cooldown_delay
    if sent_requests > max_requests:
        sent_requests = 0
        if args.verbose:
            print('CooldownMsgPlaceholder')
        time.sleep(cooldown_delay)
    sent_requests += 1


# Deserializa dados de um arquivo JSON para uma variável
def load_json(path):
    result = []
    with open(path, 'r', encoding='utf8') as file:
        result = json.load(file)
    return result


# Serializa dados de uma variável para um arquivo JSON
def save_json(data, path):
    with open(path, 'w', encoding='utf8') as file:
        json.dump(data, file)


# Obtém detalhes de todas as faixas da playlist especificada
def get_playlist(playlist_id):
    if not 'sp' in globals():
        reload_api()

    data = []

    while True:
        try:
            check_request_limits()
            playlist = sp.playlist(playlist_id)
            break;

        except ReadTimeout:
            if args.verbose:
                print('ReadTimeoutMsgPlaceholder')
                reload_api()
                # dump_partial?

    tracks = playlist['tracks']

    while tracks:
        for item in tracks['items']:
            data.append(item['track'])

        if tracks['next']:
            while True:
                try:
                    check_request_limits()
                    tracks = sp.next(tracks)
                    break;

                except ReadTimeout:
                    if args.verbose:
                        print('ReadTimeoutMsgPlaceholder')
                        reload_api()
                        # dump_partial?
        else:
            tracks = None

    return data

#==================================================================================================
#----------------------------------- PROGRAMA PRINCIPAL (MAIN) ------------------------------------

parser = argparse.ArgumentParser(allow_abbrev=False, description='SpotifyCrawler [v0.6]', epilog='Extrai dados utilizando a API do Spotify')

# To Do: quebrar em subparsers mais organizados
parser.add_argument('-i', '--in-dir', default='.', help='local contendo o(s) arquivo(s) a serem processados (padrão: pasta atual)')
parser.add_argument('-o', '--out-dir', default='.', help='local onde o(s) arquivo(s) gerado(s) serão salvos (padrão: pasta atual)')

parser.add_argument('-s', '--split-json', action='extend', nargs=2, metavar=('JSON', 'N'), help='divide o JSON informado em arquivos menores, contendo N entradas cada')
parser.add_argument('-m', '--merge-json', action='extend', nargs=2, metavar=('PRE', 'OUT'), help='mescla JSONs menores, com nomes de arquivo iniciados em PRE, em um JSON único especificado por OUT')

parser.add_argument('-p', '--get-playlists', metavar=('JSON'), help='obtém todas as faixas contidas nas playlists listadas no JSON de entrada')

parser.add_argument('-c', '--credentials', default='credentials.json', help='especifica o JSON com as credenciais de acesso (padrão: .\\credentials.json)')
parser.add_argument('-t', '--refresh-tokens', default=False, action='store_true', help='verifica se todos os tokens de acesso são válidos, reautenticando se necessário')

parser.add_argument('-v', '--verbose', default=False, action='store_true', help='mostra mensagens de status durante a execução das tarefas')

args = parser.parse_args()

# Normaliza caminhos de pasta passados pela linha de comando
args.in_dir = os.path.abspath(args.in_dir)
args.out_dir = os.path.abspath(args.out_dir)

# Processamento da opção --split-json (-s)
if args.split_json:
    data = load_json(os.path.join(args.in_dir, args.split_json[0]))
    size = int(args.split_json[1])
    part = 0

    for i in range(0, len(data), size):
        slice_name = '{}{:06d}.json'.format(re.sub('\\.[jJ][sS][oO][nN]', '', args.split_json[0]), part)
        save_json(data[i:i+size], os.path.join(args.out_dir, slice_name))
        part += 1

    if args.verbose:
        print('{} dividido em {} JSONs com {} ou menos elementos'.format(args.split_json[0], part, size))
    sys.exit()

# Processamento da opção --merge-json (-m)
if args.merge_json:
    data = []
    slices = 0

    for file in os.listdir(args.in_dir):
        if file.startswith(args.merge_json[0]):
            data.append(load_json(os.path.join(args.in_dir, file)))
            slices += 1

    if slices:
        save_json(data, os.path.join(args.out_dir, args.merge_json[1]))
    else:
        raise RuntimeError('Nenhum JSON com prefixo "{}" foi encontrado em "{}", verifique a sintaxe e tente novamente'.format(args.merge_json[0], args.in_dir))

    if args.verbose:
        print('{} elementos contidos em {} JSONs foram mesclados em {}'.format(len(data), slices, args.merge_json[1]))
    sys.exit()

# Processamento da opção --refresh-tokens (-t)
if args.refresh_tokens:
    reload_credentials()
    if args.verbose:
        print('Validando tokens de {} credenciais...'.format(len(clients)))

    for i in range(len(clients)):
        test = sp.current_user()
        reload_api()

# Processamento da opção --get-playlists (-p)
if args.get_playlists:
    source = load_json(args.get_playlists)
    data = []

    for playlist, id in source.items():
        if args.verbose:
            print('Obtendo faixas da playlist "{}"...'.format(playlist))
        data = get_playlist(id)

        save_json(data, os.path.join(args.out_dir, '{}.json'.format(playlist)))
        if args.verbose:
            print('{} faixas salvas em {}.json'.format(len(data), playlist))


