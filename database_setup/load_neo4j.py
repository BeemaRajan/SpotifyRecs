"""
Neo4j Database Loader
Loads track nodes and similarity relationships into Neo4j
"""

import json
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Neo4jLoader:
    """Loads data into Neo4j graph database"""
    
    def __init__(self):
        """Initialize Neo4j connection"""
        uri = os.getenv('NEO4J_URI', 'bolt://localhost:7687')
        user = os.getenv('NEO4J_USER', 'neo4j')
        password = os.getenv('NEO4J_PASSWORD', 'password123')
        
        try:
            self.driver = GraphDatabase.driver(uri, auth=(user, password))
            # Test connection
            with self.driver.session() as session:
                session.run("RETURN 1")
            print("✓ Connected to Neo4j\n")
        except Exception as e:
            print(f"✗ Failed to connect to Neo4j: {e}")
            print("\nMake sure Neo4j is running:")
            print("  docker-compose up -d neo4j")
            raise
    
    def close(self):
        """Close Neo4j connection"""
        if self.driver:
            self.driver.close()
    
    def clear_database(self):
        """Clear all nodes and relationships"""
        print("Step 1: Clearing existing data...")
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
        print("✓ Database cleared\n")
    
    def create_constraints(self):
        """Create constraints and indexes"""
        print("Step 2: Creating constraints and indexes...")
        
        queries = [
            "CREATE CONSTRAINT track_id_unique IF NOT EXISTS FOR (t:Track) REQUIRE t.track_id IS UNIQUE",
            "CREATE INDEX track_cluster_idx IF NOT EXISTS FOR (t:Track) ON (t.cluster_id)",
            "CREATE INDEX track_title_idx IF NOT EXISTS FOR (t:Track) ON (t.title)"
        ]
        
        with self.driver.session() as session:
            for query in queries:
                try:
                    session.run(query)
                except Exception as e:
                    print(f"  Warning: {e}")
        
        print("✓ Constraints and indexes created\n")
    
    def load_nodes(self, nodes_file: str):
        """
        Load track nodes from JSON file
        
        Args:
            nodes_file: Path to nodes JSON file
        """
        print("Step 3: Loading track nodes...")
        
        # Load nodes data
        with open(nodes_file, 'r', encoding='utf-8') as f:
            nodes = json.load(f)
        
        print(f"  Found {len(nodes)} nodes to load")
        
        # Batch create nodes (500 at a time for efficiency)
        batch_size = 500
        with self.driver.session() as session:
            for i in range(0, len(nodes), batch_size):
                batch = nodes[i:i + batch_size]
                
                query = """
                UNWIND $nodes AS node
                CREATE (t:Track {
                    track_id: node.track_id,
                    title: node.title,
                    artist: node.artist,
                    cluster_id: node.cluster_id,
                    popularity: node.popularity
                })
                """
                
                session.run(query, nodes=batch)
                
                if (i + batch_size) % 2000 == 0:
                    print(f"  Progress: {min(i + batch_size, len(nodes))}/{len(nodes)} nodes")
        
        print(f"✓ Loaded {len(nodes)} track nodes\n")
    
    def load_relationships(self, edges_file: str):
        """
        Load similarity relationships from JSON file
        
        Args:
            edges_file: Path to edges JSON file
        """
        print("Step 4: Loading similarity relationships...")
        
        # Load edges data
        with open(edges_file, 'r', encoding='utf-8') as f:
            edges = json.load(f)
        
        print(f"  Found {len(edges)} relationships to load")
        
        # Batch create relationships (500 at a time)
        batch_size = 500
        with self.driver.session() as session:
            for i in range(0, len(edges), batch_size):
                batch = edges[i:i + batch_size]
                
                query = """
                UNWIND $edges AS edge
                MATCH (a:Track {track_id: edge.source})
                MATCH (b:Track {track_id: edge.target})
                CREATE (a)-[:SIMILAR_TO {similarity: edge.similarity}]->(b)
                """
                
                session.run(query, edges=batch)
                
                if (i + batch_size) % 2000 == 0:
                    print(f"  Progress: {min(i + batch_size, len(edges))}/{len(edges)} relationships")
        
        print(f"✓ Loaded {len(edges)} similarity relationships\n")
    
    def verify_data(self):
        """Verify loaded data"""
        print("Step 5: Verifying data...")
        
        with self.driver.session() as session:
            # Count nodes
            result = session.run("MATCH (t:Track) RETURN count(t) as count")
            node_count = result.single()['count']
            print(f"✓ Total nodes: {node_count}")
            
            # Count relationships
            result = session.run("MATCH ()-[r:SIMILAR_TO]->() RETURN count(r) as count")
            rel_count = result.single()['count']
            print(f"✓ Total relationships: {rel_count}")
            
            # Calculate average degree
            result = session.run("""
                MATCH (t:Track)-[r:SIMILAR_TO]-()
                WITH t, count(r) as degree
                RETURN avg(degree) as avg_degree
            """)
            avg_degree = result.single()['avg_degree']
            print(f"✓ Average degree: {avg_degree:.2f}")
            
            # Cluster distribution
            result = session.run("""
                MATCH (t:Track)
                RETURN t.cluster_id as cluster, count(t) as count
                ORDER BY cluster
            """)
            
            print("\nCluster distribution:")
            for record in result:
                print(f"  Cluster {record['cluster']}: {record['count']} nodes")
            
            # Sample nodes with their connections
            result = session.run("""
                MATCH (t:Track)-[r:SIMILAR_TO]-()
                WITH t, count(r) as connections
                RETURN t.track_id as track_id, 
                       t.title as title, 
                       t.artist as artist,
                       connections
                ORDER BY connections DESC
                LIMIT 3
            """)
            
            print("\nMost connected tracks:")
            for i, record in enumerate(result, 1):
                print(f"  [{i}] {record['title']} - {record['artist']}")
                print(f"      Connections: {record['connections']}")


def load_neo4j(nodes_file: str = 'data/processed/neo4j_nodes.json',
               edges_file: str = 'data/processed/neo4j_edges.json'):
    """
    Main function to load Neo4j database
    
    Args:
        nodes_file: Path to nodes JSON file
        edges_file: Path to edges JSON file
    """
    print("\n" + "="*60)
    print("Neo4j Database Loader")
    print("="*60 + "\n")
    
    # Check if files exist
    if not os.path.exists(nodes_file):
        print(f"✗ Error: Nodes file not found: {nodes_file}")
        print("\nPlease run the ML processing notebook first to generate:")
        print("  - neo4j_nodes.json")
        print("  - neo4j_edges.json")
        return
    
    if not os.path.exists(edges_file):
        print(f"✗ Error: Edges file not found: {edges_file}")
        print("\nPlease run the ML processing notebook first to generate:")
        print("  - neo4j_nodes.json")
        print("  - neo4j_edges.json")
        return
    
    try:
        # Initialize loader
        loader = Neo4jLoader()
        
        # Clear database
        loader.clear_database()
        
        # Create constraints
        loader.create_constraints()
        
        # Load nodes
        loader.load_nodes(nodes_file)
        
        # Load relationships
        loader.load_relationships(edges_file)
        
        # Verify data
        loader.verify_data()
        
        print("\n" + "="*60)
        print("Neo4j loading complete!")
        print("="*60)
        print("\nYou can now:")
        print("  1. Access Neo4j Browser: http://localhost:7474")
        print("  2. Test the Flask API: python api/app.py")
        print("  3. Run example queries in Neo4j Browser:")
        print("")
        print("     // Find similar tracks (2-hop)")
        print("     MATCH path = (t:Track {track_id: 'YOUR_TRACK_ID'})")
        print("                  -[:SIMILAR_TO*1..2]-(similar:Track)")
        print("     RETURN similar, length(path) as hops")
        print("     LIMIT 20")
        print("")
        
        # Close connection
        loader.close()
        
    except Exception as e:
        print(f"\n✗ Error: {e}")
        return


if __name__ == '__main__':
    import sys
    
    # Check for custom file paths
    if len(sys.argv) > 2:
        nodes_file = sys.argv[1]
        edges_file = sys.argv[2]
    else:
        nodes_file = 'data/processed/neo4j_nodes.json'
        edges_file = 'data/processed/neo4j_edges.json'
    
    load_neo4j(nodes_file, edges_file)
