from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
from pathlib import Path


# ── Models ────────────────────────────────────────────────────

class CourseCreate(BaseModel):
    """Model for creating courses (no ID)"""
    code: str
    name: str
    semester: int
    ects: int
    lecturer: str


class Course(BaseModel):
    """Model for courses (with ID)"""
    id: int
    code: str
    name: str
    semester: int
    ects: int
    lecturer: str


# ── File Storage ──────────────────────────────────────────────

COURSES_FILE = Path("courses.json")

def load_courses():
    """Load courses from JSON file"""
    courses_db = []
    course_id_counter = 1
    if COURSES_FILE.exists():
        with open(COURSES_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            courses_db = [Course(**course) for course in data]
            if courses_db:
                course_id_counter = max(c.id for c in courses_db) + 1
    return courses_db, course_id_counter

def save_courses(courses_db):
    """Save courses to JSON file"""
    with open(COURSES_FILE, 'w', encoding='utf-8') as f:
        courses_data = [course.dict() for course in courses_db]
        json.dump(courses_data, f, indent=2, ensure_ascii=False)


# ── App ───────────────────────────────────────────────────────

app = FastAPI(
    title="StudyBuddy Course Catalog API",
    version="2.0.0"
)


# ── Endpoints ─────────────────────────────────────────────────

@app.post("/courses", status_code=201)
def create_course(course: CourseCreate) -> Course:
    """Create a new course"""
    courses_db, course_id_counter = load_courses()
    
    # Check for duplicate code
    for existing in courses_db:
        if existing.code.upper() == course.code.upper():
            raise HTTPException(
                status_code=409,
                detail=f"Course with code '{course.code}' already exists"
            )
    
    new_course = Course(
        id=course_id_counter,
        **course.dict()
    )
    courses_db.append(new_course)
    save_courses(courses_db)
    return new_course


@app.get("/courses")
def list_courses(semester: int = None, min_ects: int = 0) -> list[Course]:
    """List all courses with optional filters"""
    courses_db, _ = load_courses()
    filtered = courses_db
    if semester is not None:
        filtered = [c for c in filtered if c.semester == semester]
    if min_ects > 0:
        filtered = [c for c in filtered if c.ects >= min_ects]
    return filtered
