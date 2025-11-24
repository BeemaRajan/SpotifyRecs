"""
SpotifyRecs Flask API Application
Main entry point for the REST API
"""

from flask import Flask, jsonify
from flask_cors import CORS
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import database clients
from api.database.mongo_client import MongoDBClient
from api.database.neo4j_client import Neo4jClient

# Import routes
from api.routes.search import search_bp
from api.routes.clusters import clusters_bp
from api.routes.recommendations import recommendations_bp

# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key')

# Enable CORS
CORS(app)

# Initialize database clients (singleton pattern)
mongo_client = MongoDBClient()
neo4j_client = Neo4jClient()

# Register blueprints
app.register_blueprint(search_bp, url_prefix='/api')
app.register_blueprint(clusters_bp, url_prefix='/api')
app.register_blueprint(recommendations_bp, url_prefix='/api')


@app.route('/')
def home():
    """API home endpoint"""
    return jsonify({
        'message': 'SpotifyRecs API',
        'version': '1.0',
        'endpoints': [
            '/api/search',
            '/api/cluster/<id>',
            '/api/mood',
            '/api/recommend/<track_id>',
            '/api/stats'
        ]
    })


@app.route('/api/health')
def health():
    """Health check endpoint"""
    mongo_status = mongo_client.check_connection()
    neo4j_status = neo4j_client.check_connection()
    
    return jsonify({
        'status': 'healthy' if (mongo_status and neo4j_status) else 'degraded',
        'databases': {
            'mongodb': 'connected' if mongo_status else 'disconnected',
            'neo4j': 'connected' if neo4j_status else 'disconnected'
        }
    })


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({
        'error': 'Not found',
        'message': 'The requested endpoint does not exist'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    return jsonify({
        'error': 'Internal server error',
        'message': 'An unexpected error occurred'
    }), 500


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
