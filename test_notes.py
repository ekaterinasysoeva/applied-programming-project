import requests

BASE_URL = "http://127.0.0.1:8000"


def test_create_note():
    """Test creating a new note"""
    # Arrange - prepare test data
    note_data = {
        "title": "Test Note",
        "content": "Test content",
        "category": "Testing",
        "tags": ["test", "pytest"]
    }

  
    response = requests.post(f"{BASE_URL}/notes", json=note_data)

    assert response.status_code == 201
    assert response.json()["title"] == "Test Note"


def test_list_notes():
    """Test listing all notes"""
    response = requests.get(f"{BASE_URL}/notes")

    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_get_nonexistent_note():
    """Test getting a note that doesn't exist"""
    response = requests.get(f"{BASE_URL}/notes/99999")

    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_filter_by_category():
    """Test filtering notes by category"""
    response = requests.get(f"{BASE_URL}/notes?category=Work")

    assert response.status_code == 200
    notes = response.json()

    # All returned notes should be in Work category
    for note in notes:
        assert note["category"] == "Work"

