import argparse
import json
import os
import spotipy

from requests.exceptions import ReadTimeout
# from spotipy.cache_handler import CacheFileHandler
from spotipy.oauth2 import SpotifyOAuth

parser = argparse.ArgumentParser(allow_abbrev=False, description='SpotifyCrawler [v0.3]', epilog='Extrai dados utilizando a API do Spotify')
parser.add_argument('-v', '--verbose', default=False, action='store_true', help='mostra mensagens de status')
args = parser.parse_args()


# Controle de requisições
sent_requests = 0
max_requests = 100
requests_delay = 0
cooldown_delay = 30


# Controle de credenciais
available_clients = 0
current_client = 0
clients = []


def load_credentials(path):
    global available_clients
    global current_client
    global clients
    
    clients = load_json(path)
    available_clients = len(clients)
    if args.verbose:
        print("{} credenciais carregadas".format(available_clients))
        
    if current_client < 1:
        current_client = 1
        sp_init()

def sp_init():
    global sp
    client_id = clients[current_client]["client_id"]
    client_secret = clients[current_client]["client_secret"]
    redirect_uri = clients[current_client]["redirect_uri"]
    scope = clients[current_client]["scope"]
    
    # TODO: consertar essa gambiarra
    #cache_handler = CacheFileHandler(cache_path=path)
    if os.path.exists(".cache"):
        os.remove(".cache")        
    save_json(clients[current_client]["token"][0], ".cache")    

    auth_manager = SpotifyOAuth(client_id=client_id, client_secret=client_secret, redirect_uri=redirect_uri, scope=scope) # , cache_handler=cache_handler)
    sp = spotipy.Spotify(auth_manager=auth_manager)

def sp_reload():
    if current_client >= available_clients:
        current_client = 1
    else:
        current_client += 1
        
    del sp
    sp_init()

def check_request_limits():
    global sent_requests
    global max_requests
    global cooldown_delay
    if sent_requests > max_requests:
        sent_requests = 0
        if args.verbose:
            print("CooldownMsg")
        time.sleep(cooldown_delay)
    sent_requests += 1

def load_json(path):
    result = []
    with open(path, 'r', encoding='utf8') as file:
        result = json.load(file)
    return result
        
def save_json(data, path):
    with open(path, 'w', encoding='utf8') as file:
        json.dump(data, file)

def get_playlist(playlist_id):
    global sp
    result = []
    
    while True:
        try:
            check_request_limits()
            playlist = sp.playlist(playlist_id)
            break;

        except ReadTimeout:
            if args.verbose:
                print('ReadTimeoutMsg')
                sp_reload()
                # dump_partial?
    
    tracks = playlist['tracks']
    
    while tracks:
        for item in tracks['items']:
            result.append(item['track'])

        if tracks['next']:
            while True:
                try:
                    check_request_limits()
                    tracks = sp.next(tracks)
                    break;
                    
                except ReadTimeout:
                    if args.verbose:
                        print('ReadTimeoutMsg')
                        sp_reload()
                        # dump_partial?
        else:
            tracks = None
            
    return result


#---------------------------------------------------------------
load_credentials("credentials.json")

test = get_playlist("1I2M54ULwXzDvjRgcp4Mpv")

save_json(test, "test.json")
