from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.database import engine, Base
import app.models
from app.core.config import settings
from app.routes import companies, scans, content, contacts, financial, outreach, articles, youtube, executive, images, website_scanner, publish

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize Database Tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(
    title="EX Venture Platform API",
    description="Backend API for EX Venture Management Platform",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(companies.router)
app.include_router(scans.router)
app.include_router(content.router)
app.include_router(contacts.router)
app.include_router(financial.router)
app.include_router(outreach.router)
app.include_router(articles.router)
app.include_router(youtube.router)
app.include_router(executive.router)
app.include_router(images.router)
app.include_router(website_scanner.router)
app.include_router(publish.router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@app.get("/")
async def root():
    """API root endpoint."""
    return {"message": "EX Venture Platform API"}
