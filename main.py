from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel, Field as PydField, field_validator, model_validator, ConfigDict
from sqlmodel import SQLModel, Field, Session, create_engine, Relationship, select, or_, col
from datetime import datetime, timezone
from collections import Counter
from typing import Optional, Annotated
from typing_extensions import Self


class NoteTagLink(SQLModel, table=True):
    """Link table for many-to-many: Note <-> Tag"""
    note_id: Optional[int] = Field(default=None, foreign_key="notes.id", primary_key=True)
    tag_id: Optional[int] = Field(default=None, foreign_key="tags.id", primary_key=True)


class Note(SQLModel, table=True):
    __tablename__ = "notes"

    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    content: str
    category: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    tags: list["Tag"] = Relationship(back_populates="notes", link_model=NoteTagLink)


class Tag(SQLModel, table=True):
    __tablename__ = "tags"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(unique=True, index=True)

    notes: list[Note] = Relationship(back_populates="tags", link_model=NoteTagLink)

    @field_validator("name")
    @classmethod
    def validate_tag_name(cls, value: str) -> str:
        value = value.strip().lower()
        if len(value) < 2 or len(value) > 30:
            raise ValueError("tag name must be 2-30 characters")
        if not all(c.isalnum() or c == '-' for c in value):
            raise ValueError("tag name must contain only lowercase letters, digits, or dashes")
        return value



engine = create_engine("sqlite:///notes.db")
SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session

SessionDep = Annotated[Session, Depends(get_session)]

ALLOWED_CATEGORIES = {"work", "personal", "school", "ideas", "general"}


class NoteCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    title: str = PydField(min_length=3, max_length=100)
    content: str = PydField(min_length=1, max_length=10000)
    category: str = PydField(min_length=2, max_length=30)
    tags: list[str] = PydField(default_factory=list, max_length=10)

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        if not value or not value.strip():
            raise ValueError("title cannot be empty or whitespace only")
        return value

    @field_validator("category")
    @classmethod
    def validate_category(cls, value: str) -> str:
        value_lower = value.lower()
        if value_lower not in ALLOWED_CATEGORIES:
            raise ValueError(f"category must be one of {sorted(ALLOWED_CATEGORIES)}")
        return value_lower

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, value: list[str]) -> list[str]:
        cleaned: list[str] = []
        seen: set[str] = set()
        for tag in value:
            t = tag.strip().lower()
            if not t:
                raise ValueError("tags cannot be empty strings")
            if len(t) < 2:
                raise ValueError("each tag must be at least 2 characters")
            if t in seen:
                continue
            seen.add(t)
            cleaned.append(t)
        return cleaned

    @model_validator(mode="after")
    def work_notes_need_work_tag(self) -> Self:
        if self.category == "work" and "work" not in self.tags:
            raise ValueError("work notes must include the 'work' tag")
        return self

class NoteUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    title: str | None = PydField(default=None, min_length=3, max_length=100)
    content: str | None = PydField(default=None, min_length=1, max_length=10000)
    category: str | None = PydField(default=None, min_length=2, max_length=30)
    tags: list[str] | None = PydField(default=None, max_length=10)

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("title cannot be empty or whitespace only")
        return value

    @field_validator("category")
    @classmethod
    def validate_category(cls, value: str | None) -> str | None:
        if value is not None:
            value_lower = value.lower()
            if value_lower not in ALLOWED_CATEGORIES:
                raise ValueError(f"category must be one of {sorted(ALLOWED_CATEGORIES)}")
            return value_lower
        return value

    @field_validator("tags")
    @classmethod
    def validate_tags(cls, value: list[str] | None) -> list[str] | None:
        if value is None:
            return None
        cleaned: list[str] = []
        seen: set[str] = set()
        for tag in value:
            t = tag.strip().lower()
            if not t:
                raise ValueError("tags cannot be empty strings")
            if len(t) < 2:
                raise ValueError("each tag must be at least 2 characters")
            if t in seen:
                continue
            seen.add(t)
            cleaned.append(t)
        return cleaned

class NoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    content: str
    category: str
    tags: list[str]
    created_at: str



app = FastAPI(
    title="Note Taking API",
    description="Simple note management",
    version="2.0.0"
)


def note_to_response(note: Note) -> NoteResponse:
    """Convert DB Note object to NoteResponse"""
    return NoteResponse(
        id=note.id,
        title=note.title,
        content=note.content,
        category=note.category,
        tags=[tag.name for tag in note.tags],
        created_at=note.created_at.isoformat()
    )

def get_or_create_tags(session: Session, tag_names: list[str]) -> list[Tag]:
    """Find existing tags or create new ones"""
    tag_objects = []
    seen = set()
    for name in tag_names:
        name_lower = name.lower().strip()
        if not name_lower or name_lower in seen:
            continue
        seen.add(name_lower)
        existing = session.exec(select(Tag).where(Tag.name == name_lower)).first()
        if existing:
            tag_objects.append(existing)
        else:
            new_tag = Tag(name=name_lower)
            session.add(new_tag)
            tag_objects.append(new_tag)
    return tag_objects


@app.get("/square/{number}")
def calculate_square(number: int):
    result = number * number
    return {
        "number": number,
        "square": result,
        "calculation": f"{number} × {number} = {result}"
    }

@app.get("/student")
def get_student():
    return {
        "name": "Ekaterina Sysoeva",
        "semester": 1,
        "course": "Wirtschaftsinformatik",
        "university": "Hochschule Coburg"
    }

@app.get("/double/{number}")
def calculate_double(number: int):
    result = number * 2
    return {
        "number": number,
        "double": result,
        "calculation": f"{number} × 2 = {result}"
    }

@app.get("/")
def root():
    return {"message": "Hello World"}

@app.get("/greet/{name}")
def greet_name(name: str):
    return {"greeting": f"Hello {name}!"}

@app.get("/number/{number}")
def calculate(number: int):
    return {"message": number * 2}



@app.post("/notes", status_code=201)
def create_note(note: NoteCreate, session: SessionDep) -> NoteResponse:
    """Create a new note"""
    db_note = Note(
        title=note.title,
        content=note.content,
        category=note.category
    )
    db_note.tags = get_or_create_tags(session, note.tags)
    session.add(db_note)
    session.commit()
    session.refresh(db_note)
    return note_to_response(db_note)



@app.get("/notes/stats")
def get_note_stats(session: SessionDep):
    """Get statistics about notes"""
    notes = session.exec(select(Note)).all()
    all_tags = [tag.name for note in notes for tag in note.tags]
    tag_counter = Counter(all_tags)
    return {
        "total_notes": len(notes),
        "by_category": dict(Counter(n.category for n in notes)),
        "top_tags": [{"tag": t, "count": c} for t, c in tag_counter.most_common(5)],
        "unique_tags_count": len(set(all_tags))
    }

@app.get("/notes")
def list_notes(
    session: SessionDep,
    category: str = None,
    search: str = None,
    tag: str = None,
    created_after: str = None,
    created_before: str = None
) -> list[NoteResponse]:
    """List notes with optional filters"""
    statement = select(Note)

    if category:
        statement = statement.where(Note.category == category)

    if search:
        search_lower = search.lower()
        statement = statement.where(
            or_(
                col(Note.title).ilike(f"%{search_lower}%"),
                col(Note.content).ilike(f"%{search_lower}%")
            )
        )

    if tag:
        statement = statement.join(Note.tags).where(Tag.name == tag.lower())

    notes = session.exec(statement).all()

    # Date filters applied after query
    if created_after:
        notes = [n for n in notes if n.created_at.isoformat() >= created_after]
    if created_before:
        notes = [n for n in notes if n.created_at.isoformat() <= created_before]

    return [note_to_response(n) for n in notes]

@app.get("/notes/{note_id}")
def get_note(note_id: int, session: SessionDep) -> NoteResponse:
    """Get a specific note by ID"""
    note = session.get(Note, note_id)
    if not note:
        raise HTTPException(status_code=404, detail=f"Note with ID {note_id} not found")
    return note_to_response(note)

@app.put("/notes/{note_id}")
def update_note(note_id: int, note_update: NoteCreate, session: SessionDep) -> NoteResponse:
    """Update an existing note (replace all fields)"""
    note = session.get(Note, note_id)
    if not note:
        raise HTTPException(status_code=404, detail=f"Note with ID {note_id} not found")
    note.title = note_update.title
    note.content = note_update.content
    note.category = note_update.category
    note.tags = get_or_create_tags(session, note_update.tags)
    session.add(note)
    session.commit()
    session.refresh(note)
    return note_to_response(note)

@app.patch("/notes/{note_id}")
def partial_update_note(note_id: int, note_update: NoteUpdate, session: SessionDep) -> NoteResponse:
    """Partially update a note (only provided fields)"""
    note = session.get(Note, note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    if note_update.title is not None:
        note.title = note_update.title
    if note_update.content is not None:
        note.content = note_update.content
    if note_update.category is not None:
        note.category = note_update.category
    if note_update.tags is not None:
        note.tags = get_or_create_tags(session, note_update.tags)
    session.add(note)
    session.commit()
    session.refresh(note)
    return note_to_response(note)

@app.delete("/notes/{note_id}", status_code=204)
def delete_note(note_id: int, session: SessionDep):
    """Delete a note"""
    note = session.get(Note, note_id)
    if not note:
        raise HTTPException(status_code=404, detail=f"Note with ID {note_id} not found")
    session.delete(note)
    session.commit()



@app.get("/tags")
def list_tags(session: SessionDep) -> list[str]:
    """Get all unique tags"""
    tags = session.exec(select(Tag)).all()
    return sorted([tag.name for tag in tags])

@app.get("/tags/{tag_name}/notes")
def get_notes_by_tag(tag_name: str, session: SessionDep) -> list[NoteResponse]:
    """Get all notes with a specific tag"""
    tag = session.exec(select(Tag).where(Tag.name == tag_name.lower())).first()
    if not tag:
        return []
    return [note_to_response(note) for note in tag.notes]


@app.get("/categories")
def list_categories(session: SessionDep) -> list[str]:
    """Get all unique categories"""
    notes = session.exec(select(Note)).all()
    return sorted({n.category for n in notes})

@app.get("/categories/{category_name}/notes")
def get_notes_by_category(category_name: str, session: SessionDep) -> list[NoteResponse]:
    """Get all notes in a specific category"""
    notes = session.exec(select(Note).where(Note.category == category_name)).all()
    return [note_to_response(n) for n in notes]



@app.get("/notes/category/{category}")
def get_notes_by_category(category: str, session: SessionDep):
    notes = session.exec(
        select(Note).where(Note.category == category)
    ).all()

    return [note_to_response(n) for n in notes]

