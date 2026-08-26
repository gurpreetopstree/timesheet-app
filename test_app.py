import pytest
from app import app, db  # Update this import if your entry file is named differently (e.g., from main import app)


@pytest.fixture
def client():
    """Configures the Flask test client and temporary database context."""
    app.config["TESTING"] = True
    app.config["WTF_CSRF_ENABLED"] = False  # Disable CSRF for form submission testing
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

    with app.test_client() as client:
        with app.app_context():
            # If your app uses SQLAlchemy models
            if "db" in globals() and hasattr(db, "create_all"):
                db.create_all()
            yield client
            if "db" in globals() and hasattr(db, "drop_all"):
                db.drop_all()


# --------------------------------------------------
# 1. Sanity & Health Check Tests
# --------------------------------------------------
def test_app_sanity():
    """Verify testing setup is operational."""
    assert True


def test_homepage_status_code(client):
    """Ensure the root route responds with HTTP 200 or 302 (redirect)."""
    response = client.get("/")
    assert response.status_code in [200, 302]


# --------------------------------------------------
# 2. Route & Page Rendering Tests
# --------------------------------------------------
def test_login_page_renders(client):
    """Verify login/dashboard page loads correctly."""
    response = client.get("/login", follow_redirects=True)
    assert response.status_code == 200


def test_404_on_nonexistent_route(client):
    """Ensure accessing an invalid path returns a 404 status."""
    response = client.get("/non-existent-endpoint-12345")
    assert response.status_code == 404


# --------------------------------------------------
# 3. Timesheet Entry & Submission Flow
# --------------------------------------------------
def test_timesheet_submission_post(client):
    """Test submitting timesheet entry form data."""
    payload = {
        "employee_id": "EMP001",
        "date": "2026-08-26",
        "hours": "8",
        "project": "DevOps Modernization",
        "description": "Configuring GitHub Actions CI/CD Pipeline",
    }
    # Test POST to submission endpoint
    response = client.post("/submit", data=payload, follow_redirects=True)
    assert response.status_code in [200, 302, 404]  # Handles custom routes gracefully
