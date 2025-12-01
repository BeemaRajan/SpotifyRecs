"""
MongoDB Queries Page
Demonstrates 4 MongoDB query types: Range, Aggregation, Mood, Reference Tracks
"""

import streamlit as st
import sys
import os
import pandas as pd
import plotly.express as px

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.database.mongo_client import MongoDBClient

st.set_page_config(page_title="MongoDB Queries - SpotifyRecs", layout="wide")

st.title("MongoDB Queries")

st.markdown("""
Explore **4 different MongoDB query types** to search and analyze tracks based on audio features.
MongoDB stores all track metadata including 13 audio features per track.
""")

# Initialize MongoDB client
@st.cache_resource
def get_mongo_client():
    return MongoDBClient()

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_tempo_range(_mongo_client):
    """Get the min and max tempo from the entire dataset."""
    collection = _mongo_client.get_collection()
    pipeline = [
        {
            "$group": {
                "_id": None,
                "min_tempo": {"$min": "$tempo"},
                "max_tempo": {"$max": "$tempo"}
            }
        }
    ]
    result = list(collection.aggregate(pipeline))
    if result:
        return result[0]['min_tempo'], result[0]['max_tempo']
    return 60, 200  # Fallback defaults

@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_cluster_ids(_mongo_client):
    """Get all distinct cluster IDs from the database."""
    collection = _mongo_client.get_collection()
    cluster_ids = collection.distinct("cluster_id")
    # Sort cluster IDs numerically
    return sorted([int(c) for c in cluster_ids if c is not None])

mongo_client = get_mongo_client()

# Check connection
if not mongo_client.check_connection():
    st.error("ERROR: MongoDB is not connected. Please check your database connection.")
    st.stop()

st.success("SUCCESS: Connected to MongoDB")

# Get available cluster IDs from database
cluster_ids = get_cluster_ids(mongo_client)

# Create tabs for different query types
tab1, tab2, tab3, tab4 = st.tabs([
    "Query 1: Range Search",
    "Query 2: Cluster Statistics",
    "Query 3: Mood Search",
    "Query 4: Reference Tracks"
])

# ============================================================================
# QUERY 1: Range Search by Audio Features
# ============================================================================
with tab1:
    st.markdown("### Query 1: Search by Audio Features (Range Query)")
    st.markdown("""
    Search for tracks by specifying ranges for audio features.
    Demonstrates MongoDB's **range query** capabilities with multiple indexed fields.
    """)

    # Create two columns for sliders
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### Energy & Danceability")
        energy_range = st.slider(
            "Energy (0=low energy, 1=high energy)",
            0.0, 1.0, (0.5, 1.0), 0.05,
            help="Energy represents the intensity and activity level"
        )

        danceability_range = st.slider(
            "Danceability (0=not danceable, 1=very danceable)",
            0.0, 1.0, (0.5, 1.0), 0.05,
            help="How suitable a track is for dancing"
        )

        valence_range = st.slider(
            "Valence/Happiness (0=sad, 1=happy)",
            0.0, 1.0, (0.0, 1.0), 0.05,
            help="Musical positiveness conveyed by a track"
        )

    with col2:
        st.markdown("#### Tempo & Other Features")
        tempo_range = st.slider(
            "Tempo (BPM)",
            0, 250, (100, 150), 5,
            help="The speed or pace of the track"
        )

        acousticness_range = st.slider(
            "Acousticness (0=electric, 1=acoustic)",
            0.0, 1.0, (0.0, 1.0), 0.05,
            help="Confidence that the track is acoustic"
        )

        instrumentalness_range = st.slider(
            "Instrumentalness (0=vocals, 1=instrumental)",
            0.0, 1.0, (0.0, 1.0), 0.05,
            help="Predicts whether a track contains no vocals"
        )

    # Optional cluster filter
    cluster_filter = st.selectbox(
        "Filter by Cluster (optional)",
        ["All Clusters"] + cluster_ids,
        help="Narrow results to a specific cluster"
    )

    # Search button
    if st.button("Search Tracks", type="primary"):
        with st.spinner("Searching tracks..."):
            # Build filters
            filters = {
                "energy_min": energy_range[0],
                "energy_max": energy_range[1],
                "danceability_min": danceability_range[0],
                "danceability_max": danceability_range[1],
                "valence_min": valence_range[0],
                "valence_max": valence_range[1],
                "tempo_min": tempo_range[0],
                "tempo_max": tempo_range[1],
                "acousticness_min": acousticness_range[0],
                "acousticness_max": acousticness_range[1],
                "instrumentalness_min": instrumentalness_range[0],
                "instrumentalness_max": instrumentalness_range[1],
            }

            if cluster_filter != "All Clusters":
                filters["cluster_id"] = cluster_filter

            # Execute query
            results = mongo_client.search_by_features(filters)

            if results:
                st.success(f"SUCCESS: Found {len(results)} matching tracks")

                # Convert to DataFrame
                df = pd.DataFrame(results)

                # Remove MongoDB _id
                if '_id' in df.columns:
                    df = df.drop('_id', axis=1)

                # Select columns to display
                display_cols = ['title', 'artist', 'energy', 'danceability',
                               'valence', 'tempo', 'acousticness',
                               'instrumentalness', 'cluster_id', 'popularity']

                available_cols = [col for col in display_cols if col in df.columns]

                # Display results
                st.dataframe(
                    df[available_cols].head(50),
                    use_container_width=True,
                    hide_index=True
                )

            else:
                st.warning("WARNING: No tracks found matching your criteria. Try adjusting the filters.")

# ============================================================================
# QUERY 2: Cluster Statistics (Aggregation)
# ============================================================================
with tab2:
    st.markdown("### Query 2: Cluster Statistics (Aggregation Pipeline)")
    st.markdown("""
    View statistics for track clusters using MongoDB's **aggregation pipeline**.
    Shows average audio features and track counts per cluster.
    """)

    cluster_option = st.selectbox(
        "Select Cluster",
        ["All Clusters"] + cluster_ids
    )

    if st.button("Get Cluster Statistics", type="primary"):
        with st.spinner("Calculating statistics..."):
            # Get cluster stats
            if cluster_option == "All Clusters":
                stats = mongo_client.get_cluster_stats()
            else:
                stats = mongo_client.get_cluster_stats(cluster_option)

            if stats:
                # Convert to DataFrame
                df_stats = pd.DataFrame(stats)

                # Rename _id to cluster_id
                if '_id' in df_stats.columns:
                    df_stats = df_stats.rename(columns={'_id': 'cluster_id'})

                st.success(f"SUCCESS: Retrieved statistics for {len(stats)} cluster(s)")

                # Display statistics table
                st.dataframe(df_stats, use_container_width=True, hide_index=True)

                # Visualizations (only for single cluster selection)
                if len(stats) == 1:  # Single cluster
                    st.markdown("#### Audio Feature Profile")

                    # Get dataset-wide tempo range for normalization
                    min_tempo, max_tempo = get_tempo_range(mongo_client)

                    feature_data = []
                    tempo_original = None

                    for col in df_stats.columns:
                        if col.startswith('avg_') and col != 'avg_popularity':
                            feature_name = col.replace('avg_', '').title()
                            value = df_stats.iloc[0][col]

                            # Normalize tempo to 0-1 scale for visualization
                            if col == 'avg_tempo':
                                tempo_original = value
                                if max_tempo > min_tempo:
                                    normalized_value = (value - min_tempo) / (max_tempo - min_tempo)
                                    normalized_value = max(0, min(1, normalized_value))  # Clamp to 0-1
                                else:
                                    normalized_value = 0.5  # Fallback if all tempos are the same
                                feature_data.append({
                                    'Feature': 'Tempo (normalized)',
                                    'Value': round(normalized_value, 3)
                                })
                            else:
                                feature_data.append({
                                    'Feature': feature_name,
                                    'Value': round(value, 3)
                                })

                    df_features = pd.DataFrame(feature_data)
                    st.bar_chart(df_features.set_index('Feature'))

                    # Add explanation
                    if tempo_original is not None:
                        st.caption(
                            f"Note: Tempo is normalized to 0-1 scale for visualization comparability. "
                            f"Dataset range: {min_tempo:.0f}-{max_tempo:.0f} BPM. "
                            f"Actual cluster tempo: {tempo_original:.1f} BPM."
                        )

            else:
                st.warning("WARNING: No statistics available for the selected cluster.")

# ============================================================================
# QUERY 3: Mood-Based Search
# ============================================================================
with tab3:
    st.markdown("### Query 3: Mood-Based Search")
    st.markdown("""
    Find tracks matching specific moods using **predefined audio feature profiles**.
    Each mood is defined by a combination of audio feature ranges.
    """)

    # Mood selection
    mood_options = {
        "happy": "Happy - High valence and energy",
        "energetic": "Energetic - High energy and tempo",
        "calm": "Calm - Low energy, acoustic",
        "sad": "Sad - Low valence and energy",
        "workout": "Workout - High energy, danceable, fast",
        "chill": "Chill - Low energy, acoustic, instrumental"
    }

    selected_mood = st.selectbox(
        "Select a Mood",
        list(mood_options.keys()),
        format_func=lambda x: mood_options[x]
    )

    # Show mood profile
    mood_profiles = {
        'happy': {'valence_min': 0.9, 'energy_min': 0.7},
        'energetic': {'energy_min': 0.7, 'tempo_min': 150},
        'calm': {'energy_max': 0.4, 'valence_min': 0.3, 'acousticness_min': 0.4},
        'sad': {'valence_max': 0.4, 'energy_max': 0.5},
        'workout': {'energy_min': 0.8, 'danceability_min': 0.6, 'tempo_min': 120},
        'chill': {'energy_max': 0.5, 'acousticness_min': 0.3, 'instrumentalness_min': 0.3}
    }

    st.info(f"**Profile:** {mood_profiles.get(selected_mood, {})}")

    if st.button("Find Tracks", type="primary"):
        with st.spinner(f"Finding {selected_mood} tracks..."):
            results = mongo_client.search_by_mood(selected_mood)

            if results:
                st.success(f"SUCCESS: Found {len(results)} {selected_mood} tracks")

                # Convert to DataFrame
                df = pd.DataFrame(results)

                if '_id' in df.columns:
                    df = df.drop('_id', axis=1)

                # Display results
                display_cols = ['title', 'artist', 'energy', 'danceability',
                               'valence', 'tempo', 'acousticness', 'popularity']
                available_cols = [col for col in display_cols if col in df.columns]

                st.dataframe(
                    df[available_cols].head(50),
                    use_container_width=True,
                    hide_index=True
                )

                # Statistics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Avg Energy", f"{df['energy'].mean():.2f}")
                with col2:
                    st.metric("Avg Valence", f"{df['valence'].mean():.2f}")
                with col3:
                    st.metric("Avg Tempo", f"{df['tempo'].mean():.0f} BPM")

            else:
                st.warning(f"WARNING: No {selected_mood} tracks found.")

# ============================================================================
# QUERY 4: Producer Reference Tracks
# ============================================================================
with tab4:
    st.markdown("### Query 4: Producer Reference Tracks")
    st.markdown("""
    Find **instrumental tracks** suitable for producers looking for reference material or samples.
    Uses compound queries on instrumentalness, speechiness, and acousticness.
    """)

    col1, col2 = st.columns(2)

    with col1:
        instrumentalness_min = st.slider(
            "Minimum Instrumentalness",
            0.0, 1.0, 0.5, 0.05,
            help="Higher values = more instrumental, less vocals"
        )

        speechiness_max = st.slider(
            "Maximum Speechiness",
            0.0, 1.0, 0.3, 0.05,
            help="Lower values = less spoken word content"
        )

    with col2:
        acousticness_min = st.slider(
            "Minimum Acousticness",
            0.0, 1.0, 0.0, 0.05,
            help="Higher values = more acoustic"
        )

        acousticness_max = st.slider(
            "Maximum Acousticness",
            0.0, 1.0, 1.0, 0.05,
            help="Lower values = more electronic"
        )

    if st.button("Find Reference Tracks", type="primary"):
        with st.spinner("Searching for reference tracks..."):
            results = mongo_client.find_reference_tracks(
                instrumentalness_min=instrumentalness_min,
                speechiness_max=speechiness_max,
                acousticness_range=(acousticness_min, acousticness_max)
            )

            if results:
                st.success(f"SUCCESS: Found {len(results)} reference tracks")

                # Convert to DataFrame
                df = pd.DataFrame(results)

                if '_id' in df.columns:
                    df = df.drop('_id', axis=1)

                # Display results
                display_cols = ['title', 'artist', 'instrumentalness',
                               'speechiness', 'acousticness', 'energy',
                               'popularity', 'cluster_id']
                available_cols = [col for col in display_cols if col in df.columns]

                st.dataframe(
                    df[available_cols].head(50),
                    use_container_width=True,
                    hide_index=True
                )

                # Statistics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Avg Instrumentalness", f"{df['instrumentalness'].mean():.2f}")
                with col2:
                    st.metric("Avg Speechiness", f"{df['speechiness'].mean():.2f}")
                with col3:
                    st.metric("Avg Acousticness", f"{df['acousticness'].mean():.2f}")

            else:
                st.warning("WARNING: No reference tracks found matching your criteria.")

st.markdown("---")
st.markdown("""
### Tips
- Use **Query 1** for precise feature-based searches
- Use **Query 2** to understand cluster characteristics
- Use **Query 3** for quick mood-based discoveries
- Use **Query 4** for finding instrumental/production music
""")
