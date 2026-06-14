import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from config import settings
from database import init_db
from routers import auth, notebooks, sources, prompts


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title="PromptForge API",
    description="NotebookLM-style multimodal coding prompt builder",
    version="2.0.0",
    lifespan=lifespan,
)

origins = [o.strip() for o in settings.CORS_ORIGINS.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(notebooks.router)
app.include_router(sources.router)
app.include_router(prompts.router)


@app.get("/health", tags=["meta"])
async def health():
    return {"status": "ok", "version": "2.0.0"}
