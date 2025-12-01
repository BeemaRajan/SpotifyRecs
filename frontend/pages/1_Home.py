"""
Home Page - Dashboard with Database Statistics
"""

import streamlit as st
import sys
import os
import pandas as pd

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.database.mongo_client import MongoDBClient
from api.database.neo4j_client import Neo4jClient

st.set_page_config(page_title="Home - SpotifyRecs", layout="wide")

st.title("Home - Dashboard")

st.markdown("""
Welcome to the **SpotifyRecs Dashboard**! This page shows the current status of the database connections
and provides an overview of the dataset statistics.
""")

# Database connection helpers
@st.cache_resource
def get_mongo_client():
    """Get MongoDB client (cached)"""
    return MongoDBClient()

@st.cache_resource
def get_neo4j_client():
    """Get Neo4j client (cached)"""
    return Neo4jClient()

# Initialize clients
mongo_client = get_mongo_client()
neo4j_client = get_neo4j_client()

# Database connection status
st.markdown("## Database Connection Status")

col1, col2 = st.columns(2)

with col1:
    mongo_status = mongo_client.check_connection()
    if mongo_status:
        st.success("SUCCESS: MongoDB Connected")
    else:
        st.error("ERROR: MongoDB Disconnected")

with col2:
    neo4j_status = neo4j_client.check_connection()
    if neo4j_status:
        st.success("SUCCESS: Neo4j Connected")
    else:
        st.error("ERROR: Neo4j Disconnected")

st.markdown("---")

# Dataset statistics
if mongo_status and neo4j_status:
    st.markdown("## Dataset Statistics")

    # Get statistics from both databases
    try:
        with st.spinner("Loading statistics..."):
            mongo_stats = mongo_client.get_dataset_stats()
            neo4j_stats = neo4j_client.get_graph_stats()

        # Overview metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            total_tracks = mongo_stats.get('total_tracks', 0)
            st.metric("Total Tracks", f"{total_tracks:,}")

        with col2:
            num_clusters = len(mongo_stats.get('clusters', []))
            st.metric("Clusters", num_clusters)

        with col3:
            total_relationships = neo4j_stats.get('total_relationships', 0)
            st.metric("Similarity Links", f"{total_relationships:,}")

        with col4:
            avg_degree = neo4j_stats.get('avg_degree', 0)
            st.metric("Avg. Connections", f"{avg_degree:.1f}")

        st.markdown("---")

        # Cluster distribution
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### Cluster Distribution (MongoDB)")
            if mongo_stats.get('clusters'):
                cluster_data = []
                for cluster in mongo_stats['clusters']:
                    cluster_data.append({
                        'Cluster ID': cluster.get('_id', 'N/A'),
                        'Track Count': cluster.get('count', 0)
                    })

                df_clusters = pd.DataFrame(cluster_data)
                st.dataframe(df_clusters, hide_index=True, use_container_width=True)

                # Bar chart
                st.bar_chart(df_clusters.set_index('Cluster ID'))
            else:
                st.info("No cluster data available")

        with col2:
            st.markdown("### Average Audio Features")
            if mongo_stats.get('average_features'):
                avg_features = mongo_stats['average_features']

                # Remove _id field
                avg_features.pop('_id', None)

                feature_data = []
                for key, value in avg_features.items():
                    if key.startswith('avg_'):
                        feature_name = key.replace('avg_', '').title()
                        feature_data.append({
                            'Feature': feature_name,
                            'Average Value': round(value, 3) if value else 0
                        })

                df_features = pd.DataFrame(feature_data)
                st.dataframe(df_features, hide_index=True, use_container_width=True)
            else:
                st.info("No feature statistics available")

        st.markdown("---")

        # Neo4j graph statistics
        st.markdown("### Graph Network Statistics (Neo4j)")

        col1, col2, col3 = st.columns(3)

        with col1:
            nodes = neo4j_stats.get('total_tracks', 0)
            st.metric("Total Nodes", f"{nodes:,}")

        with col2:
            edges = neo4j_stats.get('total_relationships', 0)
            st.metric("Total Edges", f"{edges:,}")

        with col3:
            avg_deg = neo4j_stats.get('avg_degree', 0)
            st.metric("Avg. Degree", f"{avg_deg:.2f}")

        # Cluster distribution from Neo4j
        if neo4j_stats.get('clusters'):
            st.markdown("#### Cluster Distribution (Neo4j)")
            neo4j_cluster_data = []
            for cluster in neo4j_stats['clusters']:
                neo4j_cluster_data.append({
                    'Cluster ID': cluster.get('cluster_id', 'N/A'),
                    'Track Count': cluster.get('track_count', 0)
                })

            df_neo4j_clusters = pd.DataFrame(neo4j_cluster_data)
            st.dataframe(df_neo4j_clusters, hide_index=True, use_container_width=True)

    except Exception as e:
        st.error(f"ERROR: Error loading statistics: {str(e)}")
        st.error("Make sure MongoDB and Neo4j are running and populated with data.")

else:
    st.warning("WARNING: Cannot display statistics - one or more databases are not connected.")
    st.markdown("""
    ### Troubleshooting

    **MongoDB Connection:**
    - Check that MongoDB is running: `docker-compose ps mongodb`
    - Verify connection string in environment variables
    - Default: `mongodb://admin:password123@localhost:27017/spotifyrecs?authSource=admin`

    **Neo4j Connection:**
    - Check that Neo4j is running: `docker-compose ps neo4j`
    - Verify credentials in environment variables
    - Default: `bolt://localhost:7687` (user: neo4j, password: password123)

    **Start Services:**
    ```bash
    docker-compose up -d mongodb neo4j
    ```
    """)

st.markdown("---")

st.markdown("""
### Next Steps

Use the sidebar to navigate to different query pages:
- **MongoDB Queries** - Explore document-based queries
- **Neo4j Queries** - Explore graph-based queries
- **Hybrid Queries** - Explore combined queries
""")
