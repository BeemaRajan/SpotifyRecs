# SpotifyRecs: Hybrid NoSQL Music Recommendation System

A music recommendation system that combines MongoDB and Neo4j databases, powered by machine learning, and exposed through a Flask REST API with an interactive Streamlit frontend.

## Table of Contents

- [Overview](#overview)
- [Dataset](#dataset)
- [System Architecture](#system-architecture)
- [How It Works](#how-it-works)
- [Features](#features)
- [Technologies](#technologies)
- [Prerequisites](#prerequisites)
- [Quick Start Guide](#quick-start-guide)
- [Complete Setup Instructions](#complete-setup-instructions)
- [Project Structure](#project-structure)
- [API Documentation](#api-documentation)
- [Query Examples](#query-examples)
- [Frontend Interface](#frontend-interface)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)
- [Development](#development)
- [Contributors](#contributors)
- [Additional Resources](#additional-resources)

---

## Overview

SpotifyRecs is a hybrid recommendation system that demonstrates the power of combining document-based and graph databases for music discovery. The system implements 9 distinct query types across MongoDB, Neo4j, and hybrid approaches to provide comprehensive music recommendations based on audio features, similarity relationships, and clustering.

### Key Capabilities

- **Dual Database Architecture**: MongoDB for flexible document storage, Neo4j for relationship-based queries
- **Machine Learning Pipeline**: UMAP dimensionality reduction + K-means clustering for intelligent track grouping
- **Graph-Based Similarity**: Cosine similarity network enabling multi-hop recommendations
- **9 Query Types**: 4 MongoDB, 3 Neo4j, and 2 hybrid queries
- **REST API**: Flask-based API with 11 endpoints
- **Interactive Frontend**: Streamlit multi-page application for exploring all query types
- **Dockerized**: Fully containerized with Docker Compose for easy deployment

---

## Dataset

The SpotifyRecs system uses Spotify track data with comprehensive audio features extracted via the Spotify Web API. The dataset can be sourced either from the Spotify API directly or from a pre-collected Kaggle dataset, containing between 1,500 to 7,000 tracks depending on the data collection method.

### Audio Features

Each track in the dataset includes 13 audio features that characterize its sonic properties:

#### Perceptual Features (0.0 - 1.0 scale)

- **Energy**: Represents the intensity and activity of a track. High energy tracks feel fast, loud, and noisy (e.g., death metal), while low energy tracks are more calm and subdued (e.g., Bach prelude).

- **Danceability**: Describes how suitable a track is for dancing based on musical elements including tempo, rhythm stability, beat strength, and overall regularity. Values near 1.0 indicate highly danceable tracks.

- **Valence**: Measures the musical positiveness conveyed by a track. High valence tracks sound more positive (happy, cheerful, euphoric), while low valence tracks sound more negative (sad, depressed, angry).

- **Acousticness**: A confidence measure of whether the track is acoustic. Values near 1.0 represent high confidence that the track is acoustic (e.g., unplugged performances, classical music).

- **Instrumentalness**: Predicts whether a track contains no vocals. Values above 0.5 indicate instrumental tracks, with values closer to 1.0 having higher confidence (e.g., classical music, electronic beats).

- **Liveness**: Detects the presence of an audience in the recording. Higher values indicate an increased probability that the track was performed live. Values above 0.8 strongly suggest a live recording.

- **Speechiness**: Detects the presence of spoken words in a track. Values above 0.66 indicate tracks made entirely of spoken words (e.g., podcasts, audiobooks), values between 0.33-0.66 may contain both music and speech (e.g., rap music), and values below 0.33 represent music and other non-speech tracks.

#### Technical Features

- **Tempo**: The overall estimated tempo of a track in beats per minute (BPM). Typical values range from 50 to 200 BPM.

- **Loudness**: The overall loudness of a track in decibels (dB). Values typically range from -60 to 0 dB, with most popular music falling between -15 and -5 dB.

- **Key**: The key the track is in using standard Pitch Class notation (0 = C, 1 = C♯/D♭, 2 = D, etc.). Values range from 0 to 11.

- **Mode**: Indicates the modality (major or minor) of a track. Major is represented by 1 and minor by 0.

- **Time Signature**: An estimated time signature ranging from 3 to 7, representing how many beats are in each bar (e.g., 4 = 4/4 time).

### Additional Track Metadata

Beyond audio features, each track includes:
- **Track ID**: Spotify's unique identifier
- **Title**: Song name
- **Artist**: Artist name(s)
- **Album**: Album name
- **Popularity**: Spotify's popularity score (0-100)
- **Cluster ID**: Machine learning-assigned cluster (0-9 by default)
- **UMAP Coordinates**: 2D embedding coordinates (umap_x, umap_y) for visualization

---

## System Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                     DATA COLLECTION                          │
│  ┌─────────────────┐          ┌────────────────────┐         │
│  │  Spotify API    │   OR     │  Kaggle Dataset    │         │
│  │ (Custom Lists)  │          │  (Pre-collected)   │         │
│  └────────┬────────┘          └─────────┬──────────┘         │
│           └───────────────┬──────────────┘                   │
│                           │                                  │
│                    tracks.json                               │
└───────────────────────────┼──────────────────────────────────┘
                            ▼
┌──────────────────────────────────────────────────────────────┐
│                   ML PROCESSING PIPELINE                     │
│                                                              │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐    │
│  │ Normalization│ -> │ UMAP Reduc.  │ -> │  K-means     │    │
│  │ (13 features)│    │ (2D embed.)  │    │ Clustering   │    │
│  └──────────────┘    └──────────────┘    └──────────────┘    │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐    │
│  │     Cosine Similarity Calculation (Top-N pairs)      │    │
│  └──────────────────────────────────────────────────────┘    │
└──────────┬────────────────┬──────────────────┬───────────────┘
           │                │                  │
           ▼                ▼                  ▼
   tracks_with_    neo4j_nodes.json   neo4j_edges.json
   clusters.json
           │                │                  │
┌──────────┼────────────────┼──────────────────┼──────────────┐
│          │                │                  │              │
│   ┌──────▼──────┐    ┌────▼──────────────────▼───┐          │
│   │   MongoDB   │    │         Neo4j             │          │
│   │             │    │                           │          │
│   │  • Tracks   │◄───┤  • Track Nodes            │          │
│   │  • Features │    │  • SIMILAR_TO Edges       │          │
│   │  • Clusters │    │  • Similarity Scores      │          │
│   └──────▲──────┘    └────▲──────────────────────┘          │
│          │                │                                 │
│          └────────┬───────┘                                 │
│                   │                                         │
└───────────────────┼─────────────────────────────────────────┘
                    │
┌───────────────────┼─────────────────────────────────────────┐
│                   │    FLASK REST API                       │
│   ┌───────────────▼─────────────────────────────┐           │
│   │  Routes:                                    │           │
│   │  • Search (MongoDB queries)                 │           │
│   │  • Clusters (MongoDB aggregations)          │           │
│   │  • Recommendations (Neo4j + MongoDB hybrid) │           │
│   └───────────────┬─────────────────────────────┘           │
│                   │                                         │
│   ┌───────────────┴─────────────────────────────┐           │
│   │  Database Clients (Singleton Pattern):      │           │
│   │  • MongoDBClient                            │           │
│   │  • Neo4jClient                              │           │
│   └─────────────────────────────────────────────┘           │
└───────────────────┬─────────────────────────────────────────┘
                    │
┌───────────────────┼─────────────────────────────────────────┐
│                   │    STREAMLIT FRONTEND                   │
│   ┌───────────────▼─────────────────────────────┐           │
│   │  Multi-page App:                            │           │
│   │  • Home Dashboard                           │           │
│   │  • MongoDB Queries (4 types)                │           │
│   │  • Neo4j Queries (3 types)                  │           │
│   │  • Hybrid Queries (2 types)                 │           │
│   └─────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

---

## How It Works

### 1. Data Collection Phase

**Option A: Spotify API** ([spotify_collector.py](data_collection/spotify_collector.py))
- Authenticates with Spotify using OAuth
- Collects tracks from specified playlists
- Fetches 13 audio features per track:
  - Energy, danceability, valence, tempo
  - Acousticness, instrumentalness, liveness
  - Loudness, speechiness, key, mode, time signature
- Outputs: `data/raw/tracks.json`

**Option B: Kaggle Dataset** ([kaggle_conversion.py](data_collection/kaggle_conversion.py))
- Converts pre-collected CSV to JSON format
- Dataset: 1,556 tracks with all audio features
- No API credentials required
- Outputs: `data/raw/tracks.json`

### 2. ML Processing Phase

**ML Pipeline** ([audio_features_ml.py](ml_processing/audio_features_ml.py))

```python
# Key components:
class AudioFeatureProcessor:
    - load_data()            # Load raw tracks
    - normalize_features()   # StandardScaler normalization
    - reduce_dimensions()    # UMAP: 13D -> 2D
    - cluster_tracks()       # K-means clustering (default: 10 clusters)
    - calculate_similarity() # Cosine similarity on original features
    - create_graph_data()    # Top-N similar tracks per track
```

**Process Flow**:
1. **Normalization**: StandardScaler on 13 audio features
2. **Dimensionality Reduction**: UMAP reduces to 2D embeddings
3. **Clustering**: K-means groups tracks into sonic clusters
4. **Similarity**: Calculates pairwise cosine similarity
5. **Graph Construction**: Keeps top N most similar tracks per track (default: 15)

**Outputs**:
- `data/processed/tracks_with_clusters.json` - MongoDB data
- `data/processed/neo4j_nodes.json` - Track nodes for Neo4j
- `data/processed/neo4j_edges.json` - Similarity relationships

### 3. Database Loading Phase

**MongoDB Loader** ([load_mongo.py](database_setup/load_mongo.py))
- Connects using singleton pattern ([mongo_client.py](api/database/mongo_client.py))
- Loads tracks with cluster assignments
- Creates indexes on:
  - `track_id` (unique)
  - `cluster_id`
  - Audio features (energy, danceability, etc.)
- Collection: `spotifyrecs.tracks`

**Neo4j Loader** ([load_neo4j.py](database_setup/load_neo4j.py))
- Connects using singleton pattern ([neo4j_client.py](api/database/neo4j_client.py))
- Creates Track nodes with properties
- Creates SIMILAR_TO relationships with similarity scores
- Batched insertion for performance (~1000 records per batch)

### 4. API Layer

**Flask Application** ([app.py](api/app.py))
- Initializes MongoDB and Neo4j clients (singletons)
- Registers three blueprint modules:
  - **search** ([search.py](api/routes/search.py)): Range queries, mood search, reference tracks
  - **clusters** ([clusters.py](api/routes/clusters.py)): Cluster stats and navigation
  - **recommendations** ([recommendations.py](api/routes/recommendations.py)): Graph traversal, triangles, centrality

**How Hybrid Queries Work**:
```python
# Example: Recommendation endpoint
def recommend_tracks(track_id):
    # Step 1: Query Neo4j for similar track IDs via graph traversal
    similar_ids = neo4j_client.find_similar_tracks(track_id, max_hops=2)

    # Step 2: Fetch full track details from MongoDB
    full_tracks = mongo_client.get_tracks_by_ids(similar_ids)

    # Step 3: Combine and return
    return jsonify(recommendations=full_tracks)
```

### 5. Frontend Layer

**Streamlit App** ([streamlit_app.py](frontend/streamlit_app.py))
- Multi-page application with sidebar navigation
- Pages:
  - **Home**: Dashboard with DB connection status and stats
  - **MongoDB Queries**: Interactive forms for all 4 MongoDB query types
  - **Neo4j Queries**: Graph visualizations and 3 Neo4j query types
  - **Hybrid Queries**: Cluster navigation and recommendations
- Features: Sliders, dropdowns, charts, data tables, CSV export

---

## Features

### Database Capabilities

**MongoDB** (Document Store)
- **Collection**: `spotifyrecs.tracks`
- **Documents**: ~1,500-7,000 tracks (depending on data source)
- **Fields**:
  - Track metadata (id, title, artist, album, popularity)
  - Audio features (13 features)
  - ML features (cluster_id, umap_x, umap_y)
- **Indexes**: track_id (unique), cluster_id, audio features
- **Use Cases**: Range queries, aggregations, mood-based search

**Neo4j** (Graph Database)
- **Nodes**: Track nodes with properties (track_id, title, artist, cluster_id)
- **Relationships**: SIMILAR_TO with similarity score property
- **Graph Size**: ~1,500-7,000 nodes, ~22,000-100,000 edges
- **Use Cases**: Graph traversal, pattern matching, centrality analysis

### Query Types (9 Total)

#### MongoDB Queries (4)

1. **Range Query on Audio Features**
   - Search tracks by min/max values on multiple features
   - Example: High-energy dance tracks with high BPM
   - Implementation: MongoDB find() with $gte/$lte operators

2. **Aggregation Pipeline for Cluster Statistics**
   - Calculate average features per cluster
   - Group by cluster_id, compute count and averages
   - Implementation: MongoDB aggregate() with $group

3. **Mood-Based Search**
   - Pre-defined mood profiles (happy, energetic, calm, sad, workout, chill)
   - Maps moods to audio feature ranges
   - Example: Happy = high valence + moderate energy

4. **Producer Reference Tracks**
   - Find tracks by production characteristics
   - Filters: instrumentalness, speechiness, acousticness
   - Use case: Music producers finding reference tracks

#### Neo4j Queries (3)

5. **Graph Traversal for Similar Tracks**
   - Multi-hop traversal (1-3 hops) via SIMILAR_TO relationships
   - Calculates path scores (product of similarity scores)
   - Returns tracks sorted by similarity and hop distance
   - Implementation: Cypher MATCH with variable-length paths

6. **Triangle Pattern Matching**
   - Finds triplets of mutually similar tracks
   - Pattern: (a)-[:SIMILAR_TO]-(b)-[:SIMILAR_TO]-(c)-[:SIMILAR_TO]-(a)
   - Filters by minimum similarity threshold
   - Use case: Discovering tight clusters of similar tracks

7. **Network Centrality Ranking**
   - Ranks tracks by importance in similarity network
   - Algorithms:
     - **Degree Centrality**: Count of SIMILAR_TO relationships
     - **PageRank**: (if GDS plugin available) Weighted influence score
   - Use case: Finding "hub" tracks that connect many others

#### Hybrid Queries (2)

8. **Cluster Navigation**
   - Query Neo4j for track IDs in a cluster
   - Fetch full track details from MongoDB
   - Combines graph filtering with document retrieval

9. **Recommendation Engine**
   - Query Neo4j for similar tracks via graph traversal
   - Fetch full track metadata from MongoDB
   - Combines queries 5 (graph traversal) with MongoDB lookups
   - Primary recommendation algorithm for the system

### REST API Endpoints (11 Total)

| Endpoint | Method | Description | Query Type |
|----------|--------|-------------|------------|
| `/` | GET | API home and endpoint list | - |
| `/api/health` | GET | Health check and DB status | - |
| `/api/search` | POST | Range query on audio features | MongoDB #1 |
| `/api/clusters` | GET | All cluster statistics | MongoDB #2 |
| `/api/cluster/<id>` | GET | Specific cluster details | Hybrid #8 |
| `/api/mood` | GET | Mood-based search | MongoDB #3 |
| `/api/reference` | GET | Producer reference tracks | MongoDB #4 |
| `/api/track/<id>` | GET | Single track details | - |
| `/api/recommend/<id>` | GET | Graph-based recommendations | Hybrid #9 |
| `/api/triangles` | GET | Similarity triangles | Neo4j #6 |
| `/api/centrality` | GET | Network centrality ranking | Neo4j #7 |
| `/api/similar/<id>` | GET | Direct neighbors (1-hop) | Neo4j #5 |
| `/api/stats` | GET | Overall dataset statistics | - |

---

## Technologies

### Core Stack

- **Databases**:
  - MongoDB 7.0+ (Document store)
  - Neo4j 5.15+ (Graph database with APOC and GDS plugins)
- **Backend**:
  - Python 3.11+
  - Flask 3.0 (REST API)
  - PyMongo 4.6 (MongoDB client)
  - Neo4j Python Driver 5.15 (Graph client)
- **Machine Learning**:
  - scikit-learn 1.3 (K-means, StandardScaler)
  - UMAP 0.5 (Dimensionality reduction)
  - NumPy, Pandas (Data processing)
- **Data Collection**:
  - Spotipy 2.23 (Spotify Web API wrapper)
  - Kaggle dataset (Alternative source)
- **Frontend**:
  - Streamlit 1.29 (Interactive UI)
  - Plotly 5.18 (Visualizations)
- **Infrastructure**:
  - Docker & Docker Compose
  - Python dotenv (Configuration)

### Development Tools

- pytest 7.4 (Testing)
- pytest-cov 4.1 (Coverage)
- Flask-CORS 4.0 (Cross-origin requests)

---

## Prerequisites

Before you begin, ensure you have:

1. **Docker Desktop** (Required)
   - Download: https://www.docker.com/products/docker-desktop
   - Minimum 4GB RAM allocated to Docker
   - Used for: MongoDB, Neo4j, Flask API, Streamlit containers

2. **Python 3.11+** (Required)
   - Download: https://www.python.org/downloads/
   - Verify: `python --version`
   - Used for: Data collection, ML processing, database loading

3. **Git** (Optional but recommended)
   - Download: https://git-scm.com/downloads
   - Used for: Cloning the repository

4. **Spotify Developer Account** (Optional - only for Spotify API data collection)
   - Sign up: https://developer.spotify.com/dashboard
   - Alternative: Use Kaggle dataset instead

5. **Kaggle Account** (Optional - only if using Kaggle dataset)
   - Sign up: https://www.kaggle.com/
   - Dataset: https://www.kaggle.com/datasets/julianoorlandi/spotify-top-songs-and-audio-features

---

## Quick Start Guide

### 5-Minute Setup (Using Kaggle Dataset)

```bash
# 1. Clone repository
git clone https://github.com/BeemaRajan/no_sql_music_recs.git
cd SpotifyRecs

# 2. Start Docker services
docker-compose up -d

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Download Kaggle dataset
# Visit: https://www.kaggle.com/datasets/julianoorlandi/spotify-top-songs-and-audio-features
# Download spotify_top_songs_audio_features.csv
# Place in: data/raw/

# 5. Convert CSV to JSON
python data_collection/kaggle_conversion.py

# 6. Run ML processing
python ml_processing/audio_features_ml.py data/raw/tracks.json

# 7. Load databases
python database_setup/load_mongo.py
python database_setup/load_neo4j.py

# 8. Test API
curl http://localhost:5000/api/health

# 9. Launch Streamlit frontend (optional)
streamlit run frontend/streamlit_app.py
```

**Services will be available at**:
- **Flask API**: http://localhost:5000
- **Neo4j Browser**: http://localhost:7474 (neo4j/password123)
- **Streamlit UI**: http://localhost:8501
- **MongoDB**: mongodb://admin:password123@localhost:27017

---

## Complete Setup Instructions

### Step 1: Get Spotify API Credentials (Optional)

**Only required if collecting custom data from Spotify API**

1. Go to https://developer.spotify.com/dashboard
2. Log in with your Spotify account
3. Click "Create app"
4. Fill in the details:
   - App name: "SpotifyRecs"
   - App description: "Music recommendation system"
   - Redirect URI: `http://127.0.0.1:8888/callback`
   - Check the Developer Terms of Service
5. Click "Save"
6. On your app's page, click "Settings"
7. Copy your **Client ID** and **Client Secret**

### Step 2: Clone and Setup Environment

```bash
# Clone repository
git clone https://github.com/BeemaRajan/no_sql_music_recs.git
cd SpotifyRecs

# Create environment file from template
cp .env.example .env

# Edit .env with your credentials (if using Spotify API)
# nano .env  # or use your favorite editor
```

**Your `.env` file should contain**:
```bash
# Spotify API (only if using Spotify data collection)
SPOTIFY_CLIENT_ID=your_client_id_here
SPOTIFY_CLIENT_SECRET=your_client_secret_here
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8888/callback

# MongoDB (defaults work with docker-compose)
MONGO_URI=mongodb://admin:password123@localhost:27017/spotifyrecs?authSource=admin
MONGO_DB=spotifyrecs
MONGO_COLLECTION=tracks

# Neo4j (defaults work with docker-compose)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password123

# Flask
FLASK_ENV=development
FLASK_SECRET_KEY=dev-secret-key
```

### Step 3: Start Docker Services

```bash
# Start all services (MongoDB, Neo4j, Flask API, Streamlit)
docker-compose up -d

# Check services are running
docker-compose ps

# Expected output:
# NAME                      STATUS    PORTS
# spotifyrecs-mongodb       Up        0.0.0.0:27017->27017/tcp
# spotifyrecs-neo4j         Up        0.0.0.0:7474->7474/tcp, 0.0.0.0:7687->7687/tcp
# spotifyrecs-api           Up        0.0.0.0:5000->5000/tcp
# spotifyrecs-streamlit     Up        0.0.0.0:8501->8501/tcp

# View logs (optional)
docker-compose logs -f
```

**Verify services**:
- MongoDB: `docker exec -it spotifyrecs-mongodb mongosh -u admin -p password123`
- Neo4j Browser: Open http://localhost:7474 (login: neo4j/password123)
- Flask API: `curl http://localhost:5000/api/health`

### Step 4: Install Python Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On Mac/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 5: Data Collection

**Choose Option A (Spotify API) or Option B (Kaggle Dataset)**

#### Option A: Spotify API (Custom Playlists)

```bash
# Run the Spotify data collector
python data_collection/spotify_collector.py

# When prompted:
# - Press 'n' to use default example playlists (recommended for first run)
# - Or press 'y' to enter your own Spotify playlist IDs

# This will:
# - Collect ~2,500 tracks (using the default example playlists)
# - Fetch audio features for each track
# - Save to data/raw/tracks.json
# - Take approximately 10-15 minutes
```

**Output**: `data/raw/tracks.json`

#### Option B: Kaggle Dataset (Pre-collected)

```bash
# 1. Download the Kaggle dataset
# Visit: https://www.kaggle.com/datasets/julianoorlandi/spotify-top-songs-and-audio-features
# Download: spotify_top_songs_audio_features.csv
# Place in: data/raw/

# 2. Convert CSV to JSON format
python data_collection/kaggle_conversion.py

# This will:
# - Read the CSV file
# - Convert to required JSON format
# - Save to data/raw/tracks.json
# - Process 5,496 tracks
```

**Output**: `data/raw/tracks.json`

### Step 6: ML Processing

```bash
# Run the ML processing pipeline with default parameters
python ml_processing/audio_features_ml.py data/raw/tracks.json

# Or customize parameters:
python ml_processing/audio_features_ml.py data/raw/tracks.json \
  --clusters 10 \
  --neighbors 15 \
  --threshold 0.7 \
  --top-n 15

# Parameters:
# --clusters: Number of K-means clusters (default: 10)
# --neighbors: UMAP n_neighbors parameter (default: 15)
# --threshold: Minimum similarity for edges (default: 0.7)
# --top-n: Number of similar tracks per track (default: 15)

# This will:
# - Normalize audio features
# - Perform UMAP dimensionality reduction (13D -> 2D)
# - Run K-means clustering
# - Calculate pairwise cosine similarities
# - Generate graph data (nodes and edges)
# - Take approximately 5-10 minutes
```

**Outputs** (in `data/processed/`):
- `tracks_with_clusters.json` - Tracks with cluster assignments and embeddings
- `neo4j_nodes.json` - Track nodes for Neo4j
- `neo4j_edges.json` - Similarity relationships for Neo4j
- `processing_stats.json` - Processing statistics and metadata

### Step 7: Load Databases

```bash
# Load MongoDB
python database_setup/load_mongo.py

# Expected example output:
# ============================================================
# MongoDB Database Loader
# ============================================================
#
# Step 1: Connecting to MongoDB...
# ✓ Connected to MongoDB: spotifyrecs.tracks
#
# Step 2: Loading data...
# ✓ Loaded 5234 tracks from data/processed/tracks_with_clusters.json
#
# Step 3: Clearing existing data...
# ✓ Cleared existing collection
#
# Step 4: Inserting tracks...
# ✓ Inserted 5234 tracks
#
# Step 5: Creating indexes...
# ✓ Created indexes
#
# MongoDB loading complete!

# Load Neo4j
python database_setup/load_neo4j.py

# Expected example output:
# ============================================================
# Neo4j Database Loader
# ============================================================
#
# Step 1: Connecting to Neo4j...
# ✓ Connected to Neo4j at bolt://localhost:7687
#
# Step 2: Loading data...
# ✓ Loaded 5234 nodes from data/processed/neo4j_nodes.json
# ✓ Loaded 78510 edges from data/processed/neo4j_edges.json
#
# Step 3: Clearing existing data...
# ✓ Cleared existing graph
#
# Step 4: Creating constraints...
# ✓ Created constraints
#
# Step 5: Creating track nodes...
# ✓ Created 5234 track nodes
#
# Step 6: Creating similarity relationships...
# ✓ Created 78510 SIMILAR_TO relationships
#
# Neo4j loading complete!
```

### Step 8: Test API

```bash
# Health check
curl http://localhost:5000/api/health

# Expected response:
# {
#   "status": "healthy",
#   "databases": {
#     "mongodb": "connected",
#     "neo4j": "connected"
#   }
# }

# Test search endpoint
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{"energy_min": 0.7, "tempo_min": 120}'

# Test mood search
curl "http://localhost:5000/api/mood?mood=happy"

# Test cluster stats
curl "http://localhost:5000/api/clusters"

# Test recommendations (replace TRACK_ID with actual track ID from your data)
curl "http://localhost:5000/api/recommend/TRACK_ID?hops=2&limit=10"
```

### Step 9: Explore with Neo4j Browser

1. Open http://localhost:7474
2. Login with credentials:
   - Username: `neo4j`
   - Password: `password123`
3. Try these Cypher queries:

```cypher
// View sample tracks
MATCH (t:Track)
RETURN t
LIMIT 25

// View similarity graph
MATCH (a:Track)-[r:SIMILAR_TO]->(b:Track)
RETURN a, r, b
LIMIT 50

// Find similar tracks (replace 'Song Title' with actual title)
MATCH path = (t:Track {title: 'Song Title'})-[:SIMILAR_TO*1..2]-(similar:Track)
RETURN similar.title, length(path) as hops
LIMIT 10

// View clusters
MATCH (t:Track)
RETURN t.cluster_id as cluster, count(t) as count
ORDER BY count DESC
```

### Step 10: Launch Streamlit Frontend (Optional)

```bash
# Make sure dependencies are installed
pip install -r requirements.txt

# Run the frontend
streamlit run frontend/streamlit_app.py

# Or if using Docker, it's already running at:
# http://localhost:8501
```

**Streamlit Features**:
- **Home Dashboard**: Database connection status and dataset statistics
- **MongoDB Queries**: Interactive forms for all 4 MongoDB query types
- **Neo4j Queries**: Graph visualizations and 3 Neo4j query types
- **Hybrid Queries**: Cluster navigation and recommendations
- **Interactive Controls**: Sliders, dropdowns, track search
- **Visualizations**: Charts, graphs, data tables

---

## Project Structure

```
SpotifyRecs/
├── api/                                # Flask REST API
│   ├── __init__.py
│   ├── app.py                         # Main Flask application
│   ├── database/                      # Database clients (singleton pattern)
│   │   ├── __init__.py
│   │   ├── mongo_client.py           # MongoDB connection and operations
│   │   └── neo4j_client.py           # Neo4j connection and operations
│   └── routes/                        # API route blueprints
│       ├── __init__.py
│       ├── search.py                  # Search endpoints (MongoDB queries 1, 3, 4)
│       ├── clusters.py                # Cluster endpoints (MongoDB query 2, Hybrid 8)
│       └── recommendations.py         # Recommendation endpoints (Neo4j 5, 6, 7, Hybrid 9)
│
├── data_collection/                   # Data collection scripts
│   ├── spotify_collector.py          # Spotify API collector (Option A)
│   └── kaggle_conversion.py          # Kaggle CSV to JSON converter (Option B)
│
├── ml_processing/                     # Machine learning pipeline
│   └── audio_features_ml.py          # UMAP + K-means + similarity calculation
│
├── database_setup/                    # Database loading scripts
│   ├── load_mongo.py                 # MongoDB loader
│   └── load_neo4j.py                 # Neo4j loader
│
├── data/                              # Data storage (created during setup)
│   ├── raw/                           # Raw collected data
│   │   ├── spotify_top_songs_audio_features.csv  # Kaggle dataset
│   │   └── tracks.json                # Converted/collected tracks
│   └── processed/                     # ML processed data
│       ├── tracks_with_clusters.json  # Tracks with cluster assignments
│       ├── neo4j_nodes.json           # Neo4j track nodes
│       ├── neo4j_edges.json           # Neo4j similarity edges
│       └── processing_stats.json      # Processing statistics
│
├── frontend/                          # Streamlit web interface
│   ├── streamlit_app.py              # Main Streamlit application
│   └── pages/                         # Multi-page app structure
│       ├── 1_Home.py                  # Dashboard with DB stats
│       ├── 2_MongoDB_Queries.py       # MongoDB query demos
│       ├── 3_Neo4j_Queries.py         # Neo4j query demos
│       └── 4_Hybrid_Queries.py        # Hybrid query demos
│
├── tests/                             # Test suite
│   └── test_api.py                   # API endpoint tests (runs queries)
│
├── docker-compose.yml                 # Docker services configuration
├── Dockerfile                         # Flask API container
├── Dockerfile.streamlit               # Streamlit container
├── requirements.txt                   # Python dependencies
├── .env.example                       # Environment variables template
├── .env                               # Your environment variables (create from .env.example)
├── .gitignore                         # Git ignore rules
└── README.md                          # This file
```

### Key Components Explained

#### Database Clients (Singleton Pattern)

Both database clients use the singleton pattern to ensure only one connection instance exists:

**mongo_client.py**:
```python
class MongoDBClient:
    _instance = None  # Single instance

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
```

**Methods**:
- `get_track_by_id(track_id)` - Fetch single track
- `search_tracks(filters)` - Range query
- `get_cluster_stats(cluster_id)` - Aggregation
- `mood_search(mood)` - Mood-based search
- `get_reference_tracks(filters)` - Producer search

**neo4j_client.py**:
```python
class Neo4jClient:
    _instance = None  # Single instance
    _driver = None    # Neo4j driver

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
```

**Methods**:
- `find_similar_tracks(track_id, max_hops)` - Graph traversal
- `find_triangles(min_similarity)` - Pattern matching
- `get_centrality(algorithm)` - Centrality ranking
- `execute_query(query, params)` - Generic query executor

#### Route Blueprints

Flask blueprints organize API endpoints by functionality:

- **search.py**: MongoDB queries (range, mood, reference)
- **clusters.py**: Cluster operations (stats, navigation)
- **recommendations.py**: Neo4j and hybrid queries (traversal, triangles, centrality, recommendations)

---

## API Documentation

### Base URL

```
http://localhost:5000
```

### Authentication

Currently, no authentication is required. For production deployment, implement:
- API key authentication
- Rate limiting
- User authentication (JWT tokens)

---

### Endpoints

#### 1. Health Check

**GET** `/api/health`

Check API and database connectivity.

**Response**:
```json
{
  "status": "healthy",
  "databases": {
    "mongodb": "connected",
    "neo4j": "connected"
  }
}
```

---

#### 2. Range Query on Audio Features (MongoDB Query #1)

**POST** `/api/search`

Search tracks by audio feature ranges.

**Request Body**:
```json
{
  "energy_min": 0.7,
  "energy_max": 1.0,
  "danceability_min": 0.6,
  "tempo_min": 120,
  "tempo_max": 140,
  "cluster_id": 3
}
```

**Available Filters**:
- `energy_min`, `energy_max` (0.0-1.0)
- `danceability_min`, `danceability_max` (0.0-1.0)
- `valence_min`, `valence_max` (0.0-1.0)
- `tempo_min`, `tempo_max` (typically 50-200 BPM)
- `acousticness_min`, `acousticness_max` (0.0-1.0)
- `instrumentalness_min`, `instrumentalness_max` (0.0-1.0)
- `liveness_min`, `liveness_max` (0.0-1.0)
- `speechiness_min`, `speechiness_max` (0.0-1.0)
- `loudness_min`, `loudness_max` (typically -60 to 0 dB)
- `cluster_id` (integer, 0-9 for default 10 clusters)

**Response**:
```json
{
  "count": 42,
  "filters": {
    "energy_min": 0.7,
    "danceability_min": 0.6,
    "tempo_min": 120
  },
  "results": [
    {
      "track_id": "spotify:track:xyz",
      "title": "Upbeat Song",
      "artist": "Artist Name",
      "album": "Album Name",
      "popularity": 85,
      "energy": 0.85,
      "danceability": 0.75,
      "valence": 0.82,
      "tempo": 128.0,
      "cluster_id": 3,
      "umap_x": 2.34,
      "umap_y": -1.56
    }
  ]
}
```

**cURL Example**:
```bash
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "energy_min": 0.7,
    "danceability_min": 0.6,
    "tempo_min": 120
  }'
```

---

#### 3. All Cluster Statistics (MongoDB Query #2)

**GET** `/api/clusters`

Get aggregated statistics for all clusters.

**Response**:
```json
{
  "cluster_count": 10,
  "clusters": [
    {
      "cluster_id": 0,
      "count": 487,
      "avg_energy": 0.52,
      "avg_danceability": 0.61,
      "avg_valence": 0.48,
      "avg_tempo": 118.3,
      "avg_acousticness": 0.34,
      "avg_instrumentalness": 0.12,
      "avg_popularity": 62.4
    },
    {
      "cluster_id": 1,
      "count": 523,
      "avg_energy": 0.68,
      "avg_danceability": 0.72,
      "avg_valence": 0.65,
      "avg_tempo": 125.4,
      "avg_acousticness": 0.21,
      "avg_instrumentalness": 0.05,
      "avg_popularity": 68.2
    }
  ]
}
```

**cURL Example**:
```bash
curl http://localhost:5000/api/clusters
```

---

#### 4. Specific Cluster Details (Hybrid Query #8)

**GET** `/api/cluster/<cluster_id>`

Get statistics and all tracks for a specific cluster.

**Parameters**:
- `cluster_id` (path): Cluster ID (integer, e.g., 0-9)

**Response**:
```json
{
  "cluster_id": 3,
  "statistics": {
    "count": 523,
    "avg_energy": 0.68,
    "avg_danceability": 0.72,
    "avg_valence": 0.65,
    "avg_tempo": 125.4,
    "avg_acousticness": 0.21,
    "avg_instrumentalness": 0.05,
    "avg_popularity": 68.2
  },
  "track_count": 523,
  "tracks": [
    {
      "track_id": "spotify:track:abc",
      "title": "Track in Cluster 3",
      "artist": "Artist Name",
      "energy": 0.72,
      "danceability": 0.68,
      "cluster_id": 3
    }
  ]
}
```

**cURL Example**:
```bash
curl http://localhost:5000/api/cluster/3
```

---

#### 5. Mood-Based Search (MongoDB Query #3)

**GET** `/api/mood?mood={mood_name}`

Find tracks matching a mood profile.

**Query Parameters**:
- `mood` (required): One of: `happy`, `energetic`, `calm`, `sad`, `workout`, `chill`

**Mood Definitions**:
- **happy**: High valence (≥0.6), moderate energy (≥0.5)
- **energetic**: High energy (≥0.7), high tempo (≥120 BPM)
- **calm**: Low energy (≤0.4), high acousticness (≥0.5)
- **sad**: Low valence (≤0.4), low energy (≤0.5)
- **workout**: High energy (≥0.8), high tempo (≥140 BPM), high danceability (≥0.6)
- **chill**: Moderate energy (0.3-0.6), low tempo (≤110 BPM)

**Response**:
```json
{
  "mood": "happy",
  "count": 234,
  "criteria": {
    "valence_min": 0.6,
    "energy_min": 0.5
  },
  "results": [
    {
      "track_id": "spotify:track:xyz",
      "title": "Happy Song",
      "artist": "Artist Name",
      "valence": 0.82,
      "energy": 0.68,
      "cluster_id": 2
    }
  ]
}
```

**cURL Examples**:
```bash
curl "http://localhost:5000/api/mood?mood=happy"
curl "http://localhost:5000/api/mood?mood=energetic"
curl "http://localhost:5000/api/mood?mood=workout"
```

---

#### 6. Producer Reference Tracks (MongoDB Query #4)

**GET** `/api/reference`

Find tracks by production characteristics for music producers.

**Query Parameters** (all optional):
- `instrumentalness_min` (default: 0.5): Minimum instrumentalness (0.0-1.0)
- `speechiness_max` (default: 0.3): Maximum speechiness (0.0-1.0)
- `acousticness_min` (default: 0.0): Minimum acousticness (0.0-1.0)
- `acousticness_max` (default: 1.0): Maximum acousticness (0.0-1.0)

**Response**:
```json
{
  "count": 45,
  "filters": {
    "instrumentalness_min": 0.6,
    "speechiness_max": 0.2,
    "acousticness_min": 0.4,
    "acousticness_max": 0.7
  },
  "results": [
    {
      "track_id": "spotify:track:xyz",
      "title": "Instrumental Track",
      "artist": "Artist Name",
      "instrumentalness": 0.85,
      "speechiness": 0.05,
      "acousticness": 0.62,
      "popularity": 45
    }
  ]
}
```

**cURL Examples**:
```bash
curl "http://localhost:5000/api/reference?instrumentalness_min=0.7"
curl "http://localhost:5000/api/reference?instrumentalness_min=0.6&acousticness_min=0.4&acousticness_max=0.7"
```

---

#### 7. Single Track Details

**GET** `/api/track/<track_id>`

Get full details for a single track.

**Parameters**:
- `track_id` (path): Spotify track ID or URI

**Response**:
```json
{
  "track_id": "spotify:track:6rqhFgbbKwnb9MLmUQDhG6",
  "title": "Song Title",
  "artist": "Artist Name",
  "album": "Album Name",
  "popularity": 78,
  "energy": 0.85,
  "danceability": 0.75,
  "valence": 0.68,
  "tempo": 128.0,
  "acousticness": 0.12,
  "instrumentalness": 0.0,
  "liveness": 0.08,
  "loudness": -5.3,
  "speechiness": 0.04,
  "key": 5,
  "mode": 1,
  "time_signature": 4,
  "cluster_id": 3,
  "umap_x": 2.34,
  "umap_y": -1.56
}
```

**cURL Example**:
```bash
curl "http://localhost:5000/api/track/spotify:track:6rqhFgbbKwnb9MLmUQDhG6"
```

---

#### 8. Graph-Based Recommendations (Neo4j Query #5 + Hybrid Query #9)

**GET** `/api/recommend/<track_id>`

Get track recommendations using graph traversal.

**Parameters**:
- `track_id` (path): Spotify track ID or URI
- `hops` (query, optional): Maximum graph traversal distance (1-3, default: 2)
- `limit` (query, optional): Maximum number of recommendations (default: 20)

**How it Works**:
1. Queries Neo4j for similar tracks via SIMILAR_TO relationships (1-3 hops)
2. Calculates path scores (product of similarity scores along path)
3. Fetches full track details from MongoDB
4. Returns combined results sorted by similarity

**Response**:
```json
{
  "source_track": {
    "track_id": "spotify:track:xyz",
    "title": "Source Song",
    "artist": "Artist Name",
    "energy": 0.85,
    "danceability": 0.75,
    "cluster_id": 3
  },
  "parameters": {
    "max_hops": 2,
    "limit": 20
  },
  "count": 20,
  "recommendations": [
    {
      "track_id": "spotify:track:abc",
      "title": "Similar Song 1",
      "artist": "Another Artist",
      "similarity_score": 0.8523,
      "hops": 1,
      "energy": 0.82,
      "danceability": 0.78,
      "cluster_id": 3
    },
    {
      "track_id": "spotify:track:def",
      "title": "Similar Song 2",
      "artist": "Third Artist",
      "similarity_score": 0.7845,
      "hops": 2,
      "energy": 0.79,
      "danceability": 0.71,
      "cluster_id": 3
    }
  ]
}
```

**cURL Examples**:
```bash
# 2-hop recommendations
curl "http://localhost:5000/api/recommend/spotify:track:6rqhFgbbKwnb9MLmUQDhG6?hops=2&limit=20"

# 1-hop (direct neighbors only)
curl "http://localhost:5000/api/recommend/spotify:track:6rqhFgbbKwnb9MLmUQDhG6?hops=1&limit=10"

# 3-hop (wider network)
curl "http://localhost:5000/api/recommend/spotify:track:6rqhFgbbKwnb9MLmUQDhG6?hops=3&limit=20"
```

---

#### 9. Similarity Triangles (Neo4j Query #6)

**GET** `/api/triangles`

Find triangles of mutually similar tracks using pattern matching.

**Query Parameters** (all optional):
- `min_similarity` (default: 0.7): Minimum similarity threshold (0.0-1.0)
- `limit` (default: 10): Maximum number of triangles

**How it Works**:
Finds patterns where three tracks are all similar to each other:
```
(a) -[SIMILAR_TO]- (b) -[SIMILAR_TO]- (c) -[SIMILAR_TO]- (a)
```

**Response**:
```json
{
  "parameters": {
    "min_similarity": 0.75,
    "limit": 10
  },
  "count": 10,
  "triangles": [
    {
      "track_a_id": "spotify:track:abc",
      "track_a_title": "Song A",
      "track_a_artist": "Artist A",
      "track_b_id": "spotify:track:def",
      "track_b_title": "Song B",
      "track_b_artist": "Artist B",
      "track_c_id": "spotify:track:ghi",
      "track_c_title": "Song C",
      "track_c_artist": "Artist C",
      "sim_ab": 0.85,
      "sim_bc": 0.82,
      "sim_ca": 0.79,
      "avg_similarity": 0.82
    }
  ]
}
```

**cURL Examples**:
```bash
curl "http://localhost:5000/api/triangles?min_similarity=0.7&limit=10"
curl "http://localhost:5000/api/triangles?min_similarity=0.8&limit=5"
```

---

#### 10. Network Centrality Ranking (Neo4j Query #7)

**GET** `/api/centrality`

Rank tracks by network centrality (most influential/connected tracks).

**Query Parameters** (all optional):
- `algorithm` (default: "degree"): `"degree"` or `"pagerank"`
- `limit` (default: 20): Number of results

**Algorithms**:
- **degree**: Count of SIMILAR_TO relationships (simpler, faster)
- **pagerank**: Weighted influence score (requires Neo4j GDS plugin)

**Response**:
```json
{
  "algorithm": "degree",
  "count": 20,
  "tracks": [
    {
      "track_id": "spotify:track:xyz",
      "title": "Central Track",
      "artist": "Artist Name",
      "cluster_id": 3,
      "degree": 23,
      "avg_similarity": 0.7845,
      "energy": 0.68,
      "danceability": 0.72
    }
  ]
}
```

**cURL Examples**:
```bash
# Degree centrality
curl "http://localhost:5000/api/centrality?algorithm=degree&limit=20"

# PageRank centrality (if GDS is available)
curl "http://localhost:5000/api/centrality?algorithm=pagerank&limit=20"
```

---

#### 11. Direct Neighbors (1-Hop Similar Tracks)

**GET** `/api/similar/<track_id>`

Get direct neighbors (tracks with direct SIMILAR_TO relationship).

**Parameters**:
- `track_id` (path): Spotify track ID or URI
- `limit` (query, optional): Number of results (default: 10)

**Response**:
```json
{
  "source_track": {
    "track_id": "spotify:track:xyz",
    "title": "Song Title",
    "artist": "Artist"
  },
  "count": 10,
  "similar_tracks": [
    {
      "track_id": "spotify:track:abc",
      "title": "Similar Song",
      "artist": "Artist Name",
      "similarity_score": 0.8923,
      "energy": 0.82,
      "danceability": 0.78,
      "cluster_id": 3
    }
  ]
}
```

**cURL Example**:
```bash
curl "http://localhost:5000/api/similar/spotify:track:6rqhFgbbKwnb9MLmUQDhG6?limit=10"
```

---

#### 12. Dataset Statistics

**GET** `/api/stats`

Get overall statistics from both databases.

**Response**:
```json
{
  "mongodb": {
    "total_tracks": 5234,
    "total_clusters": 10,
    "clusters": [
      {
        "cluster_id": 0,
        "count": 487
      }
    ],
    "average_features": {
      "energy": 0.62,
      "danceability": 0.68,
      "valence": 0.54,
      "tempo": 121.3,
      "popularity": 65.2
    }
  },
  "neo4j": {
    "total_nodes": 5234,
    "total_relationships": 78510,
    "average_degree": 15.0,
    "average_similarity": 0.7523
  }
}
```

**cURL Example**:
```bash
curl "http://localhost:5000/api/stats"
```

---

### Error Responses

All endpoints return appropriate HTTP status codes:

- **200 OK**: Success
- **400 Bad Request**: Invalid parameters
- **404 Not Found**: Resource not found
- **500 Internal Server Error**: Server error

**Error Format**:
```json
{
  "error": "Error type",
  "message": "Detailed error message"
}
```

**Example Error Responses**:

```json
// 404 - Track not found
{
  "error": "Track not found",
  "track_id": "spotify:track:invalid"
}

// 400 - Invalid parameters
{
  "error": "Invalid hops parameter",
  "message": "hops must be between 1 and 3"
}

// 500 - Database connection error
{
  "error": "Database error",
  "message": "Failed to connect to MongoDB"
}
```

---

## Query Examples

This section demonstrates all 9 query types with MongoDB shell commands, Cypher queries, and API calls.

### MongoDB Queries (4 Queries)

#### Query 1: Range Query on Audio Features

**Description**: Find tracks by audio feature ranges

**Use Case**: Finding high-energy dance tracks with moderate tempo for a workout playlist

**MongoDB Shell**:
```javascript
// Connect to MongoDB
mongosh "mongodb://admin:password123@localhost:27017/spotifyrecs?authSource=admin"

// Use the database
use spotifyrecs

// Query
db.tracks.find({
    "energy": { "$gte": 0.7, "$lte": 1.0 },
    "danceability": { "$gte": 0.6 },
    "tempo": { "$gte": 120, "$lte": 140 }
}).limit(20)
```

**API Endpoint**:
```bash
curl -X POST http://localhost:5000/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "energy_min": 0.7,
    "energy_max": 1.0,
    "danceability_min": 0.6,
    "tempo_min": 120,
    "tempo_max": 140
  }'
```

---

#### Query 2: Aggregation Pipeline for Cluster Statistics

**Description**: Calculate average audio features by cluster

**Use Case**: Understanding the sonic characteristics of different clusters

**MongoDB Shell**:
```javascript
db.tracks.aggregate([
    {
        $group: {
            _id: "$cluster_id",
            count: { $sum: 1 },
            avg_energy: { $avg: "$energy" },
            avg_danceability: { $avg: "$danceability" },
            avg_valence: { $avg: "$valence" },
            avg_tempo: { $avg: "$tempo" },
            avg_acousticness: { $avg: "$acousticness" },
            avg_instrumentalness: { $avg: "$instrumentalness" },
            avg_popularity: { $avg: "$popularity" }
        }
    },
    {
        $sort: { _id: 1 }
    }
])
```

**API Endpoints**:
```bash
# All clusters
curl http://localhost:5000/api/clusters

# Specific cluster
curl http://localhost:5000/api/cluster/3
```

---

#### Query 3: Mood-Based Search

**Description**: Find tracks matching mood profiles

**Use Case**: Creating mood-specific playlists for different activities

**Mood Profiles**:
- **Happy**: High valence (≥0.9), high energy (≥0.7)
- **Energetic**: High energy (≥0.7), high tempo (≥150 BPM)
- **Calm**: Low energy (≤0.4), moderate valence (≥0.3), high acousticness (≥0.4)
- **Sad**: Low valence (≤0.4), low energy (≤0.5)
- **Workout**: High energy (≥0.8), moderate to high tempo (≥120 BPM), high danceability (≥0.6)
- **Chill**: Moderate energy (≤0.5), moderate acousticness (≥0.3), moderate instrumentalness (0.3)

**MongoDB Shell (Happy)**:
```javascript
db.tracks.find({
    "valence": { "$gte": 0.6 },
    "energy": { "$gte": 0.5 }
}).limit(50)
```

**MongoDB Shell (Energetic)**:
```javascript
db.tracks.find({
    "energy": { "$gte": 0.7 },
    "tempo": { "$gte": 120 }
}).limit(50)
```

**API Endpoints**:
```bash
# Happy tracks
curl "http://localhost:5000/api/mood?mood=happy"

# Energetic tracks
curl "http://localhost:5000/api/mood?mood=energetic"

# Calm tracks
curl "http://localhost:5000/api/mood?mood=calm"

# Workout tracks
curl "http://localhost:5000/api/mood?mood=workout"
```

---

#### Query 4: Producer Reference Tracks

**Description**: Find tracks by production characteristics

**Use Case**: Music producers finding reference tracks with specific production qualities

**MongoDB Shell**:
```javascript
db.tracks.find({
    "instrumentalness": { "$gte": 0.5 },
    "speechiness": { "$lte": 0.3 },
    "acousticness": { "$gte": 0.0, "$lte": 1.0 }
}).sort({ "popularity": -1 }).limit(50)
```

**API Endpoints**:
```bash
# Basic search
curl "http://localhost:5000/api/reference?instrumentalness_min=0.5&speechiness_max=0.3"

# More specific search
curl "http://localhost:5000/api/reference?instrumentalness_min=0.7&acousticness_min=0.4&acousticness_max=0.7"
```

---

### Neo4j Queries (3 Queries)

#### Query 5: Graph Traversal for Similar Tracks

**Description**: Find similar tracks within N hops using graph traversal

**Use Case**: Finding "similar to similar" recommendations through the similarity network

**Cypher (2-hop traversal)**:
```cypher
MATCH path = (source:Track {track_id: 'spotify:track:6rqhFgbbKwnb9MLmUQDhG6'})-[:SIMILAR_TO*1..2]-(similar:Track)
WHERE source <> similar
WITH similar,
     length(path) as hops,
     reduce(score = 1.0, rel in relationships(path) | score * rel.similarity) as path_score
RETURN DISTINCT similar.track_id as track_id,
       similar.title as title,
       similar.cluster_id as cluster_id,
       hops,
       path_score as similarity_score
ORDER BY path_score DESC, hops ASC
LIMIT 20
```

**Cypher (1-hop - direct neighbors)**:
```cypher
MATCH (source:Track {track_id: 'spotify:track:6rqhFgbbKwnb9MLmUQDhG6'})
      -[r:SIMILAR_TO]-(similar:Track)
RETURN similar.track_id as track_id,
       similar.title as title,
       r.similarity as similarity_score
ORDER BY similarity_score DESC
LIMIT 10
```

**API Endpoints**:
```bash
# 2-hop traversal
curl "http://localhost:5000/api/recommend/TRACK_ID?hops=2&limit=20"

# 1-hop (direct neighbors)
curl "http://localhost:5000/api/recommend/TRACK_ID?hops=1&limit=10"

# 3-hop (wider network)
curl "http://localhost:5000/api/recommend/TRACK_ID?hops=3&limit=20"
```

**Note**: Replace `TRACK_ID` with an actual track ID from your database.

---

#### Query 6: Triangle Pattern Matching

**Description**: Find triangles of mutually similar tracks

**Use Case**: Discovering tight clusters of highly similar tracks

**Cypher**:
```cypher
MATCH (a:Track)-[r1:SIMILAR_TO]-(b:Track)-[r2:SIMILAR_TO]-(c:Track)-[r3:SIMILAR_TO]-(a)
WHERE a.track_id < b.track_id AND b.track_id < c.track_id
       AND r1.similarity >= 0.7
       AND r2.similarity >= 0.7
       AND r3.similarity >= 0.7
       AND r1.similarity < 0.99
       AND r2.similarity < 0.99
       AND r3.similarity < 0.99
       AND a.title <> b.title 
       AND b.title <> c.title 
       AND a.title <> c.title 
RETURN a.track_id as track_a_id,
       a.title as track_a_title,
       b.track_id as track_b_id,
       b.title as track_b_title,
       c.track_id as track_c_id,
       c.title as track_c_title,
       r1.similarity as sim_ab,
       r2.similarity as sim_bc,
       r3.similarity as sim_ca,
       (r1.similarity + r2.similarity + r3.similarity) / 3.0 as avg_similarity
ORDER BY avg_similarity DESC
LIMIT 10
```

The where clause handles floating point values and discourages similar song triangles.

**API Endpoints**:
```bash
# Standard threshold
curl "http://localhost:5000/api/triangles?min_similarity=0.7&limit=10"

# Higher similarity threshold
curl "http://localhost:5000/api/triangles?min_similarity=0.8&limit=5"
```

---

#### Query 7: Network Centrality Ranking

**Description**: Rank tracks by degree centrality

**Use Case**: Finding the most "influential" tracks in the similarity network

**Cypher (Degree Centrality)**:
```cypher
MATCH (t:Track)-[r:SIMILAR_TO]-()
WITH t, count(r) as degree, avg(r.similarity) as avg_similarity
RETURN t.track_id as track_id,
       t.title as title,
       t.cluster_id as cluster_id,
       degree,
       avg_similarity
ORDER BY degree DESC, avg_similarity DESC
LIMIT 20
```

**API Endpoints**:
```bash
# Degree centrality
curl "http://localhost:5000/api/centrality?algorithm=degree&limit=20"

# PageRank centrality (if GDS is available)
curl "http://localhost:5000/api/centrality?algorithm=pagerank&limit=20"
```

---

### Hybrid Queries (2 Queries)

#### Hybrid Query 8: Cluster Navigation

**Description**: Query Neo4j for cluster track IDs, then fetch full details from MongoDB

**Use Case**: Exploring all tracks in a sonic cluster with full metadata

**Process**:
1. **Neo4j Part**: Get track IDs in cluster
```cypher
MATCH (t:Track {cluster_id: 3})
RETURN t.track_id as track_id
```

2. **MongoDB Part**: Fetch full track details
```javascript
db.tracks.find({
    "track_id": { "$in": [/* track IDs from Neo4j */] }
})
```

**API Endpoint**:
```bash
curl "http://localhost:5000/api/cluster/3"
```

---

#### Hybrid Query 9: Recommendation Engine

**Description**: Query Neo4j for similar track IDs via graph traversal, then fetch full details from MongoDB

**Use Case**: Complete recommendation system combining graph relationships with full track metadata

**Process**:
1. **Neo4j Part**: Graph traversal to find similar tracks
```cypher
MATCH path = (source:Track {track_id: 'spotify:track:xyz'})-[:SIMILAR_TO*1..2]-(similar:Track)
RETURN similar.track_id as track_id,
       length(path) as hops,
       reduce(score = 1.0, rel in relationships(path) | score * rel.similarity) as similarity_score
ORDER BY similarity_score DESC
LIMIT 20
```

2. **MongoDB Part**: Fetch full track details
```javascript
db.tracks.find({
    "track_id": { "$in": [/* track IDs from Neo4j */] }
})
```

**API Endpoint**:
```bash
curl "http://localhost:5000/api/recommend/TRACK_ID?hops=2&limit=20"
```

---

### Testing All Queries

#### MongoDB Shell Testing

```bash
# Connect to MongoDB
mongosh "mongodb://admin:password123@localhost:27017/spotifyrecs?authSource=admin"

# Switch to database
use spotifyrecs

# Query 1: Range query
db.tracks.find({ "energy": { "$gte": 0.7 }, "tempo": { "$gte": 120 } }).limit(5)

# Query 2: Aggregation
db.tracks.aggregate([{ $group: { _id: "$cluster_id", count: { $sum: 1 } } }])

# Query 3: Mood search
db.tracks.find({ "valence": { "$gte": 0.6 }, "energy": { "$gte": 0.5 } }).limit(5)

# Query 4: Producer search
db.tracks.find({ "instrumentalness": { "$gte": 0.5 } }).limit(5)
```

#### Neo4j Browser Testing

```bash
# Access Neo4j Browser
# URL: http://localhost:7474
# Username: neo4j
# Password: password123

# Run these queries in Neo4j Browser:

// Query 5: Find similar tracks (replace with actual track_id)
MATCH path = (t:Track {track_id: 'spotify:track:YOUR_TRACK_ID'})-[:SIMILAR_TO*1..2]-(similar:Track)
RETURN similar.title, length(path) as hops
LIMIT 10

// Query 6: Find triangles
MATCH (a:Track)-[r1:SIMILAR_TO]-(b:Track)-[r2:SIMILAR_TO]-(c:Track)-[r3:SIMILAR_TO]-(a)
WHERE a.track_id < b.track_id AND b.track_id < c.track_id
RETURN a.title, b.title, c.title, r1.similarity, r2.similarity, r3.similarity
LIMIT 5

// Query 7: Centrality
MATCH (t:Track)-[r:SIMILAR_TO]-()
WITH t, count(r) as degree
RETURN t.title, degree
ORDER BY degree DESC
LIMIT 10
```

#### API Testing Script

Create a file `test_api.sh`:

```bash
#!/bin/bash

BASE_URL="http://localhost:5000"

echo "Testing all API endpoints..."
echo "=============================="

# Query 1: Range query
echo -e "\n1. Range query (MongoDB Query #1)"
curl -X POST "$BASE_URL/api/search" \
  -H "Content-Type: application/json" \
  -d '{"energy_min": 0.7, "tempo_min": 120}'

# Query 2: Cluster statistics
echo -e "\n\n2. Cluster statistics (MongoDB Query #2)"
curl "$BASE_URL/api/clusters"

# Query 3: Mood search
echo -e "\n\n3. Mood search (MongoDB Query #3)"
curl "$BASE_URL/api/mood?mood=happy"

# Query 4: Reference tracks
echo -e "\n\n4. Reference tracks (MongoDB Query #4)"
curl "$BASE_URL/api/reference?instrumentalness_min=0.5"

# Query 5 + Hybrid Query 9: Recommendations
echo -e "\n\n5. Recommendations (Neo4j Query #5 + Hybrid #9)"
curl "$BASE_URL/api/recommend/[TRACK_ID]?hops=2"

# Query 6: Triangles
echo -e "\n\n6. Triangles (Neo4j Query #6)"
curl "$BASE_URL/api/triangles"

# Query 7: Centrality
echo -e "\n\n7. Centrality (Neo4j Query #7)"
curl "$BASE_URL/api/centrality?algorithm=degree"

# Hybrid Query 8: Cluster navigation
echo -e "\n\n8. Cluster navigation (Hybrid Query #8)"
curl "$BASE_URL/api/cluster/3"

echo -e "\n\nAll tests complete!"
```

Make it executable and run:
```bash
chmod +x test_api.sh
./test_api.sh
```

---

### Performance Notes

- **MongoDB Queries**: Fast with proper indexes (~10-50ms)
- **Neo4j 1-hop**: Very fast (~5-20ms)
- **Neo4j 2-hop**: Moderate (~20-100ms)
- **Neo4j 3-hop**: Slower (~100-500ms)
- **Triangle matching**: Can be slow on large graphs (~100-1000ms)
- **Centrality calculations**: Moderate to slow depending on graph size

### Query Optimization Tips

1. **MongoDB**: Create compound indexes for common query patterns
2. **Neo4j**: Use relationship direction wisely (undirected relationships are faster for some queries)
3. **Hybrid queries**: Fetch only needed fields from MongoDB
4. **Caching**: Consider caching frequently accessed results
5. **Pagination**: Always limit result set sizes
6. **Batch operations**: Use batch inserts/updates for large datasets

---

## Frontend Interface

### Streamlit Multi-Page Application

The project includes a full-featured Streamlit frontend for exploring all query types.

**Access**: http://localhost:8501 (when using Docker) or run locally with:
```bash
streamlit run frontend/streamlit_app.py
```

### Pages

#### 1. Home Dashboard

**Features**:
- Database connection status (MongoDB and Neo4j)
- Dataset statistics:
  - Total tracks
  - Total clusters
  - Average audio features
  - Graph statistics (nodes, edges, average degree)
- Quick links to query pages

#### 2. MongoDB Queries

**Interactive Forms**:
- **Query 1**: Range query with sliders for all audio features
- **Query 2**: Cluster statistics table
- **Query 3**: Mood selector dropdown
- **Query 4**: Producer reference track filters

**Features**:
- Real-time results
- Data tables with sorting
- CSV export
- Result count

#### 3. Neo4j Queries

**Interactive Forms**:
- **Query 5**: Graph traversal with hop selector
- **Query 6**: Triangle pattern matching with similarity threshold
- **Query 7**: Centrality ranking with algorithm selector

**Features**:
- Graph visualizations
- Network diagrams
- Data tables
- CSV export

#### 4. Hybrid Queries

**Interactive Forms**:
- **Query 8**: Cluster navigation with cluster selector
- **Query 9**: Recommendation engine with track search

**Features**:
- Track search autocomplete
- Combined results from both databases
- Similarity scores
- Hop distances
- CSV export

### Running the Frontend

**Option 1: Docker** (already running if you used docker-compose):
```bash
# Access at http://localhost:8501
# No additional steps needed
```

**Option 2: Local**:
```bash
# Install dependencies
pip install -r requirements.txt

# Run Streamlit
streamlit run frontend/streamlit_app.py

# Opens automatically in browser at http://localhost:8501
```

---

## Testing

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run all tests
pytest

# Run specific test file
pytest tests/test_api.py

# Run with coverage
pytest --cov=api tests/

# Generate coverage report
pytest --cov=api --cov-report=html tests/
```

### Test Structure

```
tests/
└── test_api.py              # API endpoint tests
```

### Example Tests

**test_api.py**:
```python
def test_health_endpoint():
    """Test /api/health endpoint"""
    response = client.get('/api/health')
    assert response.status_code == 200
    assert 'databases' in response.json

def test_search_endpoint():
    """Test /api/search endpoint"""
    response = client.post('/api/search', json={
        'energy_min': 0.7,
        'tempo_min': 120
    })
    assert response.status_code == 200
    assert 'results' in response.json
```

---

## Troubleshooting

### Docker Issues

**Problem**: Docker services won't start

```bash
# Check Docker is running
docker info

# View all container logs
docker-compose logs

# View specific service logs
docker-compose logs mongodb
docker-compose logs neo4j
docker-compose logs flask-api

# Restart services
docker-compose restart

# Clean slate (WARNING: removes all data!)
docker-compose down -v
docker-compose up -d
```

**Problem**: Port already in use (27017, 7474, 7687, or 5000)

```bash
# Find what's using the port (example for port 27017)
# On Mac/Linux:
lsof -i :27017
# On Windows:
netstat -ano | findstr :27017

# Either stop that service or change port in docker-compose.yml
```

**Problem**: Not enough memory

```bash
# Increase Docker memory allocation
# Docker Desktop > Settings > Resources > Memory
# Recommended: At least 4GB
```

### Database Connection Issues

**Problem**: MongoDB connection failed

```bash
# Check MongoDB is running
docker-compose ps mongodb

# View MongoDB logs
docker-compose logs mongodb

# Test connection manually
docker exec -it spotifyrecs-mongodb mongosh -u admin -p password123

# If that works, check MONGO_URI in .env
cat .env | grep MONGO_URI
```

**Problem**: Neo4j connection failed

```bash
# Check Neo4j is running
docker-compose ps neo4j

# View Neo4j logs
docker-compose logs neo4j

# Try browser access
# URL: http://localhost:7474
# Credentials: neo4j / password123

# Check NEO4J_URI in .env
cat .env | grep NEO4J
```

**Problem**: "Authentication failed" errors

```bash
# Verify credentials in .env match docker-compose.yml
# MongoDB: admin / password123
# Neo4j: neo4j / password123

# Restart services after changing credentials
docker-compose restart
```

### Data Collection Issues

**Problem**: Spotify API authentication failed

```bash
# Verify credentials in .env
cat .env | grep SPOTIFY

# Make sure there are no extra spaces or quotes
# Should look like:
# SPOTIFY_CLIENT_ID=abc123
# SPOTIFY_CLIENT_SECRET=xyz789

# Delete cache and try again
rm .spotify_cache
python data_collection/spotify_collector.py
```

**Problem**: Rate limit exceeded

```bash
# Spotify free tier has rate limits
# Wait a few minutes and try again

# Or reduce the number of playlists in spotify_collector.py
```

**Problem**: Kaggle CSV not found

```bash
# Make sure the CSV is in the correct location
ls data/raw/spotify_top_songs_audio_features.csv

# If not found, download from:
# https://www.kaggle.com/datasets/julianoorlandi/spotify-top-songs-and-audio-features

# Place in data/raw/ directory
```

### ML Processing Issues

**Problem**: Out of memory during processing

```bash
# Increase Docker memory
# Docker Desktop > Settings > Resources > Memory

# Or reduce dataset size
# Edit spotify_collector.py to use fewer playlists
```

**Problem**: UMAP/scikit-learn import errors

```bash
# Reinstall dependencies
pip uninstall umap-learn scikit-learn
pip install umap-learn scikit-learn

# Or use virtual environment
python -m venv venv
source venv/bin/activate  # On Mac/Linux
venv\Scripts\activate     # On Windows
pip install -r requirements.txt
```

**Problem**: "No such file or directory: data/raw/tracks.json"

```bash
# Make sure you've completed data collection first
# Run either:
python data_collection/spotify_collector.py
# OR
python data_collection/kaggle_conversion.py

# Verify file exists
ls data/raw/tracks.json
```

### API Issues

**Problem**: Flask API not starting

```bash
# Check Flask logs
docker-compose logs flask-api

# Common issues:
# 1. MongoDB or Neo4j not running
# 2. Database connection errors
# 3. Missing .env file

# Rebuild Flask container
docker-compose build flask-api
docker-compose up -d flask-api
```

**Problem**: API returns empty results

```bash
# Check that databases are loaded
# MongoDB:
docker exec -it spotifyrecs-mongodb mongosh -u admin -p password123
use spotifyrecs
db.tracks.countDocuments()

# Neo4j:
# Open http://localhost:7474
# Run: MATCH (t:Track) RETURN count(t)

# If empty, reload databases
python database_setup/load_mongo.py
python database_setup/load_neo4j.py
```

### Common Error Messages

**"Connection refused"**
- Docker services not running
- Solution: `docker-compose up -d`

**"Authentication failed"**
- Wrong credentials in .env
- Solution: Check .env matches docker-compose.yml

**"File not found"**
- Missing data files
- Solution: Run data collection and ML processing steps

**"Port already allocated"**
- Port in use by another service
- Solution: Change port in docker-compose.yml or stop other service

---

## Development

### Useful Commands

```bash
# View logs for all services
docker-compose logs -f

# View logs for specific service
docker-compose logs -f flask-api
docker-compose logs -f mongodb
docker-compose logs -f neo4j

# Restart a service
docker-compose restart flask-api
docker-compose restart mongodb
docker-compose restart neo4j

# Access MongoDB shell
docker exec -it spotifyrecs-mongodb mongosh -u admin -p password123

# Access Neo4j Cypher shell
docker exec -it spotifyrecs-neo4j cypher-shell -u neo4j -p password123

# Stop all services
docker-compose down

# Stop and remove volumes (clean slate - WARNING: deletes all data!)
docker-compose down -v

# Rebuild containers
docker-compose build

# View running containers
docker-compose ps

# View container resource usage
docker stats
```

### MongoDB Commands

```bash
# Connect to MongoDB
docker exec -it spotifyrecs-mongodb mongosh -u admin -p password123

# Common operations
use spotifyrecs
db.tracks.countDocuments()
db.tracks.findOne()
db.tracks.getIndexes()
db.tracks.aggregate([{ $group: { _id: "$cluster_id", count: { $sum: 1 } } }])

# Drop collection
db.tracks.drop()

# Create indexes manually
db.tracks.createIndex({ "track_id": 1 }, { unique: true })
db.tracks.createIndex({ "cluster_id": 1 })
db.tracks.createIndex({ "energy": 1 })
```

### Neo4j Commands

```bash
# Connect to Neo4j Cypher shell
docker exec -it spotifyrecs-neo4j cypher-shell -u neo4j -p password123

# Common operations
MATCH (t:Track) RETURN count(t);
MATCH ()-[r:SIMILAR_TO]->() RETURN count(r);
MATCH (t:Track) RETURN t LIMIT 10;

# Delete all data
MATCH (n) DETACH DELETE n;

# Create constraint manually
CREATE CONSTRAINT track_id_unique IF NOT EXISTS FOR (t:Track) REQUIRE t.track_id IS UNIQUE;
```

### Environment Variables

All configuration is in `.env` file:

```bash
# Spotify API (optional - only for data collection)
SPOTIFY_CLIENT_ID=your_client_id
SPOTIFY_CLIENT_SECRET=your_client_secret
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8888/callback

# MongoDB
MONGO_URI=mongodb://admin:password123@localhost:27017/spotifyrecs?authSource=admin
MONGO_DB=spotifyrecs
MONGO_COLLECTION=tracks

# Neo4j
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password123

# Flask
FLASK_ENV=development
FLASK_SECRET_KEY=dev-secret-key
```

## Contributors

- **Beema Rajan** - I can be reached via email: code.beema@gmail.com.

## Additional Resources

### Documentation Links

- **Spotify Web API**: https://developer.spotify.com/documentation/web-api
- **MongoDB Documentation**: https://docs.mongodb.com/
- **Neo4j Documentation**: https://neo4j.com/docs/
- **Flask Documentation**: https://flask.palletsprojects.com/
- **Streamlit Documentation**: https://docs.streamlit.io/
- **UMAP Documentation**: https://umap-learn.readthedocs.io/

### Related Projects

- **Spotipy**: https://spotipy.readthedocs.io/
- **Neo4j Python Driver**: https://neo4j.com/docs/python-manual/current/
- **PyMongo**: https://pymongo.readthedocs.io/

### Dataset Information

- **Kaggle Dataset** created by *Juliano Orlandi*: [Spotify Top Songs and Audio Features](https://www.kaggle.com/datasets/julianoorlandi/spotify-top-songs-and-audio-features)

