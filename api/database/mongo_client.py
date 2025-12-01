"""
MongoDB Client
Handles connection and operations for MongoDB database
"""

from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
import os
from typing import List, Dict, Optional


class MongoDBClient:
    """Singleton MongoDB client"""
    
    _instance = None
    _client = None
    _db = None
    _collection = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MongoDBClient, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize MongoDB connection"""
        try:
            mongo_uri = os.getenv('MONGO_URI', 'mongodb://admin:password123@localhost:27017/spotifyrecs?authSource=admin')
            db_name = os.getenv('MONGO_DB', 'spotifyrecs')
            collection_name = os.getenv('MONGO_COLLECTION', 'tracks')
            
            self._client = MongoClient(mongo_uri, serverSelectionTimeoutMS=5000)
            self._db = self._client[db_name]
            self._collection = self._db[collection_name]
            
            # Test connection
            self._client.admin.command('ping')
            print(f"✓ Connected to MongoDB: {db_name}.{collection_name}")
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            print(f"✗ MongoDB connection failed: {e}")
            self._client = None
    
    def check_connection(self) -> bool:
        """Check if MongoDB connection is active"""
        if self._client is None:
            return False
        try:
            self._client.admin.command('ping')
            return True
        except Exception:
            return False
    
    def get_collection(self):
        """Get tracks collection"""
        return self._collection
    
    def create_indexes(self):
        """Create indexes for efficient querying"""
        try:
            # Audio feature indexes for range queries
            self._collection.create_index([("energy", ASCENDING)])
            self._collection.create_index([("danceability", ASCENDING)])
            self._collection.create_index([("valence", ASCENDING)])
            self._collection.create_index([("tempo", ASCENDING)])
            self._collection.create_index([("cluster_id", ASCENDING)])
            
            # Compound index for multi-feature queries
            self._collection.create_index([
                ("energy", ASCENDING),
                ("danceability", ASCENDING),
                ("tempo", ASCENDING)
            ])
            
            # Text index for search
            self._collection.create_index([
                ("title", "text"),
                ("artist", "text")
            ])
            
            print("✓ Created MongoDB indexes")
        except Exception as e:
            print(f"✗ Failed to create indexes: {e}")
    
    # Query 1: Range query on audio features
    def search_by_features(self, filters: Dict) -> List[Dict]:
        """
        Search tracks by audio feature ranges
        
        Args:
            filters: Dictionary with min/max values for audio features
                    e.g., {"energy_min": 0.7, "energy_max": 1.0, "tempo_min": 120}
        
        Returns:
            List of matching tracks
        """
        query = {}
        
        # Build range query from filters
        feature_names = ['energy', 'danceability', 'valence', 'tempo', 
                        'acousticness', 'instrumentalness', 'liveness', 
                        'speechiness', 'loudness']
        
        for feature in feature_names:
            min_key = f"{feature}_min"
            max_key = f"{feature}_max"
            
            if min_key in filters or max_key in filters:
                query[feature] = {}
                if min_key in filters:
                    query[feature]["$gte"] = filters[min_key]
                if max_key in filters:
                    query[feature]["$lte"] = filters[max_key]
        
        # Add cluster filter if provided
        if "cluster_id" in filters:
            query["cluster_id"] = filters["cluster_id"]
        
        try:
            results = list(self._collection.find(query).limit(100))
            return results
        except Exception as e:
            print(f"Error in search_by_features: {e}")
            return []
    
    # Query 2: Aggregation pipeline for cluster statistics
    def get_cluster_stats(self, cluster_id: Optional[int] = None) -> List[Dict]:
        """
        Calculate average audio features by cluster
        
        Args:
            cluster_id: Specific cluster ID, or None for all clusters
        
        Returns:
            List of cluster statistics
        """
        pipeline = []
        
        # Match specific cluster if provided
        if cluster_id is not None:
            pipeline.append({"$match": {"cluster_id": cluster_id}})
        
        # Group by cluster and calculate averages
        pipeline.extend([
            {
                "$group": {
                    "_id": "$cluster_id",
                    "count": {"$sum": 1},
                    "avg_energy": {"$avg": "$energy"},
                    "avg_danceability": {"$avg": "$danceability"},
                    "avg_valence": {"$avg": "$valence"},
                    "avg_tempo": {"$avg": "$tempo"},
                    "avg_acousticness": {"$avg": "$acousticness"},
                    "avg_instrumentalness": {"$avg": "$instrumentalness"},
                    "avg_popularity": {"$avg": "$popularity"}
                }
            },
            {
                "$sort": {"_id": 1}
            }
        ])
        
        try:
            results = list(self._collection.aggregate(pipeline))
            return results
        except Exception as e:
            print(f"Error in get_cluster_stats: {e}")
            return []
    
    # Query 3: Mood-based search
    def search_by_mood(self, mood: str) -> List[Dict]:
        """
        Search tracks by mood profile
        
        Args:
            mood: Mood type ('happy', 'energetic', 'calm', 'sad', 'workout', 'chill')
        
        Returns:
            List of matching tracks
        """
        mood_profiles = {
            'happy': {
                'valence_min': 0.9,
                'energy_min': 0.7
            },
            'energetic': {
                'energy_min': 0.7,
                'tempo_min': 150
            },
            'calm': {
                'energy_max': 0.4,
                'valence_min': 0.3,
                'acousticness_min': 0.4
            },
            'sad': {
                'valence_max': 0.4,
                'energy_max': 0.5
            },
            'workout': {
                'energy_min': 0.8,
                'danceability_min': 0.6,
                'tempo_min': 120
            },
            'chill': {
                'energy_max': 0.5,
                'acousticness_min': 0.3,
                'instrumentalness_min': 0.3
            }
        }
        
        filters = mood_profiles.get(mood.lower(), {})
        if not filters:
            return []
        
        return self.search_by_features(filters)
    
    # Query 4: Producer reference tracks
    def find_reference_tracks(self, 
                            instrumentalness_min: float = 0.5,
                            speechiness_max: float = 0.3,
                            acousticness_range: tuple = (0.0, 1.0)) -> List[Dict]:
        """
        Find producer reference tracks based on production characteristics
        
        Args:
            instrumentalness_min: Minimum instrumentalness (default 0.5)
            speechiness_max: Maximum speechiness (default 0.3)
            acousticness_range: Tuple of (min, max) for acousticness
        
        Returns:
            List of matching tracks
        """
        query = {
            "instrumentalness": {"$gte": instrumentalness_min},
            "speechiness": {"$lte": speechiness_max},
            "acousticness": {
                "$gte": acousticness_range[0],
                "$lte": acousticness_range[1]
            }
        }
        
        try:
            results = list(self._collection.find(query)
                          .sort("popularity", DESCENDING)
                          .limit(50))
            return results
        except Exception as e:
            print(f"Error in find_reference_tracks: {e}")
            return []
    
    def get_track_by_id(self, track_id: str) -> Optional[Dict]:
        """Get single track by track_id"""
        try:
            return self._collection.find_one({"track_id": track_id})
        except Exception as e:
            print(f"Error in get_track_by_id: {e}")
            return None
    
    def get_tracks_by_ids(self, track_ids: List[str]) -> List[Dict]:
        """Get multiple tracks by track_ids"""
        try:
            results = list(self._collection.find({"track_id": {"$in": track_ids}}))
            return results
        except Exception as e:
            print(f"Error in get_tracks_by_ids: {e}")
            return []
    
    def get_dataset_stats(self) -> Dict:
        """Get overall dataset statistics"""
        try:
            total_tracks = self._collection.count_documents({})
            
            # Get cluster distribution
            cluster_pipeline = [
                {"$group": {"_id": "$cluster_id", "count": {"$sum": 1}}},
                {"$sort": {"_id": 1}}
            ]
            clusters = list(self._collection.aggregate(cluster_pipeline))
            
            # Get average audio features
            avg_pipeline = [
                {
                    "$group": {
                        "_id": None,
                        "avg_energy": {"$avg": "$energy"},
                        "avg_danceability": {"$avg": "$danceability"},
                        "avg_valence": {"$avg": "$valence"},
                        "avg_tempo": {"$avg": "$tempo"}
                    }
                }
            ]
            avg_features = list(self._collection.aggregate(avg_pipeline))
            
            return {
                "total_tracks": total_tracks,
                "clusters": clusters,
                "average_features": avg_features[0] if avg_features else {}
            }
        except Exception as e:
            print(f"Error in get_dataset_stats: {e}")
            return {}
