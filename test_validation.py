from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_create_note_rejects_short_title():
    response = client.post("/notes", json={
        "title": "ab",
        "content": "content",
        "category": "personal",
        "tags": []
    })
    assert response.status_code == 422


def test_create_note_rejects_unknown_category():
    response = client.post("/notes", json={
        "title": "Valid Title",
        "content": "content",
        "category": "banana",
        "tags": []
    })
    assert response.status_code == 422


def test_create_note_normalizes_tags():
    response = client.post("/notes", json={
        "title": "Test Note",
        "content": "content",
        "category": "personal",
        "tags": ["URGENT", "urgent", "  meeting  "]
    })
    assert response.status_code == 201
    data = response.json()
    assert set(data["tags"]) == {"urgent", "meeting"}


def test_create_note_forbids_extra_fields():
    response = client.post("/notes", json={
        "title": "Test Note",
        "content": "content",
        "category": "personal",
        "tags": [],
        "typo_field": "should fail"
    })
    assert response.status_code == 422


def test_work_note_requires_work_tag():
    response = client.post("/notes", json={
        "title": "Work Note",
        "content": "content",
        "category": "work",
        "tags": ["urgent"]
    })
    assert response.status_code == 422


def test_patch_with_empty_body_succeeds():
    create_resp = client.post("/notes", json={
        "title": "Test Note",
        "content": "content",
        "category": "personal",
        "tags": []
    })
    note_id = create_resp.json()["id"]
    
    response = client.patch(f"/notes/{note_id}", json={})
    assert response.status_code == 200


def test_patch_with_invalid_title_fails():
    create_resp = client.post("/notes", json={
        "title": "Test Note",
        "content": "content",
        "category": "personal",
        "tags": []
    })
    note_id = create_resp.json()["id"]
    
    response = client.patch(f"/notes/{note_id}", json={"title": ""})
    assert response.status_code == 422


def test_tag_name_rejects_uppercase():
    response = client.post("/notes", json={
        "title": "Test Note",
        "content": "content",
        "category": "personal",
        "tags": ["UPPERCASE"]
    })
    assert response.status_code == 201
    data = response.json()
    assert data["tags"] == ["uppercase"]
