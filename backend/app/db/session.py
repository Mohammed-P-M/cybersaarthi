import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from neo4j import GraphDatabase
from app.config import settings
from app.models.models import Base

logger = logging.getLogger("cybersaarthi.db")

# PostgreSQL setup
postgres_engine = None
SessionLocal = None

try:
    postgres_engine = create_engine(settings.POSTGRES_URI, pool_pre_ping=True)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=postgres_engine)
except Exception as e:
    logger.warning(f"Could not connect to PostgreSQL: {e}. SQLite memory fallback available.")
    postgres_engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=postgres_engine)

def init_db():
    Base.metadata.create_all(bind=postgres_engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Neo4j setup
class Neo4jConnector:
    def __init__(self):
        self.driver = None

    def connect(self):
        try:
            self.driver = GraphDatabase.driver(
                settings.NEO4J_URI, 
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
            )
            logger.info("Connected to Neo4j database successfully.")
        except Exception as e:
            logger.warning(f"Could not connect to Neo4j: {e}. Utilizing fallback graph engine.")
            self.driver = None

    def close(self):
        if self.driver:
            self.driver.close()

neo4j_conn = Neo4jConnector()
