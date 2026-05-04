from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def read_root():
    return {"message": "Hello World"}

@app.get("/greet/{name}")
def greet_person(name: str):
    return {"greeting": f"Hello {name}!"}
