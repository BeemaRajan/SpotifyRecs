"""
Hybrid Queries Page
Demonstrates 2 hybrid query types combining MongoDB and Neo4j
"""

import streamlit as st
import sys
import os
import pandas as pd
import plotly.express as px

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.database.mongo_client import MongoDBClient
from api.database.neo4j_client import Neo4jClient

st.set_page_config(page_title="Hybrid Queries - SpotifyRecs", layout="wide")

st.title("Hybrid Queries")

st.markdown("""
Explore **2 hybrid query types** that combine the strengths of both **MongoDB** and **Neo4j**.
These queries leverage graph relationships from Neo4j and detailed metadata from MongoDB.
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

# Check connections
mongo_status = mongo_client.check_connection()
neo4j_status = neo4j_client.check_connection()

if not (mongo_status and neo4j_status):
    st.error("ERROR: Both MongoDB and Neo4j must be connected for hybrid queries.")
    if not mongo_status:
        st.error("ERROR: MongoDB is disconnected")
    if not neo4j_status:
        st.error("ERROR: Neo4j is disconnected")
    st.stop()

st.success("SUCCESS: Connected to MongoDB and Neo4j")

# Create tabs for different query types
tab1, tab2 = st.tabs([
    "Query 8: Cluster Navigation",
    "Query 9: Hybrid Recommendations"
])

# ============================================================================
# QUERY 8: Cluster Navigation (Hybrid)
# ============================================================================
with tab1:
    st.markdown("### Query 8: Cluster Navigation (Hybrid Query)")
    st.markdown("""
    Explore tracks within a cluster by combining:
    1. **Neo4j**: Get track IDs in a cluster
    2. **MongoDB**: Fetch full track details and metadata

    This demonstrates how to navigate clusters using the graph structure and retrieve detailed information.
    """)

    # Cluster selection
    cluster_id = st.selectbox(
        "Select Cluster",
        list(range(10)),
        help="Choose a cluster to explore its tracks"
    )

    # Get cluster statistics first (from MongoDB)
    cluster_stats = mongo_client.get_cluster_stats(cluster_id)

    if cluster_stats:
        stats = cluster_stats[0]

        st.markdown("#### Cluster Statistics")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Track Count", stats.get('count', 0))
        with col2:
            st.metric("Avg Energy", f"{stats.get('avg_energy', 0):.2f}")
        with col3:
            st.metric("Avg Danceability", f"{stats.get('avg_danceability', 0):.2f}")
        with col4:
            st.metric("Avg Valence", f"{stats.get('avg_valence', 0):.2f}")

    if st.button("Explore Cluster Tracks", type="primary"):
        with st.spinner(f"Loading cluster {cluster_id} tracks..."):
            # Step 1: Get track IDs from Neo4j
            track_ids = neo4j_client.get_cluster_track_ids(cluster_id)

            if track_ids:
                st.success(f"SUCCESS: Found {len(track_ids)} tracks in cluster {cluster_id}")

                # Step 2: Get full track details from MongoDB
                tracks = mongo_client.get_tracks_by_ids(track_ids)

                if tracks:
                    # Convert to DataFrame
                    df = pd.DataFrame(tracks)

                    if '_id' in df.columns:
                        df = df.drop('_id', axis=1)

                    # Display results
                    display_cols = ['title', 'artist', 'energy', 'danceability',
                                   'valence', 'tempo', 'acousticness',
                                   'popularity', 'track_id']
                    available_cols = [col for col in display_cols if col in df.columns]

                    st.dataframe(
                        df[available_cols],
                        use_container_width=True,
                        hide_index=True
                    )

                    # Audio feature distributions
                    st.markdown("#### Audio Feature Distributions")

                    feature_configs = {
                        'energy': {'range': [0, 1], 'bins': 20},
                        'danceability': {'range': [0, 1], 'bins': 20},
                        'valence': {'range': [0, 1], 'bins': 20},
                        'acousticness': {'range': [0, 1], 'bins': 20},
                        'instrumentalness': {'range': [0, 1], 'bins': 20},
                        'tempo': {'range': [30, 250], 'bins': 22}
                    }

                    for feature, config in feature_configs.items():
                        if feature in df.columns:
                            st.markdown(f"**{feature.title()}**")
                            fig = px.histogram(
                                df,
                                x=feature,
                                nbins=config['bins'],
                                range_x=config['range']
                            )
                            fig.update_layout(
                                showlegend=False,
                                height=300,
                                xaxis_title=feature.title(),
                                yaxis_title="Count"
                            )
                            st.plotly_chart(fig, use_container_width=True)

                else:
                    st.warning("WARNING: Could not fetch track details from MongoDB")
            else:
                st.warning(f"WARNING: No tracks found in cluster {cluster_id}")

# ============================================================================
# QUERY 9: Hybrid Recommendations
# ============================================================================
with tab2:
    st.markdown("### Query 9: Hybrid Track Recommendations")
    st.markdown("""
    Get comprehensive track recommendations by combining:
    1. **Neo4j**: Find similar tracks through graph traversal
    2. **MongoDB**: Enrich results with full audio features and metadata

    This is the most powerful query type, leveraging both databases for optimal recommendations.
    """)

    # Track search/selection
    st.markdown("#### Select a Track")

    # Option to browse or enter track ID
    search_method = st.radio(
        "Search Method",
        ["Browse by Title", "Enter Track ID"],
        horizontal=True
    )

    selected_track_id = None

    if search_method == "Browse by Title":
        # Search by title
        search_query = st.text_input(
            "Search for a track by title or artist",
            placeholder="e.g., 'Bohemian Rhapsody' or 'Queen'"
        )

        if search_query:
            # Search in MongoDB using text search or simple filter
            try:
                collection = mongo_client.get_collection()
                search_results = list(collection.find({
                    "$or": [
                        {"title": {"$regex": search_query, "$options": "i"}},
                        {"artist": {"$regex": search_query, "$options": "i"}}
                    ]
                }).limit(20))

                if search_results:
                    # Create selection options
                    track_options = {
                        f"{track.get('title', 'Unknown')} - {track.get('artist', 'Unknown')}": track.get('track_id')
                        for track in search_results
                    }

                    selected_display = st.selectbox(
                        "Select a track",
                        list(track_options.keys())
                    )

                    selected_track_id = track_options[selected_display]
                else:
                    st.warning("WARNING: No tracks found. Try a different search term.")
            except Exception as e:
                st.error(f"ERROR: Search error: {str(e)}")

    else:  # Enter Track ID
        selected_track_id = st.text_input(
            "Track ID",
            placeholder="e.g., spotify:track:abc123..."
        )

    # Recommendation parameters
    col1, col2 = st.columns(2)

    with col1:
        max_hops = st.slider(
            "Maximum Graph Hops",
            1, 3, 2,
            help="How deep to traverse the similarity graph"
        )

    with col2:
        limit = st.slider(
            "Number of Recommendations",
            5, 50, 20,
            help="Maximum recommendations to return"
        )

    if st.button("Get Recommendations", type="primary", disabled=not selected_track_id):
        with st.spinner("Generating hybrid recommendations..."):
            # Step 1: Get source track from MongoDB
            source_track = mongo_client.get_track_by_id(selected_track_id)

            if not source_track:
                st.error(f"ERROR: Track not found: {selected_track_id}")
            else:
                # Display source track
                st.markdown("#### Source Track")

                col1, col2, col3, col4 = st.columns(4)

                with col1:
                    st.markdown("**Title**")
                    st.write(source_track.get('title', 'Unknown'))

                with col2:
                    st.markdown("**Artist**")
                    st.write(source_track.get('artist', 'Unknown'))

                with col3:
                    st.markdown("**Cluster**")
                    st.write(source_track.get('cluster_id', 'N/A'))

                with col4:
                    st.markdown("**Popularity**")
                    st.write(source_track.get('popularity', 'N/A'))

                # Audio features of source track
                with st.expander("View Source Track Audio Features"):
                    scol1, scol2, scol3 = st.columns(3)
                    with scol1:
                        st.metric("Energy", f"{source_track.get('energy', 0):.2f}")
                        st.metric("Danceability", f"{source_track.get('danceability', 0):.2f}")
                    with scol2:
                        st.metric("Valence", f"{source_track.get('valence', 0):.2f}")
                        st.metric("Tempo", f"{source_track.get('tempo', 0):.0f} BPM")
                    with scol3:
                        st.metric("Acousticness", f"{source_track.get('acousticness', 0):.2f}")
                        st.metric("Instrumentalness", f"{source_track.get('instrumentalness', 0):.2f}")

                st.markdown("---")

                # Step 2: Query Neo4j for similar tracks
                similar_tracks_neo4j = neo4j_client.find_similar_tracks(
                    track_id=selected_track_id,
                    max_hops=max_hops,
                    limit=limit
                )

                if not similar_tracks_neo4j:
                    st.warning("WARNING: No similar tracks found in the graph.")
                else:
                    # Step 3: Fetch full details from MongoDB
                    similar_track_ids = [t['track_id'] for t in similar_tracks_neo4j]
                    similar_tracks_full = mongo_client.get_tracks_by_ids(similar_track_ids)

                    # Create mapping
                    tracks_map = {t['track_id']: t for t in similar_tracks_full}

                    # Step 4: Combine Neo4j scores with MongoDB data
                    recommendations = []
                    for neo4j_track in similar_tracks_neo4j:
                        track_id = neo4j_track['track_id']
                        if track_id in tracks_map:
                            track = tracks_map[track_id]
                            recommendations.append({
                                'Title': track.get('title', 'Unknown'),
                                'Artist': track.get('artist', 'Unknown'),
                                'Similarity': round(neo4j_track['similarity_score'], 4),
                                'Hops': neo4j_track['hops'],
                                'Cluster': track.get('cluster_id', 'N/A'),
                                'Energy': round(track.get('energy', 0), 2),
                                'Danceability': round(track.get('danceability', 0), 2),
                                'Valence': round(track.get('valence', 0), 2),
                                'Tempo': round(track.get('tempo', 0), 0),
                                'Popularity': track.get('popularity', 0)
                            })

                    # Display recommendations
                    st.markdown("#### Recommended Tracks")
                    st.success(f"SUCCESS: Found {len(recommendations)} recommendations")

                    df_recs = pd.DataFrame(recommendations)
                    st.dataframe(df_recs, use_container_width=True, hide_index=True)

                    # Statistics
                    st.markdown("#### Recommendation Statistics")

                    col1, col2, col3, col4 = st.columns(4)

                    with col1:
                        avg_sim = df_recs['Similarity'].mean()
                        st.metric("Avg Similarity", f"{avg_sim:.3f}")

                    with col2:
                        same_cluster = len(df_recs[df_recs['Cluster'] == source_track.get('cluster_id')])
                        st.metric("Same Cluster", same_cluster)

                    with col3:
                        one_hop = len(df_recs[df_recs['Hops'] == 1])
                        st.metric("1-Hop", one_hop)

                    with col4:
                        avg_pop = df_recs['Popularity'].mean()
                        st.metric("Avg Popularity", f"{avg_pop:.0f}")

st.markdown("---")
st.markdown("""
### Understanding Hybrid Queries

- **Query 8 (Cluster Navigation)**: Uses Neo4j for cluster membership, MongoDB for full details
- **Query 9 (Recommendations)**: Uses Neo4j for similarity graph, MongoDB for rich metadata

These queries showcase the power of combining document and graph databases!
""")
