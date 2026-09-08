import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "CyberSaarthi Intelligence Platform"
    API_V1_STR: str = "/api/v1"
    
    # PostgreSQL settings
    POSTGRES_URI: str = os.getenv(
        "POSTGRES_URI", 
        "postgresql://cybersaarthi:cybersaarthi_secure_pass@localhost:5432/cybersaarthi"
    )
    
    # Neo4j settings
    NEO4J_URI: str = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    NEO4J_USER: str = os.getenv("NEO4J_USER", "neo4j")
    NEO4J_PASSWORD: str = os.getenv("NEO4J_PASSWORD", "cybersaarthi_graph_pass")
    
    # AI settings
    AI_API_KEY: str = os.getenv("AI_API_KEY", "")
    
    # JWT
    JWT_SECRET: str = os.getenv("JWT_SECRET", "cybersaarthi_super_secret_jwt_key_sih_2026")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    class Config:
        case_sensitive = True

settings = Settings()
