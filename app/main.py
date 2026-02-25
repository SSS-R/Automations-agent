from fastapi import FastAPI
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    yield
    # Shutdown

app = FastAPI(title="Auto-Clipper API", lifespan=lifespan)

@app.get("/")
async def root():
    return {"message": "Auto-Clipper API is running"}
