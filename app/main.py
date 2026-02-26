from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pathlib import Path
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Import our new API router
from app.api.routes import router as api_router
from app.api.routes import limiter # share the limiter instance

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown

app = FastAPI(title="Auto-Clipper API", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Mount the API routes under /api
app.include_router(api_router, prefix="/api")

# Serve the static frontend web application under /
web_dir = Path("web")
web_dir.mkdir(exist_ok=True) # Ensure it exists before mounting
app.mount("/", StaticFiles(directory="web", html=True), name="web")

