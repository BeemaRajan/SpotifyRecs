"""
SpotifyRecs Streamlit Frontend
Main entry point for the multi-page Streamlit application
"""

import streamlit as st
import sys
import os

# Add parent directory to path to import api modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Page configuration
st.set_page_config(
    page_title="SpotifyRecs - Music Recommendation System",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(90deg, #1DB954, #191414);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .sub-header {
        text-align: center;
        color: #888;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    .stButton>button {
        width: 100%;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# Main welcome page
st.markdown("""
## Welcome to SpotifyRecs!

This interactive application demonstrates a **hybrid NoSQL database architecture** combining:
- **MongoDB** for document-based track storage with rich audio features
- **Neo4j** for graph-based similarity relationships
- **Machine Learning** for clustering and similarity detection

### Available Query Types

#### MongoDB Queries (4)
1. **Range Query** - Search tracks by audio feature ranges
2. **Aggregation** - Cluster statistics and analysis
3. **Mood Search** - Find tracks matching specific moods
4. **Reference Tracks** - Producer reference track finder

#### Neo4j Queries (3)
5. **Graph Traversal** - Find similar tracks through network hops
6. **Pattern Matching** - Discover triangles of mutually similar tracks
7. **Centrality Ranking** - Identify influential tracks in the network

#### Hybrid Queries (2)
8. **Cluster Navigation** - Explore tracks within clusters
9. **Recommendations** - Combined MongoDB + Neo4j recommendations

### Getting Started

Use the **sidebar** on the left to navigate between different query types and explore the recommendation system!

### Dataset Features

Each track includes **13 audio features**:
- Energy, Danceability, Valence (happiness)
- Tempo, Loudness, Acousticness
- Instrumentalness, Liveness, Speechiness
- And more...

---

*Built with Streamlit, MongoDB, Neo4j, and scikit-learn*
""")

# Sidebar navigation info
with st.sidebar:
    st.markdown("## Navigation")
    st.markdown("""
    Select a page above to explore:

    - **Home** - This page
    - **MongoDB Queries** - Document database queries
    - **Neo4j Queries** - Graph database queries
    - **Hybrid Queries** - Combined queries
    """)

    st.markdown("---")

    st.markdown("## About")
    st.markdown("""
    **SpotifyRecs** is a music recommendation system built for demonstrating
    NoSQL database capabilities in a real-world application.

    **Technologies:**
    - Python 3.11+
    - MongoDB 7.0
    - Neo4j 5.15
    - Streamlit
    - scikit-learn (UMAP + K-means)
    """)
