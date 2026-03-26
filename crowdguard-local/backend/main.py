from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import os
from dotenv import load_dotenv

load_dotenv()

from auth.routes   import router as auth_router
from zones.routes  import router as zones_router
from alerts.routes import router as alerts_router
from ws.routes     import router as ws_router
from database      import connect_db, disconnect_db
import simulator

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_db()
    asyncio.create_task(simulator.run())
    yield
    await disconnect_db()

app = FastAPI(title="CrowdGuard API", version="2.0.0", lifespan=lifespan)

_frontend_url = os.getenv("FRONTEND_URL", "")
_origins = [_frontend_url] if _frontend_url else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=bool(_frontend_url),
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router,   prefix="/api/auth",   tags=["auth"])
app.include_router(zones_router,  prefix="/api/zones",  tags=["zones"])
app.include_router(alerts_router, prefix="/api/alerts", tags=["alerts"])
app.include_router(ws_router,     prefix="/ws",         tags=["websocket"])

@app.get("/")
async def root():
    return {"status": "CrowdGuard v2.0 online"}
