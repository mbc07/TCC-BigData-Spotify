import argparse
import json
import os
import re
import spotipy
import sys
import time

from requests.exceptions import ReadTimeout
from spotipy.cache_handler import CacheHandler
from spotipy.oauth2 import SpotifyOAuth


#==================================================================================================
#--------------------------------------- VARIÁVEIS GLOBAIS ----------------------------------------

# To Do: substituir variáveis globais por classes de objetos
# Controle de requisições
sent_requests = 0
max_requests = 60
requests_delay = 0.5
cooldown_delay = 30.0

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

    if not 'sp' in globals():
        reload_api()


# (Re)carrega instância do Spotipy. A nova instância utilizará o próximo cliente disponível na lista de credenciais atualmente carregadas
def reload_api(failed=False):
    global sp
    global current_client

    if len(clients) == 0:
        reload_credentials()
    elif current_client >= len(clients)-1:
        if failed:
            reload_credentials()
        current_client = 0
    else:
        current_client += 1

    client_id = clients[current_client]['client_id']
    client_secret = clients[current_client]['client_secret']
    redirect_uri = clients[current_client]['redirect_uri']
    scope = clients[current_client]['scope']
    cache_handler = CustomCacheHandler()

    auth_manager = SpotifyOAuth(client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri, scope=scope, cache_handler=cache_handler)
    sp = spotipy.Spotify(auth_manager=auth_manager, retries=0, status_retries=0)


# Verifica o número de requisições efetuadas e pausa temporariamente a execução, se necessário
def check_request_limits():
    global sent_requests
    global max_requests
    global cooldown_delay
    global requests_delay

    if sent_requests > max_requests:
        sent_requests = 0
        print('Limite de requisições atingido, pausando execução por {:0.0f} segundos'.format(cooldown_delay))
        time.sleep(cooldown_delay)
    else:
        sent_requests += 1
        time.sleep(requests_delay)


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
    requested_ids = []

    if os.path.isfile(os.path.join(args.in_dir, 'playlist_{}_partial.json'.format(playlist_id))):
        if args.verbose:
            print('Resultados parciais encontrados, recarregando...')
        data = load_json(os.path.join(args.in_dir, 'playlist_{}_partial.json'.format(playlist_id)))
        requested_ids = data[0].pop('crawler_retrieved_track_ids', None)
    else:
        data.insert(0, {'crawler_retrieved_track_ids': requested_ids})

    try:
        while True:
            try:
                check_request_limits()
                playlist = sp.playlist(playlist_id)
                break

            except (ReadTimeout, spotipy.exceptions.SpotifyException):
                print('Falha ao acessar API do Spotify, recarregando instância [{}/{}]'.format(current_client+1, len(clients)))
                reload_api(failed=True)

        tracks = playlist['tracks']

        while tracks:
            for item in tracks['items']:
                if item['track']['id'] in requested_ids:
                    continue

                data.append(item['track'])
                requested_ids.append(item['track']['id'])

            if tracks['next']:
                while True:
                    try:
                        check_request_limits()
                        tracks = sp.next(tracks)
                        break

                    except (ReadTimeout, spotipy.exceptions.SpotifyException):
                        print('Falha ao acessar API do Spotify, recarregando instância [{}/{}]'.format(current_client+1, len(clients)))
                        reload_api(failed=True)

                        if args.verbose:
                            print('Salvando resultados parciais...')
                        data[0]['crawler_retrieved_track_ids'] = requested_ids
                        save_json(data, os.path.join(args.out_dir, 'playlist_{}_partial.json'.format(playlist_id)))
            else:
                tracks = None

    except KeyboardInterrupt:
        if args.verbose:
            print('Salvando resultados parciais...')
        data[0]['crawler_retrieved_track_ids'] = requested_ids
        save_json(data, os.path.join(args.out_dir, 'playlist_{}_partial.json'.format(playlist_id)))
        raise

    if os.path.isfile(os.path.join(args.in_dir, 'playlist_{}_partial.json'.format(playlist_id))):
        os.remove(os.path.join(args.in_dir, 'playlist_{}_partial.json'.format(playlist_id)))

    data[0]['crawler_retrieved_track_ids'] = requested_ids
    return data


# Obtém todas as faixas das IDs de álbum especificadas
def get_album_tracks(album_ids, set_name):
    if not 'sp' in globals():
        reload_api()

    data = []
    requested_ids = []

    if os.path.isfile(os.path.join(args.in_dir, 'album_tracks_{}_partial.json'.format(set_name))):
        if args.verbose:
            print('Resultados parciais encontrados, recarregando...')
        data = load_json(os.path.join(args.in_dir, 'album_tracks_{}_partial.json'.format(set_name)))
        requested_ids = data[0].pop('crawler_retrieved_album_ids', None)
    else:
        data.insert(0, {'crawler_retrieved_album_ids': requested_ids})

    try:
        for album_id in album_ids:
            if album_id in requested_ids:
                continue

            while True:
                try:
                    check_request_limits()
                    album = sp.album_tracks(album_id, limit=50)
                    break

                except (ReadTimeout, spotipy.exceptions.SpotifyException):
                    print('Falha ao acessar API do Spotify, recarregando instância [{}/{}]'.format(current_client+1, len(clients)))
                    reload_api(failed=True)

            tracks = album['items']

            while True:
                for track in tracks:
                    try:
                        if not any(element.get('id') == track['id'] for element in data):
                            track['crawler_album_id'] = album_id
                            data.append(track)
                    except TypeError:
                        # Workaround para possível bug no Spotipy (testado pela última vez na versão 2.23.0)
                        # Exceção ocorre em álbuns com mais de 50 faixas (ID de exemplo: 3myPwaMYjdwhtq0nFgeG6W)
                        album['next'] = tracks['next']
                        tracks = tracks['items']
                        for track in tracks:
                            if not any(element.get('id') == track['id'] for element in data):
                                track['crawler_album_id'] = album_id
                                data.append(track)
                        break

                if album['next']:
                    while True:
                        try:
                            check_request_limits()
                            tracks = sp.next(album)
                            break

                        except (ReadTimeout, spotipy.exceptions.SpotifyException):
                            print('Falha ao acessar API do Spotify, recarregando instância [{}/{}]'.format(current_client+1, len(clients)))
                            reload_api(failed=True)

                            if args.verbose:
                                print('Salvando resultados parciais...')
                            data[0]['crawler_retrieved_album_ids'] = requested_ids
                            save_json(data, os.path.join(args.out_dir, 'album_tracks_{}_partial.json'.format(set_name)))

                else:
                    break
            requested_ids.append(album_id)

    except KeyboardInterrupt:
        if args.verbose:
            print('Salvando resultados parciais...')
        data[0]['crawler_retrieved_album_ids'] = requested_ids
        save_json(data, os.path.join(args.out_dir, 'album_tracks_{}_partial.json'.format(set_name)))
        raise

    if os.path.isfile(os.path.join(args.in_dir, 'album_tracks_{}_partial.json'.format(set_name))):
        os.remove(os.path.join(args.in_dir, 'album_tracks_{}_partial.json'.format(set_name)))

    data[0]['crawler_retrieved_album_ids'] = requested_ids
    return data


# Obtém informações de álbum de todas as IDs especificadas
def get_albums(album_ids, set_name):
    if not 'sp' in globals():
        reload_api()

    data = []

    if os.path.isfile(os.path.join(args.in_dir, 'albums_{}_partial.json'.format(set_name))):
        if args.verbose:
            print('Resultados parciais encontrados, recarregando...')
        data = load_json(os.path.join(args.in_dir, 'albums_{}_partial.json'.format(set_name)))

        for item in data:
            if item['id'] in album_ids:
                album_ids.remove(item['id'])

    try:
        if len(album_ids) > 20:
            for i in range(0, len(album_ids), 20):
                while True:
                    try:
                        check_request_limits()
                        albums = sp.albums(album_ids[i:i+20])
                        for album in albums['albums']:
                            data.append(album)
                        break

                    except (ReadTimeout, spotipy.exceptions.SpotifyException):
                        print('Falha ao acessar API do Spotify, recarregando instância [{}/{}]'.format(current_client+1, len(clients)))
                        reload_api(failed=True)

                        if args.verbose:
                            print('Salvando resultados parciais...')
                        save_json(data, os.path.join(args.out_dir, 'albums_{}_partial.json'.format(set_name)))

        else:
            while True:
                try:
                    check_request_limits()
                    albums = sp.albums(album_ids)
                    for album in albums['albums']:
                        data.append(album)
                    break

                except (ReadTimeout, spotipy.exceptions.SpotifyException):
                    print('Falha ao acessar API do Spotify, recarregando instância [{}/{}]'.format(current_client+1, len(clients)))
                    reload_api(failed=True)

    except KeyboardInterrupt:
        if args.verbose:
            print('Salvando resultados parciais...')
        save_json(data, os.path.join(args.out_dir, 'albums_{}_partial.json'.format(set_name)))
        raise

    if os.path.isfile(os.path.join(args.in_dir, 'albums_{}_partial.json'.format(set_name))):
        os.remove(os.path.join(args.in_dir, 'albums_{}_partial.json'.format(set_name)))

    return data


# Obtém recursos de todas as IDs de faixa especificadas
def get_features(track_ids, set_name):
    if not 'sp' in globals():
        reload_api()

    data = []

    if os.path.isfile(os.path.join(args.in_dir, 'features_{}_partial.json'.format(set_name))):
        if args.verbose:
            print('Resultados parciais encontrados, recarregando...')
        data = load_json(os.path.join(args.in_dir, 'features_{}_partial.json'.format(set_name)))

        for item in data:
            if item['id'] in track_ids:
                track_ids.remove(item['id'])

    try:
        if len(track_ids) > 100:
            for i in range(0, len(track_ids), 100):
                while True:
                    try:
                        check_request_limits()
                        data.extend(sp.audio_features(track_ids[i:i+100]))
                        break

                    except (ReadTimeout, spotipy.exceptions.SpotifyException):
                        print('Falha ao acessar API do Spotify, recarregando instância [{}/{}]'.format(current_client+1, len(clients)))
                        reload_api(failed=True)

                        if args.verbose:
                            print('Salvando resultados parciais...')
                        save_json(data, os.path.join(args.out_dir, 'features_{}_partial.json'.format(set_name)))

        else:
            while True:
                try:
                    check_request_limits()
                    data.extend(sp.audio_features(track_ids))
                    break

                except (ReadTimeout, spotipy.exceptions.SpotifyException):
                    print('Falha ao acessar API do Spotify, recarregando instância [{}/{}]'.format(current_client+1, len(clients)))
                    reload_api(failed=True)

    except KeyboardInterrupt:
        if args.verbose:
            print('Salvando resultados parciais...')
        save_json(data, os.path.join(args.out_dir, 'features_{}_partial.json'.format(set_name)))
        raise

    if os.path.isfile(os.path.join(args.in_dir, 'features_{}_partial.json'.format(set_name))):
        os.remove(os.path.join(args.in_dir, 'features_{}_partial.json'.format(set_name)))

    return data


#==================================================================================================
#----------------------------------- PROGRAMA PRINCIPAL (MAIN) ------------------------------------

parser = argparse.ArgumentParser(allow_abbrev=False, description='SpotifyCrawler [v1.2.1]', epilog='Conjunto de ferramentas para extração de dados utilizando a Web API do Spotify. Todos os arquivos de entrada/saída utilizam o formato JSON.')

# To Do: quebrar em subparsers mais organizados
parser.add_argument('-i', '--in-dir', metavar=('DIR'), default='.', help='local contendo o(s) arquivo(s) a serem processados (padrão: pasta atual)')
parser.add_argument('-o', '--out-dir', metavar=('DIR'), default='.', help='local onde o(s) arquivo(s) gerado(s) serão salvos (padrão: pasta atual)')

parser.add_argument('-s', '--split-json', action='extend', nargs=2, metavar=('FILE', 'N'), help='divide o arquivo informado em arquivos menores, contendo até N itens em cada um')
parser.add_argument('-m', '--merge-json', action='extend', nargs=2, metavar=('PREFIX', 'FILE'), help='mescla arquivos menores, com nomes iniciados em PREFIX, em um arquivo único especificado por FILE')

parser.add_argument('-p', '--get-playlists', nargs='+', metavar=('FILE'), help='obtém todas as faixas contidas na(s) playlist(s) listada(s) no(s) arquivo(s) especificado(s)')
parser.add_argument('-a', '--get-albums', nargs='+', metavar=('FILE'), help='obtém informações de álbuns contidos no(s) arquivo(s) especificado(s)')
parser.add_argument('-d', '--get-album-tracks', nargs='+', metavar=('FILE'), help='obtém todas as faixas contidas no(s) álbum(ns) listado(s) no(s) arquivo(s) especificado(s)')
parser.add_argument('-f', '--get-features', nargs='+', metavar=('FILE'), help='obtém todas os recursos das faixas contidas no(s) arquivo(s) especificado(s)')

parser.add_argument('-c', '--credentials', metavar=('FILE'), default='credentials.json', help='especifica o arquivo com as credenciais de acesso (padrão: .\\credentials.json)')
parser.add_argument('-t', '--refresh-tokens', default=False, action='store_true', help='verifica se todos os tokens de acesso do arquivo de credenciais são válidos, reautenticando tokens inválidos se necessário')

parser.add_argument('-v', '--verbose', default=False, action='store_true', help='mostra mensagens de status e depuração durante a execução das tarefas')

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
        slice_name = '{}{:06d}.json'.format(re.sub('\\.[jJ][sS][oO][nN]$', '', args.split_json[0]), part)
        save_json(data[i:i+size], os.path.join(args.out_dir, slice_name))
        part += 1

    print('{} dividido em {} JSONs com {} ou menos elementos'.format(args.split_json[0], part, size))
    sys.exit(0)

# Processamento da opção --merge-json (-m)
elif args.merge_json:
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

    print('{} elementos contidos em {} JSONs foram mesclados em {}'.format(len(data), slices, args.merge_json[1]))
    sys.exit(0)

# Processamento da opção --refresh-tokens (-t)
elif args.refresh_tokens:
    reload_credentials()
    if args.verbose:
        print('Validando tokens de {} credenciais...'.format(len(clients)))

    for i in range(len(clients)):
        test = sp.current_user()
        reload_api()

# Processamento da opção --get-playlists (-p)
elif args.get_playlists:
    for file in args.get_playlists:
        source = load_json(os.path.join(args.in_dir, file))
        data = []

        for playlist_name, playlist_id in source.items():
            if args.verbose:
                print('Obtendo faixas da playlist "{}"...'.format(playlist_name))
            data = get_playlist(playlist_id)

            save_json(data, os.path.join(args.out_dir, 'playlist_{}.json'.format(playlist_name)))
            print('{} faixas salvas em playlist_{}.json'.format(len(data)-1, playlist_name))

# Processamento da opção --get-albums (-a)
elif args.get_albums:
    for file in args.get_albums:
        source = load_json(os.path.join(args.in_dir, file))
        data = []
        for item in source:
            if item.get('crawler_retrieved_track_ids'):
                continue

            if item.get('crawler_retrieved_album_ids'):
                for album_id in item['crawler_retrieved_album_ids']:
                    if not album_id in data:
                        data.append(album_id)
                break

            elif item.get('album').get('type') == 'album':
                if not item['album']['id'] in data:
                    data.append(item['album']['id'])

        if len(data):
            if args.verbose:
                print('Obtendo informações de {} álbuns encontrados em "{}"...'.format(len(data), file))
            albums = get_albums(data, re.sub('\\.[jJ][sS][oO][nN]$', '', file))

            save_json(albums, os.path.join(args.out_dir, 'albums_{}'.format(file)))
            print('{} álbuns salvos em albums_{}'.format(len(albums), file))

# Processamento da opção --get-album-tracks (-d)
elif args.get_album_tracks:
    for file in args.get_album_tracks:
        source = load_json(os.path.join(args.in_dir, file))
        data = []
        for item in source:
            if item.get('crawler_retrieved_track_ids'):
                continue

            if item.get('album').get('type') == 'album':
                data.append(item['album']['id'])

        if len(data):
            if args.verbose:
                print('Obtendo faixas de {} álbuns encontrados em "{}"...'.format(len(data), file))
            album_tracks = get_album_tracks(data, re.sub('\\.[jJ][sS][oO][nN]$', '', file))

            save_json(album_tracks, os.path.join(args.out_dir, 'album_tracks_{}'.format(file)))
            print('{} faixas de álbum salvas em album_tracks_{}'.format(len(album_tracks)-1, file))

# Processamento da opção --get-features (-f)
elif args.get_features:
    for file in args.get_features:
        source = load_json(os.path.join(args.in_dir, file))
        data = []
        for item in source:
            if item.get('type') == 'track':
                data.append(item['id'])

        if len(data):
            if args.verbose:
                print('Obtendo recursos para {} faixas encontradas em "{}"...'.format(len(data), file))
            features = get_features(data, re.sub('\\.[jJ][sS][oO][nN]$', '', file))

            save_json(features, os.path.join(args.out_dir, 'features_{}'.format(file)))
            print('Recursos de {} faixas salvas em features_{}'.format(len(features), file))

else:
    parser.print_help()
    sys.exit(1)
