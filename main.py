from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime, timezone
import json
from pathlib import Path

app = FastAPI(
    title="Note Taking API",
    description="Simple note management",
    version="1.0.0"
)

@app.get("/")
def root():
    return {"message": "Hello, World!"}

@app.get("/name/{name}")
def greet_name(name: str):
    return {"message": f"Hello, {name}!"}

@app.get("/number/{number}")
def calculate(number: str):
    return {"message": (number*2)}


####################################
### Note API Endpoints (Day 2)
####################################

class NoteCreate(BaseModel):
    title: str
    content: str
    category: str

class Note(BaseModel):
    id: int
    title: str
    content: str
    category: str
    created_at: str

NOTES_FILE = Path("data/notes.json")

def load_notes():
    """Load notes from JSON file and return notes list and next ID counter"""
    notes_db = []
    note_id_counter = 1

    if NOTES_FILE.exists():
        with open(NOTES_FILE, 'r') as f:
            data = json.load(f)
            notes_db = [Note(**note) for note in data]

            # Set counter to max ID + 1
            if notes_db:
                note_id_counter = max(note.id for note in notes_db) + 1

    return notes_db, note_id_counter


def save_notes(notes_db):
    """Save notes to JSON file after each change"""
    # Ensure data directory exists
    NOTES_FILE.parent.mkdir(parents=True, exist_ok=True)

    with open(NOTES_FILE, 'w') as f:
        # Convert Note objects to dicts
        notes_data = [note.dict() for note in notes_db]
        json.dump(notes_data, f, indent=2)

@app.post("/notes", status_code=201)
def create_note(note: NoteCreate) -> Note:
    """Create a new note"""
    notes_db, note_id_counter = load_notes()

    new_note = Note(
        id=note_id_counter,
        title=note.title,
        content=note.content,
        category=note.category,
        created_at=datetime.now(timezone.utc).isoformat()
    )
    notes_db.append(new_note)
    save_notes(notes_db)

    return new_note

@app.get("/notes")
def list_notes() -> list[Note]:
    """Get a list of all notes"""
    notes_db, _ = load_notes()
    return notes_db

@app.get("/notes/{note_id}")
def get_note(note_id: int):
    """Get a specific note by ID"""
    notes_db, _ = load_notes()
    for note in notes_db:
        if note.id == note_id:
            return note
    
    # Not found - raise 404 error
    raise HTTPException(
        status_code=404,
        detail=f"Note with ID {note_id} not found"
    )





