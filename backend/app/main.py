import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router, source

load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await source.ensure_loaded()
    yield


app = FastAPI(title="SoleMate API", lifespan=lifespan)

allowed_origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5174",
]

env_origins = os.getenv("CORS_ORIGINS")
if env_origins:
    allowed_origins.extend([o.strip() for o in env_origins.split(",") if o.strip()])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health() -> dict[str, bool]:
    return {"ok": True}


app.include_router(router, prefix="/api")
