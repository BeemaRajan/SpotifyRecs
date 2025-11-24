# Query Examples for SpotifyRecs

This document demonstrates all 9 queries required for the final project.

## MongoDB Queries (4 queries)

### Query 1: Range Query on Audio Features

**Description:** Find tracks by audio feature ranges

**MongoDB Query:**
```javascript
db.tracks.find({
    "energy": { "$gte": 0.7, "$lte": 1.0 },
    "danceability": { "$gte": 0.6 },
    "tempo": { "$gte": 120, "$lte": 140 }
}).limit(20)
```

**API Endpoint:**
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

**Use Case:** Finding high-energy dance tracks with moderate tempo for a workout playlist

---

### Query 2: Aggregation Pipeline for Cluster Statistics

**Description:** Calculate average audio features by cluster

**MongoDB Query:**
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

**API Endpoint:**
```bash
# All clusters
curl http://localhost:5000/api/clusters

# Specific cluster
curl http://localhost:5000/api/cluster/3
```

**Use Case:** Understanding the sonic characteristics of different clusters

---

### Query 3: Mood-Based Search

**Description:** Find tracks matching mood profiles (happy, energetic, calm, sad, workout, chill)

**MongoDB Query (Happy):**
```javascript
db.tracks.find({
    "valence": { "$gte": 0.6 },
    "energy": { "$gte": 0.5 }
}).limit(50)
```

**API Endpoint:**
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

**Use Case:** Creating mood-specific playlists for different activities

---

### Query 4: Producer Reference Tracks

**Description:** Find tracks by production characteristics

**MongoDB Query:**
```javascript
db.tracks.find({
    "instrumentalness": { "$gte": 0.5 },
    "speechiness": { "$lte": 0.3 },
    "acousticness": { "$gte": 0.0, "$lte": 1.0 }
}).sort({ "popularity": -1 }).limit(50)
```

**API Endpoint:**
```bash
curl "http://localhost:5000/api/reference?instrumentalness_min=0.5&speechiness_max=0.3"

# More specific search
curl "http://localhost:5000/api/reference?instrumentalness_min=0.7&acousticness_min=0.4&acousticness_max=0.7"
```

**Use Case:** Music producers finding reference tracks with specific production qualities

---

## Neo4j Queries (3 queries)

### Query 5: Graph Traversal for Similar Tracks

**Description:** Find similar tracks within N hops using graph traversal

**Cypher Query (2-hop):**
```cypher
MATCH path = (source:Track {track_id: 'spotify:track:6rqhFgbbKwnb9MLmUQDhG6'})
             -[:SIMILAR_TO*1..2]-(similar:Track)
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

**API Endpoint:**
```bash
# 2-hop traversal
curl "http://localhost:5000/api/recommend/spotify:track:6rqhFgbbKwnb9MLmUQDhG6?hops=2&limit=20"

# 1-hop (direct neighbors)
curl "http://localhost:5000/api/recommend/spotify:track:6rqhFgbbKwnb9MLmUQDhG6?hops=1&limit=10"

# 3-hop (wider network)
curl "http://localhost:5000/api/recommend/spotify:track:6rqhFgbbKwnb9MLmUQDhG6?hops=3&limit=20"
```

**Use Case:** Finding "similar to similar" recommendations through the similarity network

---

### Query 6: Triangle Pattern Matching

**Description:** Find triangles of mutually similar tracks

**Cypher Query:**
```cypher
MATCH (a:Track)-[r1:SIMILAR_TO]-(b:Track)-[r2:SIMILAR_TO]-(c:Track)-[r3:SIMILAR_TO]-(a)
WHERE a.track_id < b.track_id AND b.track_id < c.track_id
  AND r1.similarity >= 0.7
  AND r2.similarity >= 0.7
  AND r3.similarity >= 0.7
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

**API Endpoint:**
```bash
curl "http://localhost:5000/api/triangles?min_similarity=0.7&limit=10"

# Higher similarity threshold
curl "http://localhost:5000/api/triangles?min_similarity=0.8&limit=5"
```

**Use Case:** Discovering tight clusters of highly similar tracks

---

### Query 7: Network Centrality Ranking

**Description:** Rank tracks by network centrality (degree or PageRank)

**Cypher Query (Degree Centrality):**
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

**Cypher Query (PageRank - requires GDS plugin):**
```cypher
CALL gds.pageRank.stream({
    nodeProjection: 'Track',
    relationshipProjection: {
        SIMILAR_TO: {
            type: 'SIMILAR_TO',
            properties: 'similarity'
        }
    },
    relationshipWeightProperty: 'similarity'
})
YIELD nodeId, score
WITH gds.util.asNode(nodeId) as track, score
RETURN track.track_id as track_id,
       track.title as title,
       track.cluster_id as cluster_id,
       score
ORDER BY score DESC
LIMIT 20
```

**API Endpoint:**
```bash
# Degree centrality
curl "http://localhost:5000/api/centrality?algorithm=degree&limit=20"

# PageRank centrality (if GDS is available)
curl "http://localhost:5000/api/centrality?algorithm=pagerank&limit=20"
```

**Use Case:** Finding the most "influential" tracks in the similarity network

---

## Hybrid Queries (2 queries)

### Hybrid Query 8: Cluster Navigation

**Description:** Query Neo4j for cluster track IDs, then fetch full details from MongoDB

**Neo4j Part:**
```cypher
MATCH (t:Track {cluster_id: 3})
RETURN t.track_id as track_id
```

**MongoDB Part:**
```javascript
db.tracks.find({
    "track_id": { "$in": [/* track IDs from Neo4j */] }
})
```

**API Endpoint:**
```bash
curl "http://localhost:5000/api/cluster/3"
```

**Use Case:** Exploring all tracks in a sonic cluster with full metadata

---

### Hybrid Query 9: Recommendation Engine

**Description:** Query Neo4j for similar track IDs via graph traversal, then fetch full details from MongoDB

**Neo4j Part (Graph Traversal):**
```cypher
MATCH path = (source:Track {track_id: 'spotify:track:xyz'})-[:SIMILAR_TO*1..2]-(similar:Track)
RETURN similar.track_id as track_id, 
       length(path) as hops,
       reduce(score = 1.0, rel in relationships(path) | score * rel.similarity) as similarity_score
ORDER BY similarity_score DESC
LIMIT 20
```

**MongoDB Part:**
```javascript
db.tracks.find({
    "track_id": { "$in": [/* track IDs from Neo4j */] }
})
```

**API Endpoint:**
```bash
curl "http://localhost:5000/api/recommend/spotify:track:6rqhFgbbKwnb9MLmUQDhG6?hops=2&limit=20"
```

**Use Case:** Complete recommendation system combining graph relationships with full track metadata

---

## Testing All Queries

### MongoDB Shell Testing

```bash
# Connect to MongoDB
mongosh "mongodb://admin:password123@localhost:27017/spotifyrecs?authSource=admin"

# Run queries
use spotifyrecs

// Query 1
db.tracks.find({ "energy": { "$gte": 0.7 }, "tempo": { "$gte": 120 } }).limit(5)

// Query 2
db.tracks.aggregate([{ $group: { _id: "$cluster_id", count: { $sum: 1 } } }])

// Query 3
db.tracks.find({ "valence": { "$gte": 0.6 }, "energy": { "$gte": 0.5 } }).limit(5)

// Query 4
db.tracks.find({ "instrumentalness": { "$gte": 0.5 } }).limit(5)
```

### Neo4j Browser Testing

```bash
# Access Neo4j Browser
# http://localhost:7474
# Username: neo4j
# Password: password123

# Run queries in Neo4j Browser:

// Query 5 - Find similar tracks (replace with actual track_id)
MATCH path = (t:Track {track_id: 'spotify:track:YOUR_TRACK_ID'})-[:SIMILAR_TO*1..2]-(similar:Track)
RETURN similar.title, length(path) as hops
LIMIT 10

// Query 6 - Find triangles
MATCH (a:Track)-[r1:SIMILAR_TO]-(b:Track)-[r2:SIMILAR_TO]-(c:Track)-[r3:SIMILAR_TO]-(a)
WHERE a.track_id < b.track_id AND b.track_id < c.track_id
RETURN a.title, b.title, c.title, r1.similarity, r2.similarity, r3.similarity
LIMIT 5

// Query 7 - Centrality
MATCH (t:Track)-[r:SIMILAR_TO]-()
WITH t, count(r) as degree
RETURN t.title, degree
ORDER BY degree DESC
LIMIT 10
```

### API Testing Script

```bash
#!/bin/bash

BASE_URL="http://localhost:5000"

echo "Testing all API endpoints..."

# Query 1
echo "1. Range query"
curl -X POST "$BASE_URL/api/search" \
  -H "Content-Type: application/json" \
  -d '{"energy_min": 0.7, "tempo_min": 120}'

# Query 2
echo "2. Cluster statistics"
curl "$BASE_URL/api/clusters"

# Query 3
echo "3. Mood search"
curl "$BASE_URL/api/mood?mood=happy"

# Query 4
echo "4. Reference tracks"
curl "$BASE_URL/api/reference?instrumentalness_min=0.5"

# Query 5 + Hybrid Query 9
echo "5. Recommendations"
curl "$BASE_URL/api/recommend/[TRACK_ID]?hops=2"

# Query 6
echo "6. Triangles"
curl "$BASE_URL/api/triangles"

# Query 7
echo "7. Centrality"
curl "$BASE_URL/api/centrality?algorithm=degree"

# Hybrid Query 8
echo "8. Cluster navigation"
curl "$BASE_URL/api/cluster/3"
```

---

## Performance Notes

- **MongoDB Queries**: Fast with proper indexes (~10-50ms)
- **Neo4j 1-hop**: Very fast (~5-20ms)
- **Neo4j 2-hop**: Moderate (~20-100ms)
- **Neo4j 3-hop**: Slower (~100-500ms)
- **Triangle matching**: Can be slow on large graphs (~100-1000ms)
- **Centrality calculations**: Moderate to slow depending on graph size

---

## Query Optimization Tips

1. **MongoDB**: Create compound indexes for common query patterns
2. **Neo4j**: Use relationship direction wisely
3. **Hybrid queries**: Fetch only needed fields from MongoDB
4. **Caching**: Consider caching frequently accessed results
5. **Pagination**: Always limit result set sizes
