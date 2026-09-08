import logging
from neo4j import GraphDatabase, Driver
from app.core.config import settings

logger = logging.getLogger(__name__)

_driver: Driver | None = None

def get_neo4j_driver() -> Driver | None:
    global _driver
    if _driver is not None:
        return _driver
    try:
        driver = GraphDatabase.driver(
            settings.NEO4J_URI, 
            auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD)
        )
        driver.verify_connectivity()
        _driver = driver
        logger.info("Connected to Neo4j database successfully.")
        return _driver
    except Exception as e:
        logger.warning(f"Neo4j connection unavailable ({e}). Fallback to SQLite/In-Memory graph engine.")
        return None

def close_neo4j_driver():
    global _driver
    if _driver:
        _driver.close()
        _driver = None
