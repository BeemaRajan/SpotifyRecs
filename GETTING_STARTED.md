# Getting Started with SpotifyRecs

This guide will walk you through setting up and running the SpotifyRecs project from scratch.

## Prerequisites

Before you begin, make sure you have:

1. **Docker Desktop** installed and running
   - Download from: https://www.docker.com/products/docker-desktop
   - Minimum 4GB RAM allocated to Docker

2. **Python 3.11+** installed
   - Download from: https://www.python.org/downloads/
   - Verify: `python --version`

3. **Git** (to clone your repository)
   - Download from: https://git-scm.com/downloads

4. **Spotify Developer Account**
   - Sign up at: https://developer.spotify.com/dashboard
   - You'll need this to get API credentials

## Step-by-Step Setup

### 1. Get Spotify API Credentials

1. Go to https://developer.spotify.com/dashboard
2. Log in with your Spotify account
3. Click "Create app"
4. Fill in the details:
   - App name: "SpotifyRecs"
   - App description: "Music recommendation system"
   - Redirect URI: http://localhost:8888/callback (required but not used)
   - Check the Developer Terms of Service
5. Click "Save"
6. On your app's page, click "Settings"
7. Copy your **Client ID** and **Client Secret**
8. Keep these safe - you'll need them in the next step!

### 2. Clone and Setup Environment

```bash
# Navigate to your project directory
cd /path/to/your/project

# Create .env file from template
cp .env.example .env

# Edit .env file with your credentials
# Replace YOUR_CLIENT_ID and YOUR_CLIENT_SECRET with the values from step 1
nano .env  # or use your favorite text editor
```

Your `.env` file should look like:
```
SPOTIFY_CLIENT_ID=abc123...
SPOTIFY_CLIENT_SECRET=xyz789...
```

### 3. Start Docker Services

**Option A: Quick Start Script** (Recommended)
```bash
chmod +x quick_start.sh
./quick_start.sh
```

**Option B: Manual Start**
```bash
# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f
```

**Verify services are running:**
- MongoDB: `docker exec -it spotifyrecs-mongodb mongosh -u admin -p password123`
- Neo4j Browser: Open http://localhost:7474 (neo4j/password123)
- Flask API: `curl http://localhost:5000/api/health`

### 4. Install Python Dependencies

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

### 5. Collect Spotify Data

```bash
# Run the data collector
python data_collection/spotify_collector.py

# When prompted:
# - Press 'n' to use the default example playlists (recommended for first run)
# - Or press 'y' to enter your own Spotify playlist IDs

# This will:
# - Collect ~5,000-7,000 tracks
# - Fetch audio features for each track
# - Save to data/raw/spotify_tracks.json
# - Take approximately 10-15 minutes
```

**Expected output file:** `data/raw/spotify_tracks.json` (~15-20 MB)

### 6. Process with Machine Learning

```bash
# Run the ML processing pipeline
python ml_processing/audio_features_ml.py data/raw/spotify_tracks.json

# This will:
# - Normalize audio features
# - Perform UMAP dimensionality reduction
# - Run K-means clustering
# - Calculate pairwise similarities
# - Generate processed files
# - Take approximately 5-10 minutes

# Output files:
# - data/processed/tracks_with_clusters.json (for MongoDB)
# - data/processed/neo4j_nodes.json (for Neo4j nodes)
# - data/processed/neo4j_edges.json (for Neo4j relationships)
# - data/processed/processing_stats.json (statistics)
```

### 7. Load Databases

```bash
# Load MongoDB
python database_setup/load_mongo.py

# Expected output:
# ✓ Connected to MongoDB
# ✓ Loaded 5234 tracks
# ✓ Inserted 5234 tracks
# ✓ Created indexes

# Load Neo4j
python database_setup/load_neo4j.py

# Expected output:
# ✓ Connected to Neo4j
# ✓ Loaded 5234 track nodes
# ✓ Loaded ~78,000 similarity relationships
```

### 8. Test the API

```bash
# Test health endpoint
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
```

### 9. Explore with Neo4j Browser

1. Open http://localhost:7474
2. Login: neo4j / password123
3. Try these queries:

```cypher
// View all tracks
MATCH (t:Track)
RETURN t
LIMIT 25

// View similarity graph
MATCH (a:Track)-[r:SIMILAR_TO]->(b:Track)
RETURN a, r, b
LIMIT 50

// Find similar tracks
MATCH path = (t:Track {title: 'YOUR_SONG_TITLE'})-[:SIMILAR_TO*1..2]-(similar:Track)
RETURN similar.title, length(path) as hops
LIMIT 10
```

## Project Structure Verification

After setup, your project should look like:

```
SpotifyRecs/
├── api/
│   ├── app.py                    # ✓ Flask application
│   ├── routes/                   # ✓ API endpoints
│   └── database/                 # ✓ DB clients
├── data/
│   ├── raw/
│   │   └── spotify_tracks.json   # ✓ Collected data
│   └── processed/
│       ├── tracks_with_clusters.json  # ✓ Processed data
│       ├── neo4j_nodes.json      # ✓ Neo4j nodes
│       └── neo4j_edges.json      # ✓ Neo4j edges
├── data_collection/
│   └── spotify_collector.py      # ✓ Data collector
├── ml_processing/
│   └── audio_features_ml.py      # ✓ ML pipeline
├── database_setup/
│   ├── load_mongo.py             # ✓ MongoDB loader
│   └── load_neo4j.py             # ✓ Neo4j loader
├── docker-compose.yml            # ✓ Docker services
├── requirements.txt              # ✓ Python packages
└── .env                          # ✓ Your credentials
```

## Troubleshooting

### Docker Issues

**Problem:** Docker services won't start
```bash
# Check Docker is running
docker info

# View logs
docker-compose logs

# Restart services
docker-compose restart

# Clean slate (removes all data!)
docker-compose down -v
docker-compose up -d
```

**Problem:** Port already in use (27017, 7474, 7687, or 5000)
```bash
# Find what's using the port (example for 27017)
# On Mac/Linux:
lsof -i :27017
# On Windows:
netstat -ano | findstr :27017

# Either stop that service or change port in docker-compose.yml
```

### Database Connection Issues

**Problem:** MongoDB connection failed
```bash
# Check MongoDB is running
docker-compose ps mongodb

# Test connection
docker exec -it spotifyrecs-mongodb mongosh -u admin -p password123

# If that works, check MONGO_URI in .env
```

**Problem:** Neo4j connection failed
```bash
# Check Neo4j is running
docker-compose ps neo4j

# View logs
docker-compose logs neo4j

# Try browser: http://localhost:7474
# Credentials: neo4j / password123
```

### Data Collection Issues

**Problem:** Spotify API authentication failed
```bash
# Verify credentials in .env:
cat .env | grep SPOTIFY

# Make sure there are no extra spaces or quotes
# Should look like:
# SPOTIFY_CLIENT_ID=abc123
# SPOTIFY_CLIENT_SECRET=xyz789
```

**Problem:** Rate limit exceeded
```bash
# Wait a few minutes and try again
# Spotify free tier has rate limits

# Or reduce the number of playlists in spotify_collector.py
```

### ML Processing Issues

**Problem:** Out of memory during processing
```bash
# Reduce dataset size or increase Docker memory
# Docker Desktop > Settings > Resources > Memory

# Or process in batches by modifying ml_processing script
```

**Problem:** UMAP/scikit-learn import errors
```bash
# Reinstall dependencies
pip uninstall umap-learn scikit-learn
pip install umap-learn scikit-learn
```

## Next Steps

Once everything is working:

1. **Test all 9 queries** (see docs/QUERIES.md)
2. **Take screenshots** of successful API calls
3. **Export Neo4j visualizations**
4. **Document your results** in README.md
5. **Prepare your presentation**

## Getting Help

- Check the README.md for detailed documentation
- Review API.md for endpoint details
- See QUERIES.md for query examples
- Check Docker logs: `docker-compose logs -f`
- Verify services: `docker-compose ps`

## Quick Reference

**Start everything:**
```bash
docker-compose up -d
```

**Stop everything:**
```bash
docker-compose down
```

**View logs:**
```bash
docker-compose logs -f [service-name]
```

**Access services:**
- API: http://localhost:5000
- Neo4j: http://localhost:7474
- MongoDB: mongodb://admin:password123@localhost:27017

**Run the full pipeline:**
```bash
# 1. Collect data
python data_collection/spotify_collector.py

# 2. Process with ML
python ml_processing/audio_features_ml.py data/raw/spotify_tracks.json

# 3. Load databases
python database_setup/load_mongo.py
python database_setup/load_neo4j.py

# 4. Test API
curl http://localhost:5000/api/health
```

Good luck with your project! 🎵
