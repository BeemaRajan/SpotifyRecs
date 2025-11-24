"""
MongoDB Database Loader
Loads processed track data into MongoDB
"""

import json
import os
from pymongo import MongoClient, ASCENDING
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def load_mongodb(json_file: str = 'data/processed/tracks_with_clusters.json'):
    """
    Load tracks data into MongoDB
    
    Args:
        json_file: Path to processed JSON file with cluster assignments
    """
    print("\n" + "="*60)
    print("MongoDB Database Loader")
    print("="*60 + "\n")
    
    # Check if file exists
    if not os.path.exists(json_file):
        print(f"✗ Error: File not found: {json_file}")
        print("\nPlease run the ML processing notebook first to generate processed data:")
        print("  ml_processing/audio_features_ml.ipynb")
        return
    
    # Connect to MongoDB
    print("Step 1: Connecting to MongoDB...")
    try:
        mongo_uri = os.getenv('MONGO_URI', 'mongodb://admin:password123@localhost:27017/spotifyrecs?authSource=admin')
        client = MongoClient(mongo_uri)
        db = client['spotifyrecs']
        collection = db['tracks']
        
        # Test connection
        client.admin.command('ping')
        print("✓ Connected to MongoDB\n")
    except Exception as e:
        print(f"✗ Failed to connect to MongoDB: {e}")
        print("\nMake sure MongoDB is running:")
        print("  docker-compose up -d mongodb")
        return
    
    # Load JSON data
    print("Step 2: Loading data from file...")
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            tracks = json.load(f)
        print(f"✓ Loaded {len(tracks)} tracks from {json_file}\n")
    except Exception as e:
        print(f"✗ Failed to load JSON file: {e}")
        return
    
    # Clear existing collection
    print("Step 3: Clearing existing collection...")
    collection.delete_many({})
    print("✓ Collection cleared\n")
    
    # Insert tracks
    print("Step 4: Inserting tracks...")
    try:
        if tracks:
            result = collection.insert_many(tracks)
            print(f"✓ Inserted {len(result.inserted_ids)} tracks\n")
        else:
            print("✗ No tracks to insert\n")
            return
    except Exception as e:
        print(f"✗ Failed to insert tracks: {e}")
        return
    
    # Create indexes
    print("Step 5: Creating indexes...")
    try:
        # Audio feature indexes
        collection.create_index([("energy", ASCENDING)])
        collection.create_index([("danceability", ASCENDING)])
        collection.create_index([("valence", ASCENDING)])
        collection.create_index([("tempo", ASCENDING)])
        collection.create_index([("cluster_id", ASCENDING)])
        collection.create_index([("track_id", ASCENDING)], unique=True)
        
        # Compound index
        collection.create_index([
            ("energy", ASCENDING),
            ("danceability", ASCENDING),
            ("tempo", ASCENDING)
        ])
        
        # Text index
        collection.create_index([
            ("title", "text"),
            ("artist", "text")
        ])
        
        print("✓ Created indexes\n")
    except Exception as e:
        print(f"✗ Failed to create indexes: {e}")
    
    # Verify data
    print("Step 6: Verifying data...")
    total_count = collection.count_documents({})
    print(f"✓ Total tracks in database: {total_count}")
    
    # Show cluster distribution
    cluster_pipeline = [
        {"$group": {"_id": "$cluster_id", "count": {"$sum": 1}}},
        {"$sort": {"_id": 1}}
    ]
    clusters = list(collection.aggregate(cluster_pipeline))
    
    if clusters:
        print("\nCluster distribution:")
        for cluster in clusters:
            print(f"  Cluster {cluster['_id']}: {cluster['count']} tracks")
    
    # Show sample tracks
    print("\nSample tracks:")
    sample_tracks = collection.find().limit(3)
    for i, track in enumerate(sample_tracks, 1):
        print(f"\n  [{i}] {track.get('title')} - {track.get('artist')}")
        print(f"      Energy: {track.get('energy'):.2f}, "
              f"Danceability: {track.get('danceability'):.2f}, "
              f"Valence: {track.get('valence'):.2f}")
        print(f"      Cluster: {track.get('cluster_id')}")
    
    print("\n" + "="*60)
    print("MongoDB loading complete!")
    print("="*60 + "\n")
    
    # Close connection
    client.close()


if __name__ == '__main__':
    import sys
    
    # Check for custom file path
    if len(sys.argv) > 1:
        json_file = sys.argv[1]
    else:
        json_file = 'data/processed/tracks_with_clusters.json'
    
    load_mongodb(json_file)
