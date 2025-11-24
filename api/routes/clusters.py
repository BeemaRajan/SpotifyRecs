"""
Clusters Routes
Handles cluster-related endpoints (MongoDB Query 2, Hybrid Query 8)
"""

from flask import Blueprint, jsonify
from api.database.mongo_client import MongoDBClient
from api.database.neo4j_client import Neo4jClient

clusters_bp = Blueprint('clusters', __name__)
mongo_client = MongoDBClient()
neo4j_client = Neo4jClient()


@clusters_bp.route('/cluster/<int:cluster_id>', methods=['GET'])
def get_cluster(cluster_id):
    """
    Get cluster details with statistics (Query 2) and track list (Hybrid Query 8)
    
    GET /api/cluster/<cluster_id>
    """
    try:
        # Get cluster statistics from MongoDB (Query 2)
        cluster_stats = mongo_client.get_cluster_stats(cluster_id)
        
        if not cluster_stats:
            return jsonify({
                'error': 'Cluster not found',
                'cluster_id': cluster_id
            }), 404
        
        stats = cluster_stats[0]
        
        # Get track IDs from Neo4j (Hybrid Query 8 - part 1)
        track_ids = neo4j_client.get_cluster_track_ids(cluster_id)
        
        # Fetch full track details from MongoDB (Hybrid Query 8 - part 2)
        tracks = mongo_client.get_tracks_by_ids(track_ids)
        
        # Remove MongoDB _id from tracks
        for track in tracks:
            if '_id' in track:
                del track['_id']
        
        # Remove MongoDB _id from stats
        if '_id' in stats:
            del stats['_id']
        
        return jsonify({
            'cluster_id': cluster_id,
            'statistics': stats,
            'track_count': len(tracks),
            'tracks': tracks[:20]  # Return first 20 tracks
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to retrieve cluster',
            'message': str(e)
        }), 500


@clusters_bp.route('/clusters', methods=['GET'])
def get_all_clusters():
    """
    Get all cluster statistics (Query 2 - all clusters)
    
    GET /api/clusters
    """
    try:
        cluster_stats = mongo_client.get_cluster_stats()
        
        # Remove MongoDB _id from each cluster
        for stats in cluster_stats:
            if '_id' in stats:
                cluster_id = stats.pop('_id')
                stats['cluster_id'] = cluster_id
        
        return jsonify({
            'cluster_count': len(cluster_stats),
            'clusters': cluster_stats
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to retrieve clusters',
            'message': str(e)
        }), 500


@clusters_bp.route('/stats', methods=['GET'])
def get_dataset_stats():
    """
    Get overall dataset statistics (MongoDB + Neo4j)
    
    GET /api/stats
    """
    try:
        # Get MongoDB stats
        mongo_stats = mongo_client.get_dataset_stats()
        
        # Get Neo4j stats
        neo4j_stats = neo4j_client.get_graph_stats()
        
        # Combine statistics
        combined_stats = {
            'mongodb': {
                'total_tracks': mongo_stats.get('total_tracks', 0),
                'clusters': mongo_stats.get('clusters', []),
                'average_features': mongo_stats.get('average_features', {})
            },
            'neo4j': {
                'total_nodes': neo4j_stats.get('total_tracks', 0),
                'total_relationships': neo4j_stats.get('total_relationships', 0),
                'average_degree': round(neo4j_stats.get('avg_degree', 0), 2),
                'cluster_distribution': neo4j_stats.get('clusters', [])
            }
        }
        
        return jsonify(combined_stats), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to retrieve dataset statistics',
            'message': str(e)
        }), 500
