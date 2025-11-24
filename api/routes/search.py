"""
Search Routes
Handles track search endpoints (MongoDB Query 1, 3, 4)
"""

from flask import Blueprint, request, jsonify
from api.database.mongo_client import MongoDBClient

search_bp = Blueprint('search', __name__)
mongo_client = MongoDBClient()


@search_bp.route('/search', methods=['POST'])
def search_tracks():
    """
    Search tracks by audio feature ranges (Query 1)
    
    POST /api/search
    Body: {
        "energy_min": 0.7,
        "energy_max": 1.0,
        "danceability_min": 0.6,
        "tempo_min": 120,
        "tempo_max": 140,
        "cluster_id": 3  // optional
    }
    """
    try:
        filters = request.get_json()
        
        if not filters:
            return jsonify({
                'error': 'No search filters provided',
                'example': {
                    'energy_min': 0.7,
                    'danceability_min': 0.6,
                    'tempo_min': 120
                }
            }), 400
        
        results = mongo_client.search_by_features(filters)
        
        # Remove MongoDB _id from results
        for track in results:
            if '_id' in track:
                del track['_id']
        
        return jsonify({
            'count': len(results),
            'filters': filters,
            'results': results
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Search failed',
            'message': str(e)
        }), 500


@search_bp.route('/mood', methods=['GET'])
def search_by_mood():
    """
    Search tracks by mood profile (Query 3)
    
    GET /api/mood?mood=happy
    
    Supported moods: happy, energetic, calm, sad, workout, chill
    """
    try:
        mood = request.args.get('mood', '').lower()
        
        if not mood:
            return jsonify({
                'error': 'Mood parameter required',
                'supported_moods': ['happy', 'energetic', 'calm', 'sad', 'workout', 'chill']
            }), 400
        
        results = mongo_client.search_by_mood(mood)
        
        if not results:
            return jsonify({
                'error': f'Invalid mood: {mood}',
                'supported_moods': ['happy', 'energetic', 'calm', 'sad', 'workout', 'chill']
            }), 400
        
        # Remove MongoDB _id from results
        for track in results:
            if '_id' in track:
                del track['_id']
        
        return jsonify({
            'mood': mood,
            'count': len(results),
            'results': results
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Mood search failed',
            'message': str(e)
        }), 500


@search_bp.route('/reference', methods=['GET'])
def find_reference_tracks():
    """
    Find producer reference tracks (Query 4)
    
    GET /api/reference?instrumentalness_min=0.5&speechiness_max=0.3
    """
    try:
        # Get query parameters with defaults
        instrumentalness_min = float(request.args.get('instrumentalness_min', 0.5))
        speechiness_max = float(request.args.get('speechiness_max', 0.3))
        acousticness_min = float(request.args.get('acousticness_min', 0.0))
        acousticness_max = float(request.args.get('acousticness_max', 1.0))
        
        results = mongo_client.find_reference_tracks(
            instrumentalness_min=instrumentalness_min,
            speechiness_max=speechiness_max,
            acousticness_range=(acousticness_min, acousticness_max)
        )
        
        # Remove MongoDB _id from results
        for track in results:
            if '_id' in track:
                del track['_id']
        
        return jsonify({
            'count': len(results),
            'filters': {
                'instrumentalness_min': instrumentalness_min,
                'speechiness_max': speechiness_max,
                'acousticness_range': [acousticness_min, acousticness_max]
            },
            'results': results
        }), 200
        
    except ValueError:
        return jsonify({
            'error': 'Invalid parameter values',
            'message': 'All parameters must be numbers between 0 and 1'
        }), 400
    except Exception as e:
        return jsonify({
            'error': 'Reference track search failed',
            'message': str(e)
        }), 500


@search_bp.route('/track/<track_id>', methods=['GET'])
def get_track(track_id):
    """
    Get single track by ID
    
    GET /api/track/<track_id>
    """
    try:
        track = mongo_client.get_track_by_id(track_id)
        
        if not track:
            return jsonify({
                'error': 'Track not found',
                'track_id': track_id
            }), 404
        
        # Remove MongoDB _id
        if '_id' in track:
            del track['_id']
        
        return jsonify(track), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to retrieve track',
            'message': str(e)
        }), 500
