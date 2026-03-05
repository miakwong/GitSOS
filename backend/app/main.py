from fastapi import FastAPI

app = FastAPI(title="GitSOS Backend")

@app.get("/")
def read_root():
    return {"message": "GitSOS API is running!"}

            