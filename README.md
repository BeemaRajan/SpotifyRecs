# SpotifyRecs: Hybrid NoSQL Music Recommendation System

A music recommendation system using MongoDB and Neo4j, built with Flask REST API and powered by machine learning.

## Project Overview

This project implements a hybrid recommendation system that combines:
- **MongoDB**: Stores track metadata and audio features
- **Neo4j**: Manages similarity graph for relationship-based recommendations
- **Flask API**: Provides REST endpoints for querying
- **ML Pipeline**: UMAP dimensionality reduction + K-means clustering

## Architecture

```
┌─────────────────┐
│  Spotify API    │
└────────┬────────┘
         │ (Data Collection)
         ▼
┌─────────────────┐
│  ML Processing  │ ◄── Google Colab/Local Processing
│  (UMAP+K-means) │
└────────┬────────┘
         │
         ├──────────────┬────────────────┐
         ▼              ▼                ▼
   ┌─────────┐    ┌─────────┐    ┌──────────┐
   │ MongoDB │    │  Neo4j  │    │ Flask API│
   │ (Tracks)│◄───┤ (Graph) │◄───┤(Queries) │
   └─────────┘    └─────────┘    └──────────┘
```

## Features

### Database Capabilities
- **MongoDB**: 5,000+ tracks with 13 audio features + cluster assignments
- **Neo4j**: Similarity graph with ~75,000 SIMILAR_TO relationships

### Query Types (9 total)
#### MongoDB (4 queries)
1. Range queries on audio features
2. Aggregation pipeline for cluster statistics
3. Mood-based search
4. Producer reference track finder

#### Neo4j (3 queries)
5. Graph traversal for similar tracks (N-hops)
6. Triangle pattern matching for mutually similar tracks
7. Network centrality ranking

#### Hybrid (2 queries)
8. Cluster navigation (Neo4j → MongoDB)
9. Recommendation engine (Neo4j + MongoDB)

### REST API Endpoints
1. `GET /api/search` - Find tracks by audio features
2. `GET /api/cluster/<id>` - Get cluster details
3. `GET /api/mood` - Mood-based recommendations
4. `GET /api/recommend/<track_id>` - Hybrid recommendations
5. `GET /api/stats` - Dataset statistics

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Spotify Developer Account (for data collection)

### 1. Clone and Setup

```bash
git clone https://github.com/BeemaRajan/no_sql_music_recs.git
cd SpotifyRecs

# Create environment file
cp .env.example .env
# Edit .env with your Spotify credentials
```

### 2. Start Services

```bash
# Start MongoDB, Neo4j, and Flask API
docker-compose up -d

# Check services are running
docker-compose ps -a
```

Services will be available at:
- **MongoDB**: `localhost:27017`
- **Neo4j Browser**: `http://localhost:7474` (neo4j/password123)
- **Flask API**: `http://localhost:5000`

### 3. Data Collection

```bash
# Install Python dependencies locally (for data collection)
pip install -r requirements.txt

# Run Spotify data collector
python data_collection/spotify_collector.py
```

### 4. ML Processing

Option A: Google Colab
1. Upload `ml_processing/audio_features_ml.ipynb` to Colab
2. Upload collected data
3. Run all cells
4. Download processed files

Option B: Local
```bash
jupyter notebook ml_processing/audio_features_ml.ipynb
```

### 5. Load Databases

```bash
# Load MongoDB
python database_setup/load_mongo.py

# Load Neo4j
python database_setup/load_neo4j.py
```

### 6. Test API

```bash
# Health check
curl http://localhost:5000/api/health

# Search high-energy tracks
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{"energy_min": 0.7, "tempo_min": 120}'
```

## Project Structure

```
SpotifyRecs/
├── api/
│   ├── app.py                 # Flask application
│   ├── routes/
│   │   ├── search.py          # Search endpoints
│   │   ├── clusters.py        # Cluster endpoints
│   │   └── recommendations.py # Recommendation endpoints
│   ├── database/
│   │   ├── mongo_client.py    # MongoDB connection
│   │   └── neo4j_client.py    # Neo4j connection
│   └── utils/
│       └── query_helpers.py   # Query utilities
├── data_collection/
│   ├── spotify_collector.py   # Spotify API collector
│   └── playlists.json         # Target playlists
├── ml_processing/
│   ├── audio_features_ml.ipynb # ML pipeline notebook
│   └── similarity_calculator.py # Similarity computation
├── database_setup/
│   ├── load_mongo.py          # MongoDB loader
│   ├── load_neo4j.py          # Neo4j loader
│   └── init_scripts/
│       ├── mongo_indexes.js   # MongoDB indexes
│       └── neo4j_constraints.cypher # Neo4j constraints
├── data/
│   ├── raw/                   # Raw Spotify data
│   ├── processed/             # Processed with ML features
│   └── sample/                # Sample data for testing
├── tests/
│   ├── test_api.py            # API tests
│   ├── test_mongo_queries.py # MongoDB query tests
│   └── test_neo4j_queries.py # Neo4j query tests
├── docs/
│   ├── API.md                 # API documentation
│   ├── QUERIES.md             # Query examples
│   └── screenshots/           # Demo screenshots
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── .env.example
└── README.md
```

## API Documentation

See [API.md](docs/API.md) for detailed endpoint documentation.

### Example: Search by Audio Features

```bash
POST /api/search
{
  "energy_min": 0.7,
  "energy_max": 1.0,
  "danceability_min": 0.6,
  "tempo_min": 120,
  "tempo_max": 140
}

Response:
{
  "results": [
    {
      "track_id": "spotify:track:xyz",
      "title": "Upbeat Song",
      "artist": "Artist Name",
      "energy": 0.85,
      "danceability": 0.75,
      "tempo": 128,
      "cluster_id": 3
    }
  ],
  "count": 42
}
```

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_api.py

# With coverage
pytest --cov=api tests/
```

### Useful Commands

```bash
# View logs
docker-compose logs -f flask-api

# Restart a service
docker-compose restart flask-api

# Access MongoDB shell
docker exec -it spotifyrecs-mongodb mongosh -u admin -p password123

# Access Neo4j Cypher shell
docker exec -it spotifyrecs-neo4j cypher-shell -u neo4j -p password123

# Stop all services
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v
```

## Query Examples

### MongoDB Queries

```python
# 1. Range query
db.tracks.find({
    "energy": {"$gte": 0.7, "$lte": 1.0},
    "danceability": {"$gte": 0.6},
    "tempo": {"$gte": 120, "$lte": 140}
})

# 2. Aggregation by cluster
db.tracks.aggregate([
    {"$group": {
        "_id": "$cluster_id",
        "avg_energy": {"$avg": "$energy"},
        "avg_danceability": {"$avg": "$danceability"},
        "count": {"$sum": 1}
    }}
])
```

### Neo4j Queries

```cypher
// 5. Find similar tracks (2-hop traversal)
MATCH path = (t:Track {track_id: 'spotify:track:xyz'})-[:SIMILAR_TO*1..2]-(similar:Track)
RETURN similar, length(path) as hops
ORDER BY hops, similar.popularity DESC
LIMIT 20

// 6. Find triangles of mutually similar tracks
MATCH (a:Track)-[:SIMILAR_TO]-(b:Track)-[:SIMILAR_TO]-(c:Track)-[:SIMILAR_TO]-(a)
RETURN a, b, c
LIMIT 10

// 7. Network centrality
CALL gds.pageRank.stream('track-similarity-graph')
YIELD nodeId, score
RETURN gds.util.asNode(nodeId).title as track, score
ORDER BY score DESC
LIMIT 20
```

## Dataset

- **Size**: 5,000-7,000 tracks
- **Audio Features**: 13 features per track (energy, danceability, valence, tempo, etc.)
- **ML Features**: 2D UMAP embeddings, cluster assignments
- **Graph Edges**: ~75,000 similarity relationships (top 10-15 per track)

## Technologies

- **Databases**: MongoDB 7.0, Neo4j 5.15
- **API**: Flask 3.0, Python 3.11
- **ML**: scikit-learn, UMAP, pandas, numpy
- **Data Source**: Spotify Web API
- **Deployment**: Docker Compose

## Troubleshooting

### MongoDB connection issues
```bash
# Check MongoDB is running
docker-compose ps mongodb

# View MongoDB logs
docker-compose logs mongodb

# Test connection
mongosh "mongodb://admin:password123@localhost:27017/spotifyrecs?authSource=admin"
```

### Neo4j connection issues
```bash
# Check Neo4j is running
docker-compose ps neo4j

# View Neo4j logs
docker-compose logs neo4j

# Access Neo4j browser
open http://localhost:7474
```

### API not starting
```bash
# Check Flask logs
docker-compose logs flask-api

# Rebuild Flask container
docker-compose build flask-api
docker-compose up -d flask-api
```

## Contributors

- [Your Name]

## License

MIT License

## Acknowledgments

- Spotify Web API for audio features
- DS5760 NoSQL Course