"""
Kaggle CSV to JSON Converter
Converts Kaggle Spotify dataset from CSV to JSON format compatible with the project
"""

import csv
import json
import os


def convert_csv_to_json(
    csv_file: str = 'data/raw/spotify_top_songs_audio_features.csv',
    output_file: str = 'data/raw/tracks.json'
):
    """
    Convert Kaggle CSV data to JSON format expected by the project

    Args:
        csv_file: Path to input CSV file
        output_file: Path to output JSON file

    The CSV has columns:
        id, artist_names, track_name, source, key, mode, time_signature,
        danceability, energy, speechiness, acousticness, instrumentalness,
        liveness, valence, loudness, tempo, duration_ms, weeks_on_chart, streams

    We convert to JSON format matching spotify_collector.py output:
        track_id, title, artist, album, duration_ms, popularity,
        acousticness, danceability, energy, instrumentalness, key,
        liveness, loudness, mode, speechiness, tempo, time_signature, valence
    """
    print("\n" + "="*60)
    print("Kaggle CSV to JSON Converter")
    print("="*60 + "\n")

    # Check if CSV file exists
    if not os.path.exists(csv_file):
        print(f"  Error: CSV file not found: {csv_file}")
        print("\nPlease download the Kaggle dataset and place it at:")
        print(f"  {csv_file}")
        print("\nDataset: https://www.kaggle.com/datasets/julianoorlandi/spotify-top-songs-and-audio-features")
        return

    print(f"Step 1: Reading CSV file: {csv_file}")

    tracks = []
    skipped_count = 0
    duplicate_count = 0
    seen_combinations = set()

    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            for row_num, row in enumerate(reader, start=2):  # start=2 because row 1 is header
                try:
                    # --- DUPLICATE CHECK START ---
                    # Check for duplicates based on Title and Artist (Case-insensitive)
                    # We check this early to skip processing if it's a duplicate
                    current_title = row['track_name'].strip()
                    current_artist = row['artist_names'].strip()
                    
                    # Create a unique key for the song
                    combo_key = (current_title.lower(), current_artist.lower())
                    
                    if combo_key in seen_combinations:
                        duplicate_count += 1
                        continue
                    
                    # Add to seen set
                    seen_combinations.add(combo_key)
                    # --- DUPLICATE CHECK END ---

                    # Map key names (CSV uses different names than expected)
                    # Note: 'key' in CSV is the musical key name (e.g., "G", "C#/Db")
                    # We need to convert this to a numeric value (0-11) for compatibility
                    key_mapping = {
                        'C': 0, 'C#/Db': 1, 'D': 2, 'D#/Eb': 3,
                        'E': 4, 'F': 5, 'F#/Gb': 6, 'G': 7,
                        'G#/Ab': 8, 'A': 9, 'A#/Bb': 10, 'B': 11
                    }

                    # Mode mapping: "Major" -> 1, "Minor" -> 0
                    mode_value = 1 if row.get('mode', '').strip().lower() == 'major' else 0

                    # Time signature: extract first digit from "4 beats", "3 beats", etc.
                    time_sig_str = row.get('time_signature', '4 beats')
                    time_signature = int(time_sig_str.split()[0]) if time_sig_str else 4

                    # Create track object matching expected format
                    track = {
                        'track_id': f"spotify:track:{row['id']}",
                        'title': row['track_name'],
                        'artist': row['artist_names'],
                        'album': row.get('source', 'Unknown Album'),  # CSV uses 'source' as label/album
                        'duration_ms': int(float(row['duration_ms'])) if row.get('duration_ms') else 0,
                        'popularity': int(float(row.get('streams', 0)) / 1000000) if row.get('streams') else 0,  # Approximate popularity from streams

                        # Audio features (convert to float)
                        'acousticness': float(row['acousticness']),
                        'danceability': float(row['danceability']),
                        'energy': float(row['energy']),
                        'instrumentalness': float(row['instrumentalness']),
                        'key': key_mapping.get(row.get('key', '').strip(), 0),  # Convert key name to number
                        'liveness': float(row['liveness']),
                        'loudness': float(row['loudness']),
                        'mode': mode_value,
                        'speechiness': float(row['speechiness']),
                        'tempo': float(row['tempo']),
                        'time_signature': time_signature,
                        'valence': float(row['valence']),
                    }

                    tracks.append(track)

                except (ValueError, KeyError) as e:
                    skipped_count += 1
                    print(f"  Warning: Skipped row {row_num} due to error: {e}")
                    continue

        print(f"Successfully read {len(tracks)} unique tracks from CSV")
        if duplicate_count > 0:
            print(f"  (Removed {duplicate_count} duplicate songs)")
        if skipped_count > 0:
            print(f"  (Skipped {skipped_count} rows due to errors)")
        print()

    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return

    # Save to JSON
    print(f"Step 2: Saving to JSON file: {output_file}")

    try:
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_file), exist_ok=True)

        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(tracks, f, indent=2, ensure_ascii=False)

        file_size_kb = os.path.getsize(output_file) / 1024
        print(f"  Successfully saved {len(tracks)} tracks to JSON")
        print(f"  File size: {file_size_kb:.2f} KB")
        print()

    except Exception as e:
        print(f"  Error saving JSON file: {e}")
        return

    # Show sample data
    print("Step 3: Sample of converted data")
    print("-" * 60)

    for i, track in enumerate(tracks[:3], 1):
        print(f"\n[{i}] {track['title']} - {track['artist']}")
        print(f"    Track ID: {track['track_id']}")
        print(f"    Album: {track['album']}")
        print(f"    Duration: {track['duration_ms']}ms")
        print(f"    Audio Features:")
        print(f"      Energy: {track['energy']:.3f}, "
              f"Danceability: {track['danceability']:.3f}, "
              f"Valence: {track['valence']:.3f}")
        print(f"      Tempo: {track['tempo']:.1f} BPM, "
              f"Key: {track['key']}, "
              f"Mode: {'Major' if track['mode'] == 1 else 'Minor'}")

    print("\n" + "="*60)
    print("Conversion complete!")
    print("="*60)
    print("\nNext steps:")
    print("  1. Run ML processing notebook: ml_processing/audio_features_ml.py")
    print("  2. Load data into databases:")
    print("     python database_setup/load_mongo.py")
    print("     python database_setup/load_neo4j.py")
    print("="*60 + "\n")


def main():
    """Main execution function"""
    import sys

    # Allow custom paths via command line
    if len(sys.argv) > 2:
        csv_file = sys.argv[1]
        output_file = sys.argv[2]
    elif len(sys.argv) > 1:
        csv_file = sys.argv[1]
        output_file = 'data/raw/tracks.json'
    else:
        csv_file = 'data/raw/spotify_top_songs_audio_features.csv'
        output_file = 'data/raw/tracks.json'

    convert_csv_to_json(csv_file, output_file)


if __name__ == '__main__':
    main()
