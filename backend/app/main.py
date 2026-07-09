from fastapi import FastAPI

# Import the database engine
from app.database import Base, engine

# Import ALL models
import app.models

# Create database tables (if they don't already exist)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Identity Resolution System",
    description="AI-assisted identity resolution backend",
    version="1.0.0"
)


@app.get("/")
def root():
    return {
        "message": "Welcome to the Identity Resolution System API"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "Identity Resolution System"
    }