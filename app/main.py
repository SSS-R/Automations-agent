from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pathlib import Path

# Import our new API router
from app.api.routes import router as api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown

app = FastAPI(title="Auto-Clipper API", lifespan=lifespan)

# Mount the API routes under /api
app.include_router(api_router, prefix="/api")

# Serve the static frontend web application under /
web_dir = Path("web")
web_dir.mkdir(exist_ok=True) # Ensure it exists before mounting
app.mount("/", StaticFiles(directory="web", html=True), name="web")

