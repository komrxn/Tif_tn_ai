import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.auth import router as auth_router
from app.config import settings
from app.db import close_db, connect_db
from app.routers.broadcast import router as broadcast_router
from app.routers.dashboard import router as dashboard_router
from app.routers.errors import router as errors_router
from app.routers.requests import router as requests_router
from app.routers.usage import router as usage_router
from app.routers.users import router as users_router

logging.basicConfig(level="INFO", format="%(asctime)s %(name)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    yield
    await close_db()


app = FastAPI(title="TNVED Admin", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(dashboard_router)
app.include_router(users_router)
app.include_router(requests_router)
app.include_router(usage_router)
app.include_router(errors_router)
app.include_router(broadcast_router)

static_dir = Path(settings.static_dir)
if static_dir.exists():
    app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
else:
    logger.warning("Static dir %s does not exist — frontend not served", static_dir)
