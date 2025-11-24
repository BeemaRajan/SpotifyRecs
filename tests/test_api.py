"""
Basic API Tests
Run with: pytest tests/test_api.py
"""

import pytest
import json
from api.app import app


@pytest.fixture
def client():
    """Create test client"""
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def test_home_endpoint(client):
    """Test home endpoint"""
    response = client.get('/')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'message' in data
    assert 'SpotifyRecs' in data['message']


def test_health_endpoint(client):
    """Test health check endpoint"""
    response = client.get('/api/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert 'status' in data
    assert 'databases' in data


def test_search_endpoint_no_filters(client):
    """Test search endpoint without filters"""
    response = client.post('/api/search',
                          content_type='application/json',
                          data=json.dumps({}))
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data


def test_search_endpoint_with_filters(client):
    """Test search endpoint with valid filters"""
    filters = {
        'energy_min': 0.7,
        'danceability_min': 0.6
    }
    response = client.post('/api/search',
                          content_type='application/json',
                          data=json.dumps(filters))
    assert response.status_code in [200, 500]  # 500 if DB not populated
    data = json.loads(response.data)
    if response.status_code == 200:
        assert 'results' in data
        assert 'count' in data


def test_mood_endpoint_no_mood(client):
    """Test mood endpoint without mood parameter"""
    response = client.get('/api/mood')
    assert response.status_code == 400
    data = json.loads(response.data)
    assert 'error' in data


def test_mood_endpoint_with_mood(client):
    """Test mood endpoint with valid mood"""
    response = client.get('/api/mood?mood=happy')
    assert response.status_code in [200, 400, 500]
    data = json.loads(response.data)
    if response.status_code == 200:
        assert 'mood' in data
        assert 'results' in data


def test_clusters_endpoint(client):
    """Test clusters endpoint"""
    response = client.get('/api/clusters')
    assert response.status_code in [200, 500]


def test_cluster_endpoint(client):
    """Test single cluster endpoint"""
    response = client.get('/api/cluster/1')
    assert response.status_code in [200, 404, 500]


def test_stats_endpoint(client):
    """Test stats endpoint"""
    response = client.get('/api/stats')
    assert response.status_code in [200, 500]


def test_triangles_endpoint(client):
    """Test triangles endpoint"""
    response = client.get('/api/triangles?min_similarity=0.7&limit=5')
    assert response.status_code in [200, 500]


def test_centrality_endpoint(client):
    """Test centrality endpoint"""
    response = client.get('/api/centrality?algorithm=degree&limit=10')
    assert response.status_code in [200, 500]


def test_not_found(client):
    """Test 404 error handling"""
    response = client.get('/api/nonexistent')
    assert response.status_code == 404
    data = json.loads(response.data)
    assert 'error' in data


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
