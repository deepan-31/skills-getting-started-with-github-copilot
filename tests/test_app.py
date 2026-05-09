"""Backend tests for the Mergington High School Activities API"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state before each test"""
    # Store original state
    original = {k: {"participants": v["participants"].copy()} for k, v in activities.items()}
    yield
    # Restore original state after test
    for activity_name in original:
        activities[activity_name]["participants"] = original[activity_name]["participants"]


class TestRoot:
    def test_root_redirect(self, client):
        # Arrange: prepare the test client
        
        # Act: make request to root
        response = client.get("/", follow_redirects=False)
        
        # Assert: verify redirect to static
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    def test_get_activities_returns_all_activities(self, client):
        # Arrange: prepare expected activity names
        expected_activities = [
            "Chess Club", "Programming Class", "Gym Class", 
            "Basketball Team", "Tennis Club", "Art Studio", 
            "Drama Club", "Science Olympiad", "Debate Team"
        ]
        
        # Act: fetch all activities
        response = client.get("/activities")
        activities_data = response.json()
        
        # Assert: verify all activities returned
        assert response.status_code == 200
        assert len(activities_data) == 9
        assert all(activity in activities_data for activity in expected_activities)
    
    def test_get_activities_returns_participant_info(self, client):
        # Arrange: prepare test client
        
        # Act: fetch activities
        response = client.get("/activities")
        activities_data = response.json()
        
        # Assert: verify each activity has required fields
        for activity_name, activity_info in activities_data.items():
            assert "description" in activity_info
            assert "schedule" in activity_info
            assert "max_participants" in activity_info
            assert "participants" in activity_info
            assert isinstance(activity_info["participants"], list)


class TestSignup:
    def test_signup_success(self, client, reset_activities):
        # Arrange: choose an activity and email
        activity_name = "Tennis Club"
        email = "student@example.com"
        
        # Act: signup for activity
        response = client.post(f"/activities/{activity_name}/signup?email={email}")
        
        # Assert: verify success and participant added
        assert response.status_code == 200
        assert email in activities[activity_name]["participants"]
        assert "Signed up" in response.json()["message"]
    
    def test_signup_activity_not_found(self, client):
        # Arrange: use non-existent activity
        activity_name = "Nonexistent Club"
        email = "student@example.com"
        
        # Act: attempt signup
        response = client.post(f"/activities/{activity_name}/signup?email={email}")
        
        # Assert: verify 404 error
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_signup_duplicate_email(self, client, reset_activities):
        # Arrange: use existing participant in Chess Club
        activity_name = "Chess Club"
        email = "michael@mergington.edu"  # Already in Chess Club
        
        # Act: attempt duplicate signup
        response = client.post(f"/activities/{activity_name}/signup?email={email}")
        
        # Assert: verify 400 error for duplicate
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"].lower()


class TestUnregister:
    def test_unregister_success(self, client, reset_activities):
        # Arrange: get existing participant
        activity_name = "Chess Club"
        email = "michael@mergington.edu"
        
        # Act: unregister participant
        response = client.delete(f"/activities/{activity_name}/signup?email={email}")
        
        # Assert: verify success and participant removed
        assert response.status_code == 200
        assert email not in activities[activity_name]["participants"]
        assert "Unregistered" in response.json()["message"]
    
    def test_unregister_activity_not_found(self, client):
        # Arrange: use non-existent activity
        activity_name = "Nonexistent Club"
        email = "student@example.com"
        
        # Act: attempt unregister
        response = client.delete(f"/activities/{activity_name}/signup?email={email}")
        
        # Assert: verify 404 error
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_unregister_student_not_signed_up(self, client, reset_activities):
        # Arrange: use student not in activity
        activity_name = "Chess Club"
        email = "notregistered@example.com"
        
        # Act: attempt to unregister
        response = client.delete(f"/activities/{activity_name}/signup?email={email}")
        
        # Assert: verify 400 error
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"].lower()
