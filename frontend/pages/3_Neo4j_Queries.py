"""
Neo4j Queries Page
Demonstrates 3 Neo4j graph query types: Graph Traversal, Pattern Matching, Centrality
"""

import streamlit as st
import sys
import os
import pandas as pd

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.database.mongo_client import MongoDBClient
from api.database.neo4j_client import Neo4jClient

st.set_page_config(page_title="Neo4j Queries - SpotifyRecs", layout="wide")

st.title("Neo4j Graph Queries")

st.markdown("""
Explore **3 graph-based query types** using Neo4j to find similar tracks and analyze the similarity network.
Neo4j stores tracks as nodes and similarity relationships as edges.
""")

# Initialize clients
@st.cache_resource
def get_mongo_client():
    return MongoDBClient()

@st.cache_resource
def get_neo4j_client():
    return Neo4jClient()

mongo_client = get_mongo_client()
neo4j_client = get_neo4j_client()

# Check connection
if not neo4j_client.check_connection():
    st.error("ERROR: Neo4j is not connected. Please check your database connection.")
    st.stop()

st.success("SUCCESS: Connected to Neo4j")

# Create tabs for different query types
tab1, tab2, tab3 = st.tabs([
    "Query 5: Graph Traversal",
    "Query 6: Triangle Patterns",
    "Query 7: Degree Centrality"
])

# ============================================================================
# QUERY 5: Graph Traversal - Find Similar Tracks
# ============================================================================
with tab1:
    st.markdown("### Query 5: Graph Traversal - Find Similar Tracks")
    st.markdown("""
    Find similar tracks by **traversing the similarity graph** up to N hops away.
    Uses Neo4j's graph traversal capabilities to discover tracks connected through similarity relationships.
    """)

    # Track ID input
    st.markdown("#### Enter Track ID")
    st.markdown("You can get track IDs from the MongoDB Queries page or use a sample ID below.")

    # Sample track IDs (you may want to fetch these dynamically)
    sample_tracks = st.checkbox("Use sample track ID", value=True)

    if sample_tracks:
        # Try to get a sample track from MongoDB
        try:
            sample_result = mongo_client.get_collection().find_one({})
            if sample_result:
                default_track_id = sample_result.get('track_id', '')
                st.info(f"Sample track: **{sample_result.get('title', 'Unknown')}** by {sample_result.get('artist', 'Unknown')}")
            else:
                default_track_id = ""
        except:
            default_track_id = ""
    else:
        default_track_id = ""

    track_id = st.text_input(
        "Track ID",
        value=default_track_id,
        placeholder="e.g., spotify:track:abc123...",
        help="Enter a Spotify track ID"
    )

    # Parameters
    col1, col2 = st.columns(2)

    with col1:
        max_hops = st.slider(
            "Maximum Hops",
            1, 3, 2,
            help="How many relationship hops to traverse (1-3 recommended)"
        )

    with col2:
        limit = st.slider(
            "Result Limit",
            5, 50, 20,
            help="Maximum number of similar tracks to return"
        )

    if st.button("Find Similar Tracks", type="primary", disabled=not track_id):
        with st.spinner("Traversing similarity graph..."):
            # Get source track details from MongoDB
            source_track = mongo_client.get_track_by_id(track_id)

            if not source_track:
                st.error(f"ERROR: Track not found: {track_id}")
            else:
                st.success(f"**Source Track:** {source_track.get('title', 'Unknown')} by {source_track.get('artist', 'Unknown')}")

                # Query Neo4j
                results = neo4j_client.find_similar_tracks(
                    track_id=track_id,
                    max_hops=max_hops,
                    limit=limit
                )

                if results:
                    st.success(f"SUCCESS: Found {len(results)} similar tracks")

                    # Convert to DataFrame
                    df = pd.DataFrame(results)

                    # Get full track details from MongoDB
                    track_ids = df['track_id'].tolist()
                    full_tracks = mongo_client.get_tracks_by_ids(track_ids)
                    tracks_map = {t['track_id']: t for t in full_tracks}

                    # Enhance with MongoDB data
                    enhanced_results = []
                    for _, row in df.iterrows():
                        tid = row['track_id']
                        if tid in tracks_map:
                            track = tracks_map[tid]
                            enhanced_results.append({
                                'Title': track.get('title', 'Unknown'),
                                'Artist': track.get('artist', 'Unknown'),
                                'Similarity Score': round(row.get('similarity_score', 0), 4),
                                'Hops': row.get('hops', 0),
                                'Cluster': row.get('cluster_id', 'N/A'),
                                'Energy': round(track.get('energy', 0), 2),
                                'Danceability': round(track.get('danceability', 0), 2),
                                'Valence': round(track.get('valence', 0), 2)
                            })

                    df_display = pd.DataFrame(enhanced_results)
                    st.dataframe(df_display, use_container_width=True, hide_index=True)

                    # Statistics
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Avg Similarity", f"{df['similarity_score'].mean():.3f}")
                    with col2:
                        st.metric("1-Hop Tracks", len(df[df['hops'] == 1]))
                    with col3:
                        st.metric("2+ Hop Tracks", len(df[df['hops'] > 1]))

                else:
                    st.warning("WARNING: No similar tracks found. The track may not have similarity relationships.")

# ============================================================================
# QUERY 6: Pattern Matching - Triangles
# ============================================================================
with tab2:
    st.markdown("### Query 6: Triangle Pattern Matching")
    st.markdown("""
    Find **triangles of mutually similar tracks** in the graph.
    A triangle consists of three tracks that are all similar to each other - useful for discovering tight-knit musical clusters.
    """)

    col1, col2 = st.columns(2)

    with col1:
        min_similarity = st.slider(
            "Minimum Similarity Threshold",
            0.0, 1.0, 0.7, 0.05,
            help="All three edges must have at least this similarity"
        )

    with col2:
        triangle_limit = st.slider(
            "Maximum Triangles to Return",
            1, 20, 10,
            help="Number of triangle patterns to find"
        )

    if st.button("Find Triangles", type="primary"):
        with st.spinner("Finding triangle patterns..."):
            results = neo4j_client.find_similarity_triangles(
                min_similarity=min_similarity,
                limit=triangle_limit
            )

            if results:
                st.success(f"SUCCESS: Found {len(results)} triangles")

                # Display results
                for i, triangle in enumerate(results, 1):
                    with st.expander(f"Triangle {i} - Avg Similarity: {triangle.get('avg_similarity', 0):.3f}"):
                        col1, col2, col3 = st.columns(3)

                        with col1:
                            st.markdown("**Track A**")
                            st.write(f"{triangle.get('track_a_title', 'Unknown')}")
                            st.caption(f"ID: {triangle.get('track_a_id', 'N/A')}")

                        with col2:
                            st.markdown("**Track B**")
                            st.write(f"{triangle.get('track_b_title', 'Unknown')}")
                            st.caption(f"ID: {triangle.get('track_b_id', 'N/A')}")

                        with col3:
                            st.markdown("**Track C**")
                            st.write(f"{triangle.get('track_c_title', 'Unknown')}")
                            st.caption(f"ID: {triangle.get('track_c_id', 'N/A')}")

                        st.markdown("**Similarity Scores:**")
                        scol1, scol2, scol3 = st.columns(3)
                        with scol1:
                            st.metric("A <-> B", f"{triangle.get('sim_ab', 0):.3f}")
                        with scol2:
                            st.metric("B <-> C", f"{triangle.get('sim_bc', 0):.3f}")
                        with scol3:
                            st.metric("C <-> A", f"{triangle.get('sim_ca', 0):.3f}")

            else:
                st.warning("WARNING: No triangles found with the specified similarity threshold. Try lowering the threshold.")

# ============================================================================
# QUERY 7: Degree Centrality Ranking
# ============================================================================
with tab3:
    st.markdown("### Query 7: Degree Centrality Ranking")
    st.markdown("""
    Rank tracks by **degree centrality** to find the most well-connected tracks in the network.
    Degree centrality counts the number of similarity relationships each track has.
    """)

    centrality_limit = st.slider(
        "Number of Top Tracks",
        5, 50, 20,
        help="How many top-ranked tracks to return"
    )

    if st.button("Get Centrality Ranking", type="primary"):
        with st.spinner("Calculating degree centrality..."):
            results = neo4j_client.get_centrality_ranking(
                limit=centrality_limit,
                algorithm="degree"
            )

            if results:
                st.success(f"SUCCESS: Found {len(results)} highly central tracks")

                # Get full track details from MongoDB
                track_ids = [r['track_id'] for r in results]
                full_tracks = mongo_client.get_tracks_by_ids(track_ids)
                tracks_map = {t['track_id']: t for t in full_tracks}

                # Enhance results
                enhanced_results = []
                for rank, result in enumerate(results, 1):
                    tid = result['track_id']
                    if tid in tracks_map:
                        track = tracks_map[tid]
                        enhanced_results.append({
                            'Rank': rank,
                            'Title': track.get('title', 'Unknown'),
                            'Artist': track.get('artist', 'Unknown'),
                            'Degree': result.get('degree', 0),
                            'Avg Similarity': round(result.get('avg_similarity', 0), 3),
                            'Cluster': result.get('cluster_id', 'N/A'),
                            'Popularity': track.get('popularity', 0)
                        })

                df_display = pd.DataFrame(enhanced_results)
                st.dataframe(df_display, use_container_width=True, hide_index=True)

                # Statistics
                col1, col2, col3 = st.columns(3)
                with col1:
                    avg_degree = sum(r['degree'] for r in results) / len(results)
                    st.metric("Avg Degree", f"{avg_degree:.1f}")
                with col2:
                    max_degree = max(r['degree'] for r in results)
                    st.metric("Max Degree", max_degree)
                with col3:
                    avg_sim = sum(r.get('avg_similarity', 0) for r in results) / len(results)
                    st.metric("Avg Similarity", f"{avg_sim:.3f}")

            else:
                st.warning("WARNING: Failed to calculate centrality. The track may not have any similarity relationships.")

st.markdown("---")
st.markdown("""
### Understanding Graph Queries

- **Query 5 (Traversal)**: Finds tracks connected through 1-3 hops in the similarity network
- **Query 6 (Triangles)**: Discovers groups of 3 mutually similar tracks
- **Query 7 (Degree Centrality)**: Identifies the most connected tracks in the network by counting similarity relationships

These queries demonstrate Neo4j's strength in relationship-based analysis!
""")
