"""
ML Processing Script
Performs UMAP dimensionality reduction, K-means clustering, and similarity calculation
"""

import json
import numpy as np
import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.metrics.pairwise import cosine_similarity
import umap
import os


class AudioFeatureProcessor:
    """Process audio features with ML techniques"""
    
    def __init__(self, n_clusters=10, n_neighbors=15, min_dist=0.1, 
                 similarity_threshold=0.7, top_n_similar=15):
        """
        Initialize processor
        
        Args:
            n_clusters: Number of clusters for K-means
            n_neighbors: UMAP n_neighbors parameter
            min_dist: UMAP min_dist parameter
            similarity_threshold: Minimum similarity score for edges
            top_n_similar: Number of similar tracks to keep per track
        """
        self.n_clusters = n_clusters
        self.n_neighbors = n_neighbors
        self.min_dist = min_dist
        self.similarity_threshold = similarity_threshold
        self.top_n_similar = top_n_similar
        
        # Audio features to use
        self.feature_columns = [
            'acousticness', 'danceability', 'energy', 'instrumentalness',
            'liveness', 'loudness', 'speechiness', 'tempo', 'valence'
        ]
    
    def load_data(self, json_file: str) -> pd.DataFrame:
        """Load tracks from JSON file"""
        print(f"\nLoading data from {json_file}...")
        
        with open(json_file, 'r', encoding='utf-8') as f:
            tracks = json.load(f)
        
        df = pd.DataFrame(tracks)
        print(f"✓ Loaded {len(df)} tracks")
        
        # Check for missing values
        missing = df[self.feature_columns].isnull().sum()
        if missing.any():
            print(f"\nWarning: Missing values detected:")
            print(missing[missing > 0])
            
            # Drop rows with missing audio features
            df = df.dropna(subset=self.feature_columns)
            print(f"✓ After removing incomplete tracks: {len(df)} tracks")
        
        return df
    
    def normalize_features(self, df: pd.DataFrame) -> tuple:
        """
        Normalize audio features
        
        Returns:
            Tuple of (normalized_features, scaler)
        """
        print("\nNormalizing features...")
        
        # Extract feature matrix
        features = df[self.feature_columns].values
        
        # Normalize to 0-1 scale
        scaler = StandardScaler()
        normalized = scaler.fit_transform(features)
        
        print(f"✓ Normalized {normalized.shape[1]} features")
        
        return normalized, scaler
    
    def perform_umap(self, features: np.ndarray) -> np.ndarray:
        """
        Perform UMAP dimensionality reduction
        
        Returns:
            2D embeddings
        """
        print(f"\nPerforming UMAP dimensionality reduction...")
        print(f"  Parameters: n_neighbors={self.n_neighbors}, min_dist={self.min_dist}")
        
        reducer = umap.UMAP(
            n_neighbors=self.n_neighbors,
            min_dist=self.min_dist,
            n_components=2,
            random_state=42,
            metric='euclidean'
        )
        
        embeddings = reducer.fit_transform(features)
        
        print(f"✓ Generated 2D embeddings: {embeddings.shape}")
        
        return embeddings
    
    def find_optimal_clusters(self, features: np.ndarray, k_range: range = range(2, 21)) -> dict:
        """
        Find optimal number of clusters using silhouette score

        Args:
            features: Normalized feature matrix
            k_range: Range of k values to test (default: 2 to 20)

        Returns:
            Dictionary with optimal k and all scores
        """
        print(f"\nFinding optimal number of clusters...")
        print(f"  Testing k values from {k_range.start} to {k_range.stop - 1}")

        silhouette_scores = []
        k_values = []

        for k in k_range:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            labels = kmeans.fit_predict(features)
            score = silhouette_score(features, labels)

            silhouette_scores.append(score)
            k_values.append(k)

            print(f"    k={k:2d}: silhouette={score:.4f}")

        # Find optimal k
        optimal_idx = np.argmax(silhouette_scores)
        optimal_k = k_values[optimal_idx]
        optimal_score = silhouette_scores[optimal_idx]

        print(f"\n✓ Optimal number of clusters: {optimal_k}")
        print(f"  Best silhouette score: {optimal_score:.4f}")

        return {
            'optimal_k': optimal_k,
            'optimal_score': optimal_score,
            'all_k_values': k_values,
            'all_scores': silhouette_scores
        }

    def perform_clustering(self, features: np.ndarray) -> tuple:
        """
        Perform K-means clustering

        Returns:
            Tuple of (cluster_labels, silhouette_score, kmeans_model)
        """
        print(f"\nPerforming K-means clustering...")
        print(f"  Number of clusters: {self.n_clusters}")

        kmeans = KMeans(
            n_clusters=self.n_clusters,
            random_state=42,
            n_init=10
        )

        cluster_labels = kmeans.fit_predict(features)

        # Calculate silhouette score
        sil_score = silhouette_score(features, cluster_labels)

        print(f"✓ Clustering complete")
        print(f"  Silhouette score: {sil_score:.4f}")

        # Show cluster distribution
        unique, counts = np.unique(cluster_labels, return_counts=True)
        print(f"\n  Cluster distribution:")
        for cluster_id, count in zip(unique, counts):
            print(f"    Cluster {cluster_id}: {count} tracks")

        return cluster_labels, sil_score, kmeans
    
    def calculate_similarities(self, features: np.ndarray, track_ids: list) -> list:
        """
        Calculate cosine similarity between all tracks
        Keep only top N most similar tracks per track
        
        Returns:
            List of edge dictionaries for Neo4j
        """
        print(f"\nCalculating pairwise similarities...")
        print(f"  This may take a while for large datasets...")
        
        # Calculate cosine similarity matrix
        similarity_matrix = cosine_similarity(features)
        
        # Set diagonal to 0 (track shouldn't be similar to itself)
        np.fill_diagonal(similarity_matrix, 0)
        
        edges = []
        
        # For each track, find top N most similar tracks
        for i, track_id in enumerate(track_ids):
            # Get similarity scores for this track
            similarities = similarity_matrix[i]
            
            # Get indices of top N most similar tracks
            top_indices = np.argsort(similarities)[-self.top_n_similar:][::-1]
            
            # Filter by similarity threshold
            for j in top_indices:
                sim_score = similarities[j]
                if sim_score >= self.similarity_threshold:
                    edges.append({
                        'source': track_id,
                        'target': track_ids[j],
                        'similarity': float(sim_score)
                    })
            
            # Progress update
            if (i + 1) % 500 == 0:
                print(f"  Progress: {i + 1}/{len(track_ids)} tracks processed")
        
        print(f"✓ Generated {len(edges)} similarity relationships")
        print(f"  Average edges per track: {len(edges) / len(track_ids):.2f}")
        
        return edges
    
    def process(self, input_file: str, output_dir: str = 'data/processed',
                optimize_clusters: bool = False, k_range: range = range(2, 21)):
        """
        Complete ML processing pipeline

        Args:
            input_file: Path to input JSON file
            output_dir: Directory to save processed files
            optimize_clusters: If True, find optimal number of clusters
            k_range: Range of k values to test for optimization
        """
        print("\n" + "="*60)
        print("Audio Features ML Processing Pipeline")
        print("="*60)

        # Create output directory
        os.makedirs(output_dir, exist_ok=True)

        # Load data
        df = self.load_data(input_file)

        # Normalize features
        normalized_features, scaler = self.normalize_features(df)

        # Perform UMAP
        embeddings = self.perform_umap(normalized_features)

        # Add embeddings to dataframe
        df['embedding_x'] = embeddings[:, 0]
        df['embedding_y'] = embeddings[:, 1]

        # Find optimal clusters if requested
        optimization_results = None
        if optimize_clusters:
            optimization_results = self.find_optimal_clusters(normalized_features, k_range)
            self.n_clusters = optimization_results['optimal_k']

        # Perform clustering
        cluster_labels, sil_score, kmeans = self.perform_clustering(normalized_features)
        
        # Add cluster labels to dataframe
        df['cluster_id'] = cluster_labels.astype(int)
        
        # Calculate similarities
        edges = self.calculate_similarities(
            normalized_features,
            df['track_id'].tolist()
        )
        
        # Save processed tracks for MongoDB
        print(f"\nSaving processed data...")
        
        tracks_output = os.path.join(output_dir, 'tracks_with_clusters.json')
        df.to_json(tracks_output, orient='records', indent=2)
        print(f"✓ Saved: {tracks_output}")
        
        # Save Neo4j nodes
        nodes = df[['track_id', 'title', 'artist', 'cluster_id', 'popularity']].to_dict('records')
        nodes_output = os.path.join(output_dir, 'neo4j_nodes.json')
        with open(nodes_output, 'w', encoding='utf-8') as f:
            json.dump(nodes, f, indent=2)
        print(f"✓ Saved: {nodes_output}")
        
        # Save Neo4j edges
        edges_output = os.path.join(output_dir, 'neo4j_edges.json')
        with open(edges_output, 'w', encoding='utf-8') as f:
            json.dump(edges, f, indent=2)
        print(f"✓ Saved: {edges_output}")
        
        # Save statistics
        stats = {
            'total_tracks': len(df),
            'n_clusters': self.n_clusters,
            'silhouette_score': float(sil_score),
            'total_edges': len(edges),
            'avg_edges_per_track': len(edges) / len(df),
            'umap_params': {
                'n_neighbors': self.n_neighbors,
                'min_dist': self.min_dist
            },
            'similarity_threshold': self.similarity_threshold,
            'top_n_similar': self.top_n_similar
        }

        # Add optimization results if available
        if optimization_results:
            stats['optimization'] = {
                'optimized': True,
                'optimal_k': optimization_results['optimal_k'],
                'optimal_score': optimization_results['optimal_score'],
                'tested_k_values': optimization_results['all_k_values'],
                'all_silhouette_scores': optimization_results['all_scores']
            }
        else:
            stats['optimization'] = {'optimized': False}
        
        stats_output = os.path.join(output_dir, 'processing_stats.json')
        with open(stats_output, 'w') as f:
            json.dump(stats, f, indent=2)
        print(f"✓ Saved: {stats_output}")
        
        print("\n" + "="*60)
        print("Processing complete!")
        print(f"  Total tracks: {len(df)}")
        print(f"  Clusters: {self.n_clusters}")
        print(f"  Silhouette score: {sil_score:.4f}")
        print(f"  Similarity edges: {len(edges)}")
        print("="*60 + "\n")
        
        print("Next steps:")
        print("  1. Load MongoDB: python database_setup/load_mongo.py")
        print("  2. Load Neo4j: python database_setup/load_neo4j.py")
        print("  3. Start API: python api/app.py")


def main():
    """Main execution"""
    import argparse

    parser = argparse.ArgumentParser(description='Process audio features with ML')
    parser.add_argument('input', help='Input JSON file')
    parser.add_argument('--output', default='data/processed', help='Output directory')
    parser.add_argument('--clusters', type=int, default=10, help='Number of clusters (ignored if --optimize-clusters is used)')
    parser.add_argument('--neighbors', type=int, default=15, help='UMAP n_neighbors')
    parser.add_argument('--min-dist', type=float, default=0.1, help='UMAP min_dist')
    parser.add_argument('--threshold', type=float, default=0.7, help='Similarity threshold')
    parser.add_argument('--top-n', type=int, default=15, help='Top N similar tracks')
    parser.add_argument('--optimize-clusters', action='store_true',
                        help='Automatically find optimal number of clusters using silhouette score')
    parser.add_argument('--k-min', type=int, default=2, help='Minimum k to test when optimizing (default: 2)')
    parser.add_argument('--k-max', type=int, default=21, help='Maximum k to test when optimizing (default: 21)')

    args = parser.parse_args()

    processor = AudioFeatureProcessor(
        n_clusters=args.clusters,
        n_neighbors=args.neighbors,
        min_dist=args.min_dist,
        similarity_threshold=args.threshold,
        top_n_similar=args.top_n
    )

    processor.process(
        args.input,
        args.output,
        optimize_clusters=args.optimize_clusters,
        k_range=range(args.k_min, args.k_max)
    )


if __name__ == '__main__':
    main()
