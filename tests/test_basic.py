def test_home_page(client):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/' page is requested (GET)
    THEN check that the response is valid
    """
    response = client.get('/')
    assert response.status_code == 200

def test_privacy_page(client):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/privacy' page is requested (GET)
    THEN check that the response is valid
    """
    response = client.get('/privacy')
    assert response.status_code == 200

def test_terms_page(client):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/terms' page is requested (GET)
    THEN check that the response is valid
    """
    response = client.get('/terms')
    assert response.status_code == 200
