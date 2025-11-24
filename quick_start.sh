#!/bin/bash

# SpotifyRecs Quick Start Script
# This script helps you set up the project quickly

echo "================================================"
echo "SpotifyRecs - Quick Start Setup"
echo "================================================"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running"
    echo "   Please start Docker Desktop and try again"
    exit 1
fi

echo "✓ Docker is running"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "✓ Created .env file"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env file and add your Spotify credentials:"
    echo "   SPOTIFY_CLIENT_ID=your_client_id_here"
    echo "   SPOTIFY_CLIENT_SECRET=your_client_secret_here"
    echo ""
    echo "   Get credentials from: https://developer.spotify.com/dashboard"
    echo ""
    read -p "Press Enter when you've updated .env with your credentials..."
else
    echo "✓ .env file exists"
fi

echo ""
echo "================================================"
echo "Starting Docker Services"
echo "================================================"
echo ""

# Start Docker services
echo "Starting MongoDB, Neo4j, and Flask API..."
docker-compose up -d

# Wait for services to be ready
echo ""
echo "Waiting for services to be ready..."
sleep 10

# Check service health
echo ""
echo "Checking service status..."
docker-compose ps

echo ""
echo "================================================"
echo "Service URLs"
echo "================================================"
echo ""
echo "✓ MongoDB:       mongodb://localhost:27017"
echo "✓ Neo4j Browser: http://localhost:7474"
echo "   Username:      neo4j"
echo "   Password:      password123"
echo "✓ Flask API:     http://localhost:5000"
echo ""

echo "================================================"
echo "Next Steps"
echo "================================================"
echo ""
echo "1. Collect Spotify data:"
echo "   python data_collection/spotify_collector.py"
echo ""
echo "2. Process with ML:"
echo "   python ml_processing/audio_features_ml.py data/raw/spotify_tracks.json"
echo ""
echo "3. Load databases:"
echo "   python database_setup/load_mongo.py"
echo "   python database_setup/load_neo4j.py"
echo ""
echo "4. Test the API:"
echo "   curl http://localhost:5000/api/health"
echo ""
echo "================================================"
echo "Useful Commands"
echo "================================================"
echo ""
echo "View logs:           docker-compose logs -f"
echo "Stop services:       docker-compose down"
echo "Restart service:     docker-compose restart <service>"
echo "Clean everything:    docker-compose down -v"
echo ""
echo "Setup complete! 🎉"
echo ""
