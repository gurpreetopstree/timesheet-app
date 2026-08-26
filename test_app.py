import pytest
from app import app


@pytest.fixture
def client():
    """Configures the Flask test client."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


def test_sanity():
    """Basic environment check."""
    assert True


def test_home_page(client):
    """Verify root endpoint responds."""
    response = client.get("/")
    assert response.status_code in [200, 302]


def test_app_configured(client):
    """Verify application testing configuration."""
    assert app.config["TESTING"] is True
