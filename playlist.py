import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

import spotipy
from spotipy.oauth2 import SpotifyOAuth

# Configuration de l'authentification Spotify
client_id = 'c8de126b1c154032b3a126c49485e743'
client_secret = 'eafb134699f440b2874b5419b5bba1c6'
redirect_uri = 'http://localhost:8888/callback'

scope = 'playlist-modify-public'

print("Initializing SpotifyOAuth...")

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=client_id,
                                               client_secret=client_secret,
                                               redirect_uri=redirect_uri,
                                               scope=scope))

try:
    user_id = sp.me()['id']
    print(f"Authenticated as user: {user_id}")
except spotipy.exceptions.SpotifyException as e:
    print(f"Failed to authenticate: {e}")
    exit(1)

def get_track_and_artist_ids_from_playlist(playlist_url):
    playlist_id = playlist_url.split('/')[-1].split('?')[0]
    playlist_tracks = sp.playlist_tracks(playlist_id)
    track_ids = []
    artist_ids = []

    for item in playlist_tracks['items']:
        track_ids.append(item['track']['id'])
        for artist in item['track']['artists']:
            artist_ids.append(artist['id'])
    
    return track_ids, artist_ids

def filter_tracks(tracks, excluded_track_ids, excluded_artist_ids, min_bpm=None, max_bpm=None, min_valence=None, max_valence=None):
    filtered_tracks = []

    for track_id in tracks:
        track = sp.track(track_id)
        if track_id in excluded_track_ids:
            continue
        
        artist_ids = [artist['id'] for artist in track['artists']]
        if any(artist_id in excluded_artist_ids for artist_id in artist_ids):
            continue

        features = sp.audio_features(track_id)[0]
        
        if min_bpm and features['tempo'] < min_bpm:
            continue
        if max_bpm and features['tempo'] > max_bpm:
            continue
        if min_valence and features['valence'] < min_valence:
            continue
        if max_valence and features['valence'] > max_valence:
            continue
        
        filtered_tracks.append(track_id)
    
    return filtered_tracks



def generate_playlist_from_input(input_titles=None, input_artists=None, input_playlist=None,
                                 num_tracks=20, min_bpm=None, max_bpm=None, 
                                 min_valence=None, max_valence=None, genres=None):
    track_ids = []
    excluded_track_ids = []
    excluded_artist_ids = []

    # Exclusion des titres et artistes donnés
    if input_titles:
        for title in input_titles:
            results = sp.search(q='track:' + title, type='track', limit=5)
            for track in results['tracks']['items']:
                excluded_track_ids.append(track['id'])
    
    if input_artists:
        for artist in input_artists:
            results = sp.search(q='artist:' + artist, type='artist')
            if results['artists']['items']:
                artist_id = results['artists']['items'][0]['id']
                excluded_artist_ids.append(artist_id)
                top_tracks = sp.artist_top_tracks(artist_id)['tracks']
                for track in top_tracks[:5]:
                    excluded_track_ids.append(track['id'])

    # Exclusion des titres et artistes de la playlist
    if input_playlist:
        for playlist_url in input_playlist:
            p_track_ids, p_artist_ids = get_track_and_artist_ids_from_playlist(playlist_url)
            excluded_track_ids.extend(p_track_ids)
            excluded_artist_ids.extend(p_artist_ids)

    # Recommandations basées sur les genres
    if genres:
        recommendations = sp.recommendations(seed_genres=genres, limit=100)
        for track in recommendations['tracks']:
            track_ids.append(track['id'])

    # Éviter les doublons
    track_ids = list(set(track_ids))
    
    # Filtrage des pistes exclues et par BPM, valence (humeur)
    track_ids = filter_tracks(track_ids, excluded_track_ids, excluded_artist_ids, min_bpm, max_bpm, min_valence, max_valence)
    
    # Si plus de titres que nécessaire, on les réduit aléatoirement
    if len(track_ids) > num_tracks:
        import random
        track_ids = random.sample(track_ids, num_tracks)

    # Création d'une playlist
    user_id = sp.me()['id']
    new_playlist = sp.user_playlist_create(user_id, 'Generated Playlist', public=True)
    sp.user_playlist_add_tracks(user_id, new_playlist['id'], track_ids)

    return new_playlist['external_urls']['spotify']

# Exemple d'utilisation avec les paramètres fournis
new_playlist_url = generate_playlist_from_input(
    input_titles=["Ta façon d'être", "BESOIN D'EN PARLER", "DIVAS"],
    input_artists=["Araujo", "Siji", "SEYLI","DMS"],
    input_playlist=["https://open.spotify.com/playlist/5aaVQvemS3KN3CIT9kpICX"],
    num_tracks=20,
    min_bpm=90,
    max_bpm=130,
    min_valence=0.2,
    genres=["rap"]
)

print(f"La nouvelle playlist est disponible à : {new_playlist_url}")