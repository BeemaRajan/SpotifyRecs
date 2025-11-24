"""
Spotify Data Collector
Collects track data and audio features from Spotify API
"""

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
import json
import os
from dotenv import load_dotenv
from typing import List, Dict
import time

# Load environment variables
load_dotenv()


class SpotifyCollector:
    """Collects track data from Spotify API"""
    
    def __init__(self):
        """Initialize Spotify client"""
        client_id = os.getenv('SPOTIFY_CLIENT_ID')
        client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
        
        if not client_id or not client_secret:
            raise ValueError("SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET must be set in .env file")
        
        # Initialize Spotify client
        client_credentials_manager = SpotifyClientCredentials(
            client_id=client_id,
            client_secret=client_secret
        )
        self.sp = spotipy.Spotify(client_credentials_manager=client_credentials_manager)
        print("✓ Connected to Spotify API")
    
    def get_playlist_tracks(self, playlist_id: str) -> List[str]:
        """
        Get all track IDs from a playlist
        
        Args:
            playlist_id: Spotify playlist ID or URI
        
        Returns:
            List of track IDs
        """
        track_ids = []
        try:
            results = self.sp.playlist_tracks(playlist_id)
            
            while results:
                for item in results['items']:
                    if item['track'] and item['track']['id']:
                        track_ids.append(item['track']['id'])
                
                # Handle pagination
                if results['next']:
                    results = self.sp.next(results)
                else:
                    results = None
            
            print(f"  Found {len(track_ids)} tracks in playlist")
            return track_ids
            
        except Exception as e:
            print(f"  Error getting playlist tracks: {e}")
            return []
    
    def get_track_details(self, track_id: str) -> Dict:
        """
        Get track metadata for a single track
        
        Args:
            track_id: Spotify track ID
        
        Returns:
            Dictionary with track details
        """
        try:
            track = self.sp.track(track_id)
            
            return {
                'track_id': f"spotify:track:{track_id}",
                'title': track['name'],
                'artist': ', '.join([artist['name'] for artist in track['artists']]),
                'album': track['album']['name'],
                'release_date': track['album']['release_date'],
                'duration_ms': track['duration_ms'],
                'popularity': track['popularity'],
                'isrc': track.get('external_ids', {}).get('isrc', None)
            }
        except Exception as e:
            print(f"  Error getting track details for {track_id}: {e}")
            return None
    
    def get_audio_features(self, track_ids: List[str]) -> List[Dict]:
        """
        Get audio features for multiple tracks (batch operation)
        
        Args:
            track_ids: List of Spotify track IDs
        
        Returns:
            List of audio feature dictionaries
        """
        features_list = []
        
        # Spotify API allows up to 100 tracks per request
        batch_size = 100
        
        for i in range(0, len(track_ids), batch_size):
            batch = track_ids[i:i + batch_size]
            
            try:
                features = self.sp.audio_features(batch)
                
                for feature in features:
                    if feature:  # Skip None results
                        features_list.append({
                            'track_id': f"spotify:track:{feature['id']}",
                            'acousticness': feature['acousticness'],
                            'danceability': feature['danceability'],
                            'energy': feature['energy'],
                            'instrumentalness': feature['instrumentalness'],
                            'key': feature['key'],
                            'liveness': feature['liveness'],
                            'loudness': feature['loudness'],
                            'mode': feature['mode'],
                            'speechiness': feature['speechiness'],
                            'tempo': feature['tempo'],
                            'time_signature': feature['time_signature'],
                            'valence': feature['valence']
                        })
                
                # Rate limiting: be nice to Spotify API
                time.sleep(0.1)
                
            except Exception as e:
                print(f"  Error getting audio features for batch: {e}")
        
        return features_list
    
    def collect_from_playlists(self, playlist_ids: List[str], output_file: str = 'data/raw/tracks.json'):
        """
        Collect tracks from multiple playlists
        
        Args:
            playlist_ids: List of Spotify playlist IDs
            output_file: Path to save collected data
        """
        print(f"\n{'='*60}")
        print("Starting data collection from Spotify...")
        print(f"{'='*60}\n")
        
        all_track_ids = set()
        
        # Step 1: Collect track IDs from all playlists
        print("Step 1: Collecting track IDs from playlists...")
        for i, playlist_id in enumerate(playlist_ids, 1):
            print(f"  [{i}/{len(playlist_ids)}] Processing playlist: {playlist_id}")
            track_ids = self.get_playlist_tracks(playlist_id)
            all_track_ids.update(track_ids)
            time.sleep(0.5)  # Rate limiting
        
        print(f"\n✓ Found {len(all_track_ids)} unique tracks\n")
        
        # Step 2: Get track details
        print("Step 2: Fetching track metadata...")
        tracks_data = []
        all_track_ids = list(all_track_ids)
        
        for i, track_id in enumerate(all_track_ids, 1):
            if i % 100 == 0:
                print(f"  Progress: {i}/{len(all_track_ids)} tracks")
            
            track_details = self.get_track_details(track_id)
            if track_details:
                tracks_data.append(track_details)
            
            # Rate limiting
            if i % 50 == 0:
                time.sleep(1)
        
        print(f"\n✓ Retrieved metadata for {len(tracks_data)} tracks\n")
        
        # Step 3: Get audio features
        print("Step 3: Fetching audio features...")
        audio_features = self.get_audio_features(all_track_ids)
        print(f"✓ Retrieved audio features for {len(audio_features)} tracks\n")
        
        # Step 4: Merge track details with audio features
        print("Step 4: Merging data...")
        features_map = {f['track_id']: f for f in audio_features}
        
        complete_tracks = []
        for track in tracks_data:
            track_id = track['track_id']
            if track_id in features_map:
                # Merge track details with audio features
                complete_track = {**track, **features_map[track_id]}
                complete_tracks.append(complete_track)
        
        print(f"✓ Successfully merged {len(complete_tracks)} complete tracks\n")
        
        # Step 5: Save to file
        print(f"Step 5: Saving to {output_file}...")
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(complete_tracks, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Data saved successfully\n")
        print(f"{'='*60}")
        print(f"Collection complete!")
        print(f"  Total tracks: {len(complete_tracks)}")
        print(f"  Output file: {output_file}")
        print(f"  File size: {os.path.getsize(output_file) / 1024:.2f} KB")
        print(f"{'='*60}\n")
        
        return complete_tracks


def main():
    """Main execution function"""
    
    # Example playlist IDs (replace with your own or use these diverse ones)
    # You can get playlist IDs from Spotify URLs: 
    # https://open.spotify.com/playlist/PLAYLIST_ID
    
    example_playlists = [
        '37i9dQZF1DXcBWIGoYBM5M',  # Today's Top Hits
        '37i9dQZF1DX0XUsuxWHRQd',  # RapCaviar
        '37i9dQZF1DX4dyzvuaRJ0n',  # Mint (pop)
        '37i9dQZF1DX4JAvHpjipBk',  # New Music Friday
        '37i9dQZF1DX1lVhptIYRda',  # Hot Country
        '37i9dQZF1DX4sWSpwq3LiO',  # Peaceful Piano
        '37i9dQZF1DX3rxVfibe1L0',  # Mood Booster
        '37i9dQZF1DX0BcQWzuB7ZO',  # Dance Rising
        '37i9dQZF1DWXRqgorJj26U',  # Rock Classics
        '37i9dQZF1DWWEJlAGA9gs0',  # Classical Essentials
    ]
    
    print("\nSpotify Data Collector")
    print("=" * 60)
    print("Make sure you have set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET")
    print("in your .env file!")
    print("=" * 60)
    
    try:
        collector = SpotifyCollector()
        
        # Option to use custom playlists
        use_custom = input("\nUse custom playlist IDs? (y/n): ").lower()
        
        if use_custom == 'y':
            print("\nEnter playlist IDs (one per line, empty line to finish):")
            custom_playlists = []
            while True:
                playlist_id = input("Playlist ID: ").strip()
                if not playlist_id:
                    break
                custom_playlists.append(playlist_id)
            
            if custom_playlists:
                playlist_ids = custom_playlists
            else:
                print("No playlists entered, using example playlists")
                playlist_ids = example_playlists
        else:
            playlist_ids = example_playlists
        
        # Collect data
        tracks = collector.collect_from_playlists(
            playlist_ids=playlist_ids,
            output_file='data/raw/spotify_tracks.json'
        )
        
        print("\nData collection complete!")
        print(f"  Next steps:")
        print(f"  1. Run ML processing notebook: ml_processing/audio_features_ml.ipynb")
        print(f"  2. Load data into databases: python database_setup/load_mongo.py")
        
    except Exception as e:
        print(f"\nError: {e}")
        print("Make sure your Spotify credentials are correct in .env file")


if __name__ == '__main__':
    main()
