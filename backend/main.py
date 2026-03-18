from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import analyze, auth, users
from .database import Base, engine


Base.metadata.create_all(bind=engine)

app = FastAPI(title="NutriGuard AI API")

# CORS configuration for local development.
# Allow all origins temporarily for easier testing.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Versioned API paths
app.include_router(analyze.router, prefix="/api/v1", tags=["analyze"])
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(users.router, prefix="/api/v1/users", tags=["users"])


@app.get("/api/v1/health")
def health_check() -> dict:
    return {"status": "ok", "service": "NutriGuard AI"}

