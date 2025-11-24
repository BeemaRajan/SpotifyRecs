# SpotifyRecs API Documentation

Base URL: `http://localhost:5000`

## Table of Contents
- [Health Check](#health-check)
- [Search Endpoints](#search-endpoints)
- [Cluster Endpoints](#cluster-endpoints)
- [Recommendation Endpoints](#recommendation-endpoints)

---

## Health Check

### GET /api/health
Check API and database connectivity status.

**Response:**
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

## Search Endpoints

### 1. POST /api/search
**Query 1: Range query on audio features**

Search tracks by audio feature ranges.

**Request Body:**
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

**Available filters:** energy, danceability, valence, tempo, acousticness, instrumentalness, liveness, speechiness, loudness, cluster_id

**Response:**
```json
{
  "count": 42,
  "filters": { "energy_min": 0.7, ... },
  "results": [
    {
      "track_id": "spotify:track:xyz",
      "title": "Song Title",
      "artist": "Artist Name",
      "energy": 0.85,
      "danceability": 0.75,
      "tempo": 128,
      "cluster_id": 3
    }
  ]
}
```

**cURL Example:**
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

### 2. GET /api/mood
**Query 3: Mood-based search**

Find tracks matching a mood profile.

**Query Parameters:**
- `mood` (required): happy, energetic, calm, sad, workout, chill

**Example:**
```
GET /api/mood?mood=happy
```

**Response:**
```json
{
  "mood": "happy",
  "count": 234,
  "results": [...]
}
```

**cURL Example:**
```bash
curl "http://localhost:5000/api/mood?mood=energetic"
```

---

### 3. GET /api/reference
**Query 4: Producer reference tracks**

Find tracks by production characteristics.

**Query Parameters:**
- `instrumentalness_min` (default: 0.5)
- `speechiness_max` (default: 0.3)
- `acousticness_min` (default: 0.0)
- `acousticness_max` (default: 1.0)

**Example:**
```
GET /api/reference?instrumentalness_min=0.6&speechiness_max=0.2
```

**Response:**
```json
{
  "count": 45,
  "filters": { ... },
  "results": [...]
}
```

**cURL Example:**
```bash
curl "http://localhost:5000/api/reference?instrumentalness_min=0.7"
```

---

### 4. GET /api/track/<track_id>
Get single track details.

**Example:**
```
GET /api/track/spotify:track:6rqhFgbbKwnb9MLmUQDhG6
```

**Response:**
```json
{
  "track_id": "spotify:track:6rqhFgbbKwnb9MLmUQDhG6",
  "title": "Song Title",
  "artist": "Artist Name",
  "energy": 0.85,
  "danceability": 0.75,
  ...
}
```

---

## Cluster Endpoints

### 5. GET /api/cluster/<cluster_id>
**Query 2 + Hybrid Query 8: Cluster statistics and track list**

Get cluster details with statistics and all tracks in the cluster.

**Example:**
```
GET /api/cluster/3
```

**Response:**
```json
{
  "cluster_id": 3,
  "statistics": {
    "count": 523,
    "avg_energy": 0.68,
    "avg_danceability": 0.72,
    "avg_valence": 0.65,
    "avg_tempo": 125.4
  },
  "track_count": 523,
  "tracks": [...]
}
```

**cURL Example:**
```bash
curl "http://localhost:5000/api/cluster/3"
```

---

### 6. GET /api/clusters
**Query 2: All cluster statistics**

Get statistics for all clusters.

**Response:**
```json
{
  "cluster_count": 10,
  "clusters": [
    {
      "cluster_id": 0,
      "count": 487,
      "avg_energy": 0.52,
      "avg_danceability": 0.61,
      ...
    }
  ]
}
```

**cURL Example:**
```bash
curl "http://localhost:5000/api/clusters"
```

---

### 7. GET /api/stats
Get overall dataset statistics from both databases.

**Response:**
```json
{
  "mongodb": {
    "total_tracks": 5234,
    "clusters": [...],
    "average_features": {...}
  },
  "neo4j": {
    "total_nodes": 5234,
    "total_relationships": 78510,
    "average_degree": 15.0
  }
}
```

**cURL Example:**
```bash
curl "http://localhost:5000/api/stats"
```

---

## Recommendation Endpoints

### 8. GET /api/recommend/<track_id>
**Query 5 + Hybrid Query 9: Graph-based recommendations**

Get recommendations using graph traversal (Neo4j) and full track details (MongoDB).

**Query Parameters:**
- `hops` (default: 2, range: 1-3): Maximum graph traversal distance
- `limit` (default: 20): Maximum number of recommendations

**Example:**
```
GET /api/recommend/spotify:track:6rqhFgbbKwnb9MLmUQDhG6?hops=2&limit=10
```

**Response:**
```json
{
  "source_track": {
    "track_id": "spotify:track:xyz",
    "title": "Source Song",
    "artist": "Artist Name",
    "energy": 0.85,
    "danceability": 0.75
  },
  "parameters": {
    "max_hops": 2,
    "limit": 10
  },
  "count": 10,
  "recommendations": [
    {
      "track_id": "spotify:track:abc",
      "title": "Similar Song",
      "artist": "Another Artist",
      "similarity_score": 0.8523,
      "hops": 1,
      ...
    }
  ]
}
```

**cURL Example:**
```bash
curl "http://localhost:5000/api/recommend/spotify:track:6rqhFgbbKwnb9MLmUQDhG6?hops=2&limit=20"
```

---

### 9. GET /api/triangles
**Query 6: Similarity triangles**

Find triangles of mutually similar tracks using pattern matching.

**Query Parameters:**
- `min_similarity` (default: 0.7): Minimum similarity threshold
- `limit` (default: 10): Maximum number of triangles

**Example:**
```
GET /api/triangles?min_similarity=0.75&limit=5
```

**Response:**
```json
{
  "parameters": {
    "min_similarity": 0.75,
    "limit": 5
  },
  "count": 5,
  "triangles": [
    {
      "track_a_id": "spotify:track:abc",
      "track_a_title": "Song A",
      "track_b_id": "spotify:track:def",
      "track_b_title": "Song B",
      "track_c_id": "spotify:track:ghi",
      "track_c_title": "Song C",
      "sim_ab": 0.85,
      "sim_bc": 0.82,
      "sim_ca": 0.79,
      "avg_similarity": 0.82
    }
  ]
}
```

**cURL Example:**
```bash
curl "http://localhost:5000/api/triangles?min_similarity=0.7&limit=10"
```

---

### 10. GET /api/centrality
**Query 7: Network centrality ranking**

Get most influential tracks by network centrality.

**Query Parameters:**
- `algorithm` (default: "degree"): "degree" or "pagerank"
- `limit` (default: 20): Number of results

**Example:**
```
GET /api/centrality?algorithm=degree&limit=10
```

**Response:**
```json
{
  "algorithm": "degree",
  "count": 10,
  "tracks": [
    {
      "track_id": "spotify:track:xyz",
      "title": "Central Track",
      "artist": "Artist Name",
      "degree": 23,
      "avg_similarity": 0.7845,
      ...
    }
  ]
}
```

**cURL Example:**
```bash
curl "http://localhost:5000/api/centrality?algorithm=pagerank&limit=20"
```

---

### 11. GET /api/similar/<track_id>
Get direct neighbors (1-hop similar tracks).

**Query Parameters:**
- `limit` (default: 10): Number of results

**Example:**
```
GET /api/similar/spotify:track:6rqhFgbbKwnb9MLmUQDhG6?limit=5
```

**Response:**
```json
{
  "source_track": {
    "track_id": "spotify:track:xyz",
    "title": "Song Title",
    "artist": "Artist"
  },
  "count": 5,
  "similar_tracks": [
    {
      "track_id": "spotify:track:abc",
      "title": "Similar Song",
      "similarity_score": 0.8923,
      ...
    }
  ]
}
```

**cURL Example:**
```bash
curl "http://localhost:5000/api/similar/spotify:track:6rqhFgbbKwnb9MLmUQDhG6?limit=10"
```

---

## Error Responses

All endpoints return appropriate HTTP status codes:
- `200`: Success
- `400`: Bad request (invalid parameters)
- `404`: Resource not found
- `500`: Internal server error

**Error Format:**
```json
{
  "error": "Error type",
  "message": "Detailed error message"
}
```

---

## Testing with Postman

1. Import the API endpoints into Postman
2. Set the base URL as a collection variable: `{{baseUrl}} = http://localhost:5000`
3. Create requests for each endpoint
4. Save example responses for documentation

---

## Rate Limiting

Currently, there are no rate limits on the API. In production, consider implementing:
- Request throttling
- API key authentication
- Usage quotas per user
