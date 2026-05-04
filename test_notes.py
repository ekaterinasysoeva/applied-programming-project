import requests

BASE_URL = "http://127.0.0.1:8000"


# ── CRUD Tests ────────────────────────────────────────────────

def test_create_note():
    """Test creating a new note"""
    note_data = {
        "title": "Test Note",
        "content": "Test content",
        "category": "Testing",
        "tags": ["test", "pytest"]
    }
    response = requests.post(f"{BASE_URL}/notes", json=note_data)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Note"
    assert "id" in data
    assert "created_at" in data

def test_list_notes():
    """Test listing all notes"""
    response = requests.get(f"{BASE_URL}/notes")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_note_by_id():
    """Test getting specific note by ID"""
    create_resp = requests.post(f"{BASE_URL}/notes", json={
        "title": "Note for ID test",
        "content": "Content",
        "category": "Testing",
        "tags": ["test"]
    })
    note_id = create_resp.json()["id"]
    response = requests.get(f"{BASE_URL}/notes/{note_id}")
    assert response.status_code == 200
    assert response.json()["id"] == note_id

def test_update_note():
    """Test updating a note (PUT)"""
    create_resp = requests.post(f"{BASE_URL}/notes", json={
        "title": "Original Title",
        "content": "Original content",
        "category": "Testing",
        "tags": ["test"]
    })
    note_id = create_resp.json()["id"]
    updated_data = {
        "title": "Updated Title",
        "content": "Updated content",
        "category": "Updated",
        "tags": ["updated"]
    }
    response = requests.put(f"{BASE_URL}/notes/{note_id}", json=updated_data)
    assert response.status_code == 200
    assert response.json()["title"] == "Updated Title"

def test_delete_note():
    """Test deleting a note"""
    create_resp = requests.post(f"{BASE_URL}/notes", json={
        "title": "Note to delete",
        "content": "Will be deleted",
        "category": "Testing",
        "tags": ["test"]
    })
    note_id = create_resp.json()["id"]
    response = requests.delete(f"{BASE_URL}/notes/{note_id}")
    assert response.status_code == 204
    get_resp = requests.get(f"{BASE_URL}/notes/{note_id}")
    assert get_resp.status_code == 404


# ── Filter Tests ──────────────────────────────────────────────

def test_filter_by_category():
    """Test filtering notes by category"""
    for i in range(3):
        requests.post(f"{BASE_URL}/notes", json={
            "title": f"Work Note {i}",
            "content": "Work content",
            "category": "Work",
            "tags": []
        })
    response = requests.get(f"{BASE_URL}/notes?category=Work")
    assert response.status_code == 200
    notes = response.json()
    for note in notes:
        assert note["category"] == "Work"

def test_filter_by_search():
    """Test search functionality"""
    requests.post(f"{BASE_URL}/notes", json={
        "title": "Unique Meeting Note",
        "content": "Meeting content",
        "category": "Work",
        "tags": []
    })
    response = requests.get(f"{BASE_URL}/notes?search=Unique Meeting")
    assert response.status_code == 200
    notes = response.json()
    assert len(notes) > 0

def test_filter_by_tag():
    """Test filtering by tag"""
    requests.post(f"{BASE_URL}/notes", json={
        "title": "Tagged Note",
        "content": "Content",
        "category": "Work",
        "tags": ["urgent"]
    })
    response = requests.get(f"{BASE_URL}/notes?tag=urgent")
    assert response.status_code == 200
    notes = response.json()
    for note in notes:
        assert "urgent" in note["tags"]

def test_combined_filters():
    """Test using multiple filters at once"""
    requests.post(f"{BASE_URL}/notes", json={
        "title": "Combined filter meeting",
        "content": "Content",
        "category": "Work",
        "tags": ["urgent"]
    })
    response = requests.get(
        f"{BASE_URL}/notes?category=Work&tag=urgent&search=meeting"
    )
    assert response.status_code == 200
    notes = response.json()
    for note in notes:
        assert note["category"] == "Work"
        assert "urgent" in note["tags"]


# ── Error Cases ───────────────────────────────────────────────

def test_create_note_missing_field():
    """Test creating note with missing required field"""
    invalid_note = {
        "title": "Test"
    }
    response = requests.post(f"{BASE_URL}/notes", json=invalid_note)
    assert response.status_code == 422

def test_get_nonexistent_note():
    """Test getting a note that doesn't exist"""
    response = requests.get(f"{BASE_URL}/notes/99999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

def test_update_nonexistent_note():
    """Test updating a note that doesn't exist"""
    response = requests.put(f"{BASE_URL}/notes/99999", json={
        "title": "Title",
        "content": "Content",
        "category": "Work",
        "tags": []
    })
    assert response.status_code == 404

def test_delete_nonexistent_note():
    """Test deleting a note that doesn't exist"""
    response = requests.delete(f"{BASE_URL}/notes/99999")
    assert response.status_code == 404


# ── Day 3 Features ────────────────────────────────────────────

def test_notes_statistics():
    """Test GET /notes/stats endpoint"""
    response = requests.get(f"{BASE_URL}/notes/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_notes" in data
    assert "by_category" in data
    assert "top_tags" in data

def test_patch_note():
    """Test PATCH to partially update a note"""
    create_resp = requests.post(f"{BASE_URL}/notes", json={
        "title": "Original Title",
        "content": "Original content",
        "category": "Testing",
        "tags": ["test"]
    })
    note_id = create_resp.json()["id"]
    response = requests.patch(f"{BASE_URL}/notes/{note_id}", json={
        "title": "Patched Title"
    })
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Patched Title"
    assert data["content"] == "Original content"
    

