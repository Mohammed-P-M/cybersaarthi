import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.db.session import init_db, neo4j_conn
from app.api.router import router as api_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("cybersaarthi")

app = FastAPI(title=settings.PROJECT_NAME, openapi_url=f"{settings.API_V1_STR}/openapi.json")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.on_event("startup")
def startup_event():
    logger.info("Initializing PostgreSQL schema...")
    init_db()
    logger.info("Connecting to Neo4j Graph Database...")
    neo4j_conn.connect()

@app.on_event("shutdown")
def shutdown_event():
    neo4j_conn.close()

app.include_router(api_router, prefix=settings.API_V1_STR)

@app.get("/")
def root():
    return {"app": settings.PROJECT_NAME, "status": "online", "docs": "/docs"}
