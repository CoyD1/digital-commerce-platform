from fastapi import FastAPI
from contextlib import asynccontextmanager

from app.api.router import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Application starting...")
    yield
    print("Application shutting down...")

app = FastAPI(
    title="My API",
    description="Описание API",
    version="1.0.0",
    lifespan=lifespan
)

app.include_router(api_router)