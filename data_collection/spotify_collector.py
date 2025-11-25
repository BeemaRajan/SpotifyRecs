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
import re

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
        total_batches = (len(track_ids) + batch_size - 1) // batch_size

        for batch_num, i in enumerate(range(0, len(track_ids), batch_size), 1):
            batch = track_ids[i:i + batch_size]

            print(f"  Processing batch {batch_num}/{total_batches} ({len(batch)} tracks)...")

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

                # Generous rate limiting to avoid hitting API limits
                time.sleep(1.5)

            except Exception as e:
                print(f"  ✗ Error getting audio features for batch {batch_num}: {e}")

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
            time.sleep(1.5)  # Generous rate limiting between playlists
        
        print(f"\n✓ Found {len(all_track_ids)} unique tracks\n")
        
        # Step 2: Get track details
        print("Step 2: Fetching track metadata...")
        print(f"  This will take approximately {len(all_track_ids) * 0.1:.0f} seconds...")
        tracks_data = []
        all_track_ids = list(all_track_ids)

        for i, track_id in enumerate(all_track_ids, 1):
            if i % 50 == 0:
                print(f"  Progress: {i}/{len(all_track_ids)} tracks ({i*100//len(all_track_ids)}%)")

            track_details = self.get_track_details(track_id)
            if track_details:
                tracks_data.append(track_details)

            # Generous rate limiting - sleep every 30 tracks
            if i % 30 == 0:
                time.sleep(2)
        
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


def extract_playlist_ids(input_text: str) -> List[str]:
    """
    Extract playlist IDs from various input formats:
    - Full Spotify URLs: https://open.spotify.com/playlist/PLAYLIST_ID
    - Playlist IDs directly: PLAYLIST_ID
    - Comma or space separated

    Args:
        input_text: String containing playlist URLs or IDs

    Returns:
        List of extracted playlist IDs
    """
    playlist_ids = []

    # Pattern to match Spotify playlist URLs
    url_pattern = r'spotify\.com/playlist/([a-zA-Z0-9]+)'

    # Find all URLs first
    url_matches = re.findall(url_pattern, input_text)
    playlist_ids.extend(url_matches)

    # If no URLs found, try to extract IDs directly
    if not playlist_ids:
        # Split by common delimiters
        parts = re.split(r'[,\s\n]+', input_text.strip())
        for part in parts:
            if part and len(part) == 22 and part.isalnum():
                playlist_ids.append(part)

    return playlist_ids


def main():
    """Main execution function"""

    print("\nSpotify Data Collector")
    print("=" * 60)
    print("Make sure you have set SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET")
    print("in your .env file!")
    print("=" * 60)

    try:
        collector = SpotifyCollector()

        # Option to use custom playlists
        print("\n" + "=" * 60)
        print("PLAYLIST INPUT OPTIONS")
        print("=" * 60)
        print("You can input playlists in multiple ways:")
        print("  1. Paste full Spotify URLs (one or more)")
        print("     Example: https://open.spotify.com/playlist/37i9dQZEVXbMDoHDwVN2tF")
        print("  2. Enter just the playlist IDs (comma or space separated)")
        print("     Example: 37i9dQZEVXbMDoHDwVN2tF, 3fB6UcYdnPkXJhEMV9kWtB")
        print("  3. Mix of URLs and IDs")
        print("\nTo find playlists on Spotify:")
        print("  - Open Spotify web player (open.spotify.com)")
        print("  - Search for playlists (e.g., 'Top 100', 'Rock', 'Workout')")
        print("  - Copy the URL from your browser")
        print("=" * 60)

        use_custom = input("\nEnter your own playlists? (y/n): ").lower()

        if use_custom == 'y':
            print("\nPaste your playlist URLs or IDs below.")
            print("You can paste multiple at once (separated by commas, spaces, or new lines)")
            print("Type 'done' on a new line when finished:\n")

            all_input = []
            while True:
                line = input().strip()
                if line.lower() == 'done':
                    break
                if line:
                    all_input.append(line)

            # Combine all input and extract IDs
            combined_input = ' '.join(all_input)
            playlist_ids = extract_playlist_ids(combined_input)

            if playlist_ids:
                print(f"\n✓ Found {len(playlist_ids)} playlist(s):")
                for i, pid in enumerate(playlist_ids, 1):
                    print(f"  {i}. {pid}")
            else:
                print("\n✗ No valid playlist IDs found.")
                print("Please make sure you're using valid Spotify playlist URLs or IDs.")
                return
        else:
            print("\n✗ No playlists provided. Exiting.")
            print("\nTo collect data, run again and enter your playlist URLs or IDs.")
            return
        
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
