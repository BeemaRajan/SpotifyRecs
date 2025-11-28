"""
Spotify Data Collector
Collects track data and audio features from Spotify API
"""

import spotipy
from spotipy.oauth2 import SpotifyOAuth
import json
import os
from dotenv import load_dotenv
from typing import List, Dict
import time
import re
import glob

# Load environment variables
load_dotenv()


class SpotifyCollector:
    """Collects track data from Spotify API"""
    
    def __init__(self):
        """Initialize Spotify client with user authentication"""
        client_id = os.getenv('SPOTIFY_CLIENT_ID')
        client_secret = os.getenv('SPOTIFY_CLIENT_SECRET')
        redirect_uri = os.getenv('SPOTIFY_REDIRECT_URI', 'http://localhost:8888/callback')

        if not client_id or not client_secret:
            raise ValueError("SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET must be set in .env file")

        # Initialize Spotify client with OAuth (user authentication)
        auth_manager = SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope='user-read-private user-library-read',
            cache_path='.spotify_cache'
        )
        self.sp = spotipy.Spotify(auth_manager=auth_manager)
        print("✓ Connected to Spotify API with user authentication")
    
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


def get_next_output_filename(base_dir: str = 'data/raw', prefix: str = 'spotify_tracks') -> str:
    """
    Find the next available filename with incrementing number.

    Args:
        base_dir: Directory to check for existing files
        prefix: Filename prefix (default: 'spotify_tracks')

    Returns:
        Path to the next available file (e.g., 'data/raw/spotify_tracks_0.json')
    """
    # Create directory if it doesn't exist
    os.makedirs(base_dir, exist_ok=True)

    # Find all existing files matching the pattern
    pattern = os.path.join(base_dir, f'{prefix}_*.json')
    existing_files = glob.glob(pattern)

    if not existing_files:
        # No existing files, start with 0
        next_number = 0
    else:
        # Extract numbers from existing filenames
        numbers = []
        for filepath in existing_files:
            filename = os.path.basename(filepath)
            # Extract number from pattern like 'spotify_tracks_5.json'
            match = re.search(rf'{prefix}_(\d+)\.json$', filename)
            if match:
                numbers.append(int(match.group(1)))

        # Get the next number
        next_number = max(numbers) + 1 if numbers else 0

    output_file = os.path.join(base_dir, f'{prefix}_{next_number}.json')
    return output_file


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

    # Default playlists covering various genres
    DEFAULT_PLAYLISTS = {
        'Hip-Hop & Rap': [
            '15efRmOd668AKaKJUVVdcZ',  # Rap Nation (164 tracks)
            '0NCspsyf0OS4BsPgGhkQXM',  # Trap Nation (151 tracks, 2M+ followers)
            '60reOQRhSzi7AnslijjP8x',  # Wave Nation (77 tracks)
        ],
        'Lo-Fi & Chill': [
            '0vvXsWCC9xrXsKd4FyS8kM',  # Lofi Girl - beats to relax/study to (500 tracks, 7.1M+ followers)
            '0CFuMybe6s77w6QQrJjW7d',  # Chillhop Radio (300 tracks, 627K+ followers)
            '74sUjcvpGfdOvCHvgzNEDO',  # lofi hip hop beats (200 tracks, 1M+ followers)
        ],
        'Indie & Alternative': [
            '4H6VS6HIC2cn42UlXj9BLi',  # Soft Indie - Indie Pop/Rock/Folk
            '6jcrMxA2x01W43Hu7onvEC',  # Daydream: Indie & Alternative
        ],
        'Electronic/EDM/House': [
            '7qhhMMuWRxnq8pbvUlNcKy',  # EDM & HOUSE TOP 100 (100 tracks, 20.9K followers)
            '4kyg9qA547jUo52Ee5oWsJ',  # House & Techno 2025 (79 tracks, 14K followers)
            '5Hl7t263NvJVasvEYuXgIr',  # Techno House 2025 | Party Hits (82 tracks, 30.9K followers)
        ],
        'Throwback/Decades': [
            '0JNuNJ5bag4ANieh61XYMC',  # Top Hits 2020-Today
            '1BCipY1frgsqhrrJnRDhzv',  # Top Hits 2010-2019
            '1mdQJeKlV7HZgqoMuy6v4t',  # Top Hits 2000-2009
            '2yCL2JuHkpjC2yVQ3B1d1g',  # Top Hits 1990-1999
        ]
    }

    print("\nSpotify Data Collector")
    print("=" * 60)
    print("SETUP REQUIREMENTS:")
    print("1. SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET in .env file")
    print("2. SPOTIFY_REDIRECT_URI (optional, defaults to http://localhost:8888/callback)")
    print("\nIMPORTANT: User Authentication Required")
    print("  - A browser window will open for Spotify login")
    print("  - Log in and authorize the app")
    print("  - You'll be redirected to localhost (this is normal)")
    print("  - Copy the FULL URL from your browser and paste it back here")
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
            # Use default playlists
            print("\n✓ Using default playlists covering multiple genres:")
            playlist_ids = []
            for genre, playlists in DEFAULT_PLAYLISTS.items():
                print(f"\n  {genre}:")
                for playlist_id in playlists:
                    print(f"    - {playlist_id}")
                playlist_ids.extend(playlists)

            print(f"\n✓ Total: {len(playlist_ids)} playlists")

        # Get next available filename
        output_file = get_next_output_filename()
        print(f"\n✓ Output will be saved to: {output_file}\n")

        # Collect data
        tracks = collector.collect_from_playlists(
            playlist_ids=playlist_ids,
            output_file=output_file
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
