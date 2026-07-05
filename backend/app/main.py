"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.repositories.sqlite_repo import init_db
from app.routers import health, upload, documents, chat, timeline, suspects, contradictions, summary

app = FastAPI(
    title="DetectiveRAG API",
    description="RAG-powered criminal investigation workstation",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize DB on startup
@app.on_event("startup")
async def startup():
    init_db()

# Include routers
app.include_router(health.router)
app.include_router(upload.router)
app.include_router(documents.router)
app.include_router(chat.router)
app.include_router(timeline.router)
app.include_router(suspects.router)
app.include_router(contradictions.router)
app.include_router(summary.router)
