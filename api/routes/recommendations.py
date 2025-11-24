"""
Recommendations Routes
Handles recommendation endpoints (Neo4j Queries 5, 6, 7 and Hybrid Query 9)
"""

from flask import Blueprint, request, jsonify
from api.database.mongo_client import MongoDBClient
from api.database.neo4j_client import Neo4jClient

recommendations_bp = Blueprint('recommendations', __name__)
mongo_client = MongoDBClient()
neo4j_client = Neo4jClient()


@recommendations_bp.route('/recommend/<track_id>', methods=['GET'])
def recommend_tracks(track_id):
    """
    Get track recommendations using graph traversal (Hybrid Query 9)
    
    GET /api/recommend/<track_id>?hops=2&limit=20
    
    This is a hybrid query:
    1. Query Neo4j for similar track IDs (Query 5)
    2. Fetch full track details from MongoDB
    """
    try:
        # Get query parameters
        max_hops = int(request.args.get('hops', 2))
        limit = int(request.args.get('limit', 20))
        
        # Validate parameters
        if max_hops < 1 or max_hops > 3:
            return jsonify({
                'error': 'Invalid hops parameter',
                'message': 'hops must be between 1 and 3'
            }), 400
        
        # Get source track from MongoDB
        source_track = mongo_client.get_track_by_id(track_id)
        if not source_track:
            return jsonify({
                'error': 'Source track not found',
                'track_id': track_id
            }), 404
        
        # Query Neo4j for similar tracks (Query 5 - Graph Traversal)
        similar_tracks_neo4j = neo4j_client.find_similar_tracks(
            track_id=track_id,
            max_hops=max_hops,
            limit=limit
        )
        
        if not similar_tracks_neo4j:
            return jsonify({
                'source_track': {
                    'track_id': source_track.get('track_id'),
                    'title': source_track.get('title'),
                    'artist': source_track.get('artist')
                },
                'recommendations': [],
                'count': 0,
                'message': 'No similar tracks found'
            }), 200
        
        # Extract track IDs from Neo4j results
        similar_track_ids = [t['track_id'] for t in similar_tracks_neo4j]
        
        # Fetch full track details from MongoDB
        similar_tracks_full = mongo_client.get_tracks_by_ids(similar_track_ids)
        
        # Create a mapping for quick lookup
        tracks_map = {t['track_id']: t for t in similar_tracks_full}
        
        # Combine Neo4j scores with MongoDB track data
        recommendations = []
        for neo4j_track in similar_tracks_neo4j:
            track_id = neo4j_track['track_id']
            if track_id in tracks_map:
                track = tracks_map[track_id].copy()
                # Remove MongoDB _id
                if '_id' in track:
                    del track['_id']
                # Add similarity info from Neo4j
                track['similarity_score'] = round(neo4j_track['similarity_score'], 4)
                track['hops'] = neo4j_track['hops']
                recommendations.append(track)
        
        # Remove MongoDB _id from source track
        if '_id' in source_track:
            del source_track['_id']
        
        return jsonify({
            'source_track': {
                'track_id': source_track.get('track_id'),
                'title': source_track.get('title'),
                'artist': source_track.get('artist'),
                'energy': source_track.get('energy'),
                'danceability': source_track.get('danceability'),
                'valence': source_track.get('valence')
            },
            'parameters': {
                'max_hops': max_hops,
                'limit': limit
            },
            'count': len(recommendations),
            'recommendations': recommendations
        }), 200
        
    except ValueError:
        return jsonify({
            'error': 'Invalid parameter values',
            'message': 'hops and limit must be integers'
        }), 400
    except Exception as e:
        return jsonify({
            'error': 'Recommendation failed',
            'message': str(e)
        }), 500


@recommendations_bp.route('/triangles', methods=['GET'])
def find_triangles():
    """
    Find triangles of mutually similar tracks (Query 6)
    
    GET /api/triangles?min_similarity=0.7&limit=10
    """
    try:
        min_similarity = float(request.args.get('min_similarity', 0.7))
        limit = int(request.args.get('limit', 10))
        
        # Validate parameters
        if min_similarity < 0 or min_similarity > 1:
            return jsonify({
                'error': 'Invalid min_similarity',
                'message': 'min_similarity must be between 0 and 1'
            }), 400
        
        # Query Neo4j for triangles (Query 6)
        triangles = neo4j_client.find_similarity_triangles(
            min_similarity=min_similarity,
            limit=limit
        )
        
        return jsonify({
            'parameters': {
                'min_similarity': min_similarity,
                'limit': limit
            },
            'count': len(triangles),
            'triangles': triangles
        }), 200
        
    except ValueError:
        return jsonify({
            'error': 'Invalid parameter values',
            'message': 'Parameters must be valid numbers'
        }), 400
    except Exception as e:
        return jsonify({
            'error': 'Triangle search failed',
            'message': str(e)
        }), 500


@recommendations_bp.route('/centrality', methods=['GET'])
def get_centrality():
    """
    Get most influential tracks by network centrality (Query 7)
    
    GET /api/centrality?algorithm=degree&limit=20
    
    Supported algorithms: degree, pagerank
    """
    try:
        algorithm = request.args.get('algorithm', 'degree').lower()
        limit = int(request.args.get('limit', 20))
        
        # Validate algorithm
        if algorithm not in ['degree', 'pagerank']:
            return jsonify({
                'error': 'Invalid algorithm',
                'message': 'Supported algorithms: degree, pagerank'
            }), 400
        
        # Query Neo4j for centrality (Query 7)
        central_tracks_neo4j = neo4j_client.get_centrality_ranking(
            limit=limit,
            algorithm=algorithm
        )
        
        if not central_tracks_neo4j:
            return jsonify({
                'error': 'No results',
                'message': 'Centrality calculation failed or returned no results'
            }), 500
        
        # Extract track IDs
        track_ids = [t['track_id'] for t in central_tracks_neo4j]
        
        # Fetch full details from MongoDB
        tracks_full = mongo_client.get_tracks_by_ids(track_ids)
        tracks_map = {t['track_id']: t for t in tracks_full}
        
        # Combine Neo4j centrality with MongoDB details
        results = []
        for neo4j_track in central_tracks_neo4j:
            track_id = neo4j_track['track_id']
            if track_id in tracks_map:
                track = tracks_map[track_id].copy()
                if '_id' in track:
                    del track['_id']
                
                # Add centrality score
                if 'degree' in neo4j_track:
                    track['degree'] = neo4j_track['degree']
                    track['avg_similarity'] = round(neo4j_track.get('avg_similarity', 0), 4)
                elif 'score' in neo4j_track:
                    track['pagerank_score'] = round(neo4j_track['score'], 6)
                
                results.append(track)
        
        return jsonify({
            'algorithm': algorithm,
            'count': len(results),
            'tracks': results
        }), 200
        
    except ValueError:
        return jsonify({
            'error': 'Invalid limit value',
            'message': 'limit must be an integer'
        }), 400
    except Exception as e:
        return jsonify({
            'error': 'Centrality ranking failed',
            'message': str(e)
        }), 500


@recommendations_bp.route('/similar/<track_id>', methods=['GET'])
def get_similar_neighbors(track_id):
    """
    Get direct neighbors (1-hop similar tracks)
    
    GET /api/similar/<track_id>?limit=10
    """
    try:
        limit = int(request.args.get('limit', 10))
        
        # Get source track
        source_track = mongo_client.get_track_by_id(track_id)
        if not source_track:
            return jsonify({
                'error': 'Track not found',
                'track_id': track_id
            }), 404
        
        # Get neighbors from Neo4j
        neighbors = neo4j_client.get_track_neighbors(track_id, limit)
        
        if not neighbors:
            return jsonify({
                'source_track': source_track.get('title'),
                'similar_tracks': [],
                'count': 0
            }), 200
        
        # Fetch full details from MongoDB
        neighbor_ids = [n['track_id'] for n in neighbors]
        tracks_full = mongo_client.get_tracks_by_ids(neighbor_ids)
        tracks_map = {t['track_id']: t for t in tracks_full}
        
        # Combine data
        similar_tracks = []
        for neighbor in neighbors:
            track_id = neighbor['track_id']
            if track_id in tracks_map:
                track = tracks_map[track_id].copy()
                if '_id' in track:
                    del track['_id']
                track['similarity_score'] = round(neighbor['similarity_score'], 4)
                similar_tracks.append(track)
        
        if '_id' in source_track:
            del source_track['_id']
        
        return jsonify({
            'source_track': {
                'track_id': source_track.get('track_id'),
                'title': source_track.get('title'),
                'artist': source_track.get('artist')
            },
            'count': len(similar_tracks),
            'similar_tracks': similar_tracks
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to get similar tracks',
            'message': str(e)
        }), 500
