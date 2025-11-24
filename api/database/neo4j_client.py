"""
Neo4j Client
Handles connection and operations for Neo4j graph database
"""

from neo4j import GraphDatabase
from neo4j.exceptions import ServiceUnavailable, AuthError
import os
from typing import List, Dict, Optional


class Neo4jClient:
    """Singleton Neo4j client"""
    
    _instance = None
    _driver = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Neo4jClient, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize Neo4j connection"""
        try:
            uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
            user = os.getenv('NEO4J_USER', 'neo4j')
            password = os.getenv('NEO4J_PASSWORD', 'password123')
            
            self._driver = GraphDatabase.driver(uri, auth=(user, password))
            
            # Test connection
            with self._driver.session() as session:
                session.run("RETURN 1")
            
            print(f"✓ Connected to Neo4j at {uri}")
            
        except (ServiceUnavailable, AuthError) as e:
            print(f"✗ Neo4j connection failed: {e}")
            self._driver = None
    
    def check_connection(self) -> bool:
        """Check if Neo4j connection is active"""
        if self._driver is None:
            return False
        try:
            with self._driver.session() as session:
                session.run("RETURN 1")
            return True
        except Exception:
            return False
    
    def close(self):
        """Close Neo4j connection"""
        if self._driver:
            self._driver.close()
    
    def create_constraints_and_indexes(self):
        """Create constraints and indexes for efficient querying"""
        queries = [
            # Uniqueness constraint on track_id
            "CREATE CONSTRAINT track_id_unique IF NOT EXISTS FOR (t:Track) REQUIRE t.track_id IS UNIQUE",
            
            # Index on cluster_id
            "CREATE INDEX track_cluster_idx IF NOT EXISTS FOR (t:Track) ON (t.cluster_id)",
            
            # Index on title for text search
            "CREATE INDEX track_title_idx IF NOT EXISTS FOR (t:Track) ON (t.title)"
        ]
        
        try:
            with self._driver.session() as session:
                for query in queries:
                    session.run(query)
            print("✓ Created Neo4j constraints and indexes")
        except Exception as e:
            print(f"✗ Failed to create constraints/indexes: {e}")
    
    # Query 5: Graph traversal to find similar tracks within N hops
    def find_similar_tracks(self, track_id: str, max_hops: int = 2, limit: int = 20) -> List[Dict]:
        """
        Find similar tracks using graph traversal
        
        Args:
            track_id: Source track ID
            max_hops: Maximum number of hops (1-3 recommended)
            limit: Maximum number of results
        
        Returns:
            List of similar tracks with similarity scores and hop distances
        """
        query = """
        MATCH path = (source:Track {track_id: $track_id})-[:SIMILAR_TO*1..""" + str(max_hops) + """]->(similar:Track)
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
        LIMIT $limit
        """
        
        try:
            with self._driver.session() as session:
                result = session.run(query, track_id=track_id, limit=limit)
                return [dict(record) for record in result]
        except Exception as e:
            print(f"Error in find_similar_tracks: {e}")
            return []
    
    # Query 6: Pattern matching for triangles of mutually similar tracks
    def find_similarity_triangles(self, min_similarity: float = 0.7, limit: int = 10) -> List[Dict]:
        """
        Find triangles of mutually similar tracks
        
        Args:
            min_similarity: Minimum similarity threshold for edges
            limit: Maximum number of triangles to return
        
        Returns:
            List of track triangles
        """
        query = """
        MATCH (a:Track)-[r1:SIMILAR_TO]-(b:Track)-[r2:SIMILAR_TO]-(c:Track)-[r3:SIMILAR_TO]-(a)
        WHERE a.track_id < b.track_id AND b.track_id < c.track_id
          AND r1.similarity >= $min_similarity
          AND r2.similarity >= $min_similarity
          AND r3.similarity >= $min_similarity
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
        LIMIT $limit
        """
        
        try:
            with self._driver.session() as session:
                result = session.run(query, min_similarity=min_similarity, limit=limit)
                return [dict(record) for record in result]
        except Exception as e:
            print(f"Error in find_similarity_triangles: {e}")
            return []
    
    # Query 7: Network centrality ranking
    def get_centrality_ranking(self, limit: int = 20, algorithm: str = 'degree') -> List[Dict]:
        """
        Rank tracks by network centrality
        
        Args:
            limit: Maximum number of results
            algorithm: Centrality algorithm ('degree', 'pagerank', 'betweenness')
        
        Returns:
            List of tracks ranked by centrality
        """
        if algorithm == 'degree':
            # Simple degree centrality (count of SIMILAR_TO relationships)
            query = """
            MATCH (t:Track)-[r:SIMILAR_TO]-()
            WITH t, count(r) as degree, avg(r.similarity) as avg_similarity
            RETURN t.track_id as track_id,
                   t.title as title,
                   t.cluster_id as cluster_id,
                   degree,
                   avg_similarity
            ORDER BY degree DESC, avg_similarity DESC
            LIMIT $limit
            """
        elif algorithm == 'pagerank':
            # PageRank using GDS library (requires GDS plugin)
            query = """
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
            LIMIT $limit
            """
        else:
            # Fallback to degree centrality
            return self.get_centrality_ranking(limit, 'degree')
        
        try:
            with self._driver.session() as session:
                result = session.run(query, limit=limit)
                return [dict(record) for record in result]
        except Exception as e:
            print(f"Error in get_centrality_ranking: {e}")
            # If GDS library not available, fallback to degree centrality
            if algorithm == 'pagerank':
                print("PageRank failed, falling back to degree centrality")
                return self.get_centrality_ranking(limit, 'degree')
            return []
    
    # Hybrid Query 8: Cluster navigation
    def get_cluster_track_ids(self, cluster_id: int) -> List[str]:
        """
        Get all track IDs in a cluster (for hybrid query with MongoDB)
        
        Args:
            cluster_id: Cluster ID
        
        Returns:
            List of track IDs in the cluster
        """
        query = """
        MATCH (t:Track {cluster_id: $cluster_id})
        RETURN t.track_id as track_id
        """
        
        try:
            with self._driver.session() as session:
                result = session.run(query, cluster_id=cluster_id)
                return [record['track_id'] for record in result]
        except Exception as e:
            print(f"Error in get_cluster_track_ids: {e}")
            return []
    
    def get_track_neighbors(self, track_id: str, limit: int = 10) -> List[Dict]:
        """
        Get direct neighbors of a track (1-hop)
        
        Args:
            track_id: Source track ID
            limit: Maximum number of neighbors
        
        Returns:
            List of neighboring tracks with similarity scores
        """
        query = """
        MATCH (source:Track {track_id: $track_id})-[r:SIMILAR_TO]-(neighbor:Track)
        RETURN neighbor.track_id as track_id,
               neighbor.title as title,
               neighbor.cluster_id as cluster_id,
               r.similarity as similarity_score
        ORDER BY r.similarity DESC
        LIMIT $limit
        """
        
        try:
            with self._driver.session() as session:
                result = session.run(query, track_id=track_id, limit=limit)
                return [dict(record) for record in result]
        except Exception as e:
            print(f"Error in get_track_neighbors: {e}")
            return []
    
    def get_graph_stats(self) -> Dict:
        """Get overall graph statistics"""
        queries = {
            'total_tracks': "MATCH (t:Track) RETURN count(t) as count",
            'total_relationships': "MATCH ()-[r:SIMILAR_TO]->() RETURN count(r) as count",
            'avg_degree': """
                MATCH (t:Track)-[r:SIMILAR_TO]-()
                WITH t, count(r) as degree
                RETURN avg(degree) as avg_degree
            """,
            'clusters': """
                MATCH (t:Track)
                RETURN DISTINCT t.cluster_id as cluster_id, count(t) as track_count
                ORDER BY cluster_id
            """
        }
        
        stats = {}
        try:
            with self._driver.session() as session:
                for key, query in queries.items():
                    result = session.run(query)
                    if key == 'clusters':
                        stats[key] = [dict(record) for record in result]
                    else:
                        record = result.single()
                        stats[key] = record[0] if record else 0
            return stats
        except Exception as e:
            print(f"Error in get_graph_stats: {e}")
            return {}
