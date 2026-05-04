"""
Tests for Day 2: Note Taking API
=================================

This file tests all the endpoints from Day 2.
Each endpoint has 2 simple tests.

To run: pytest tests/test_day_02.py -v
"""

from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add the reference-implementation folder so we can import main.py
sys.path.insert(0, str(Path(__file__).parent.parent / "reference-implementation"))

# Import your FastAPI app
from main import app

# Create a test client - this lets you make requests to your API
client = TestClient(app)


# ============================================================================
# Tests for POST /notes (Create a note)
# ============================================================================

def test_create_note_success():
    """Test creating a note with valid data"""
    # Create a note
    new_note = {
        "title": "Test Note",
        "content": "This is test content",
        "category": "test"
    }
    
    response = client.post("/notes", json=new_note)
    
    # Check it worked
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Note"
    assert data["content"] == "This is test content"
    assert data["category"] == "test"


def test_create_note_missing_field():
    """Test creating a note without all required fields"""
    # Try to create a note without content
    incomplete_note = {
        "title": "Incomplete",
        "category": "test"
        # Missing "content" field!
    }
    
    response = client.post("/notes", json=incomplete_note)
    
    # Should get validation error
    assert response.status_code == 422


# ============================================================================
# Tests for GET /notes (Get all notes)
# ============================================================================

def test_get_all_notes():
    """Test getting list of all notes"""
    response = client.get("/notes")
    
    # Should return a list
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_all_notes_after_creating_one():
    """Test that created notes appear in the list"""
    # Create a note first
    client.post("/notes", json={
        "title": "List Test",
        "content": "Test content",
        "category": "test"
    })
    
    # Get all notes
    response = client.get("/notes")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0


# ============================================================================
# Tests for GET /notes/{note_id} (Get specific note)
# ============================================================================

def test_get_note_by_id_success():
    """Test getting a note by its ID"""
    # Create a note first
    create_response = client.post("/notes", json={
        "title": "Get by ID Test",
        "content": "Test content",
        "category": "test"
    })
    note_id = create_response.json()["id"]
    
    # Get the note by ID
    response = client.get(f"/notes/{note_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == note_id
    assert data["title"] == "Get by ID Test"


def test_get_note_by_id_not_found():
    """Test getting a note with an ID that doesn't exist"""
    # Try to get a note with a very high ID (probably doesn't exist)
    response = client.get("/notes/99999")
    
    # Should return 404 Not Found
    assert response.status_code == 404


# ============================================================================
# Tests for GET /notes/category/{category} (Filter by category)
# ============================================================================

def test_get_notes_by_category():
    """Test filtering notes by category"""
    # Create notes in different categories
    client.post("/notes", json={
        "title": "Study Note",
        "content": "Study content",
        "category": "study"
    })
    client.post("/notes", json={
        "title": "Work Note",
        "content": "Work content",
        "category": "work"
    })
    
    # Get only study notes
    response = client.get("/notes/category/study")
    
    assert response.status_code == 200
    data = response.json()
    # All notes should be in study category
    for note in data:
        assert note["category"] == "study"


def test_get_notes_by_category_empty():
    """Test filtering by a category that has no notes"""
    response = client.get("/notes/category/nonexistent")
    
    # Should return empty list, not an error
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


# ============================================================================
# Tests for GET /notes/stats (Get statistics)
# ============================================================================

def test_get_stats():
    """Test getting note statistics"""
    response = client.get("/notes/stats")
    
    # Should return stats with correct structure
    assert response.status_code == 200
    data = response.json()
    assert "total_notes" in data
    assert "by_category" in data


def test_get_stats_after_creating_notes():
    """Test that stats reflect created notes"""
    # Create some notes
    client.post("/notes", json={
        "title": "Stats Test 1",
        "content": "Content",
        "category": "personal"
    })
    client.post("/notes", json={
        "title": "Stats Test 2",
        "content": "Content",
        "category": "personal"
    })
    
    response = client.get("/notes/stats")
    
    assert response.status_code == 200
    data = response.json()
    assert data["total_notes"] > 0
    assert isinstance(data["by_category"], dict)
