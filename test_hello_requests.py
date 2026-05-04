import requests

BASE_URL = "http://127.0.0.1:8000"

def test_root():
    response = requests.get(f"{BASE_URL}/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}

def test_greet():
    response = requests.get(f"{BASE_URL}/greet/Alice")
    assert response.status_code == 200
    assert response.json() == {"greeting": "Hello Alice!"}
    