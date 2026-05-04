# ============================================================================
# DAY 4: Advanced API Features
# ============================================================================
# Goal: Write and run tests for our APIs
#       - Use pytest to write unit tests for our API endpoints
#       - Use FastAPI's TestClient to simulate API requests
#       - Use Requests library to test API endpoints from outside the app
# Topics: Testing FastAPI applications, pytest, TestClient, Requests library
# ============================================================================

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
import json
from pathlib import Path

# Create FastAPI application
app = FastAPI(
    title="Applied Programming Course API",
    description="Reference implementation for Day 4",
    version="1.0.0"
)

# ----------------------------------------------------------------------------
# PYDANTIC MODELS
# ----------------------------------------------------------------------------

class GreetingResponse(BaseModel):
    """Response model for greeting endpoints

    Attributes:
        message (str): The greeting message to be returned to the client
    """
    message: str

# ----------------------------------------------------------------------------
# DAY 4: API ENDPOINTS FOR TESTING
# ----------------------------------------------------------------------------

@app.get("/", response_model=GreetingResponse)
def read_root():
    """Welcome endpoint - returns greeting message"""
    return {"message": "Hello World!"}




@app.get("/greetings/{name}", response_model=GreetingResponse)
def read_greeting(name: str):
    """Personalized greeting endpoint - returns greeting message with name"""
    return {"message": f"Hello {name}!"}


# ----------------------------------------------------------------------------
# BUGGY ENDPOINT - For Teaching Purposes
# ----------------------------------------------------------------------------

@app.get("/is-adult/{age}")
def check_adult(age: int):
    """
    Check if person is an adult (18 or older)
    Example: /is-adult/17
    """
    is_adult = age > 18

    return {
        "age": age,
        "is_adult": is_adult,
        "can_vote": is_adult,
        "can_drive": is_adult
    }

 