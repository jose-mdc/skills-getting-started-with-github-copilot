from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


TEST_ACTIVITY_NAME = "Test Activity"
TEST_EMAIL = "student@example.com"


@pytest.fixture(autouse=True)
def reset_activities():
    original_activities = deepcopy(activities)
    activities[TEST_ACTIVITY_NAME] = {
        "description": "An activity used in API tests",
        "schedule": "Fridays, 3:00 PM - 4:00 PM",
        "max_participants": 1,
        "participants": [],
    }

    yield

    activities.clear()
    activities.update(original_activities)


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_root_redirects_to_static_homepage(client):
    # Arrange
    path = "/"

    # Act
    response = client.get(path, follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_static_homepage_is_served(client):
    # Arrange
    path = "/static/index.html"

    # Act
    response = client.get(path)

    # Assert
    assert response.status_code == 200
    assert "Mergington High School" in response.text


def test_get_activities_returns_activity_data(client):
    # Arrange
    expected_activity = activities[TEST_ACTIVITY_NAME]

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert response.json()[TEST_ACTIVITY_NAME] == expected_activity


def test_signup_adds_participant(client):
    # Arrange
    path = f"/activities/{TEST_ACTIVITY_NAME}/signup"

    # Act
    response = client.post(path, params={"email": TEST_EMAIL})

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {TEST_EMAIL} for {TEST_ACTIVITY_NAME}"
    }
    assert TEST_EMAIL in activities[TEST_ACTIVITY_NAME]["participants"]


def test_signup_rejects_unknown_activity(client):
    # Arrange
    path = "/activities/Unknown Activity/signup"

    # Act
    response = client.post(path, params={"email": TEST_EMAIL})

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_rejects_duplicate_participant(client):
    # Arrange
    path = f"/activities/{TEST_ACTIVITY_NAME}/signup"
    client.post(path, params={"email": TEST_EMAIL})

    # Act
    response = client.post(path, params={"email": TEST_EMAIL})

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_signup_requires_email(client):
    # Arrange
    path = f"/activities/{TEST_ACTIVITY_NAME}/signup"

    # Act
    response = client.post(path)

    # Assert
    assert response.status_code == 422


def test_remove_participant_removes_signup(client):
    # Arrange
    participants = activities[TEST_ACTIVITY_NAME]["participants"]
    participants.append(TEST_EMAIL)
    path = f"/activities/{TEST_ACTIVITY_NAME}/participants/{TEST_EMAIL}"

    # Act
    response = client.delete(path)

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Removed {TEST_EMAIL} from {TEST_ACTIVITY_NAME}"
    }
    assert TEST_EMAIL not in participants


def test_remove_participant_rejects_unknown_activity(client):
    # Arrange
    path = f"/activities/Unknown Activity/participants/{TEST_EMAIL}"

    # Act
    response = client.delete(path)

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_remove_participant_rejects_unregistered_email(client):
    # Arrange
    path = f"/activities/{TEST_ACTIVITY_NAME}/participants/{TEST_EMAIL}"

    # Act
    response = client.delete(path)

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"