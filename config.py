import os
from pathlib import Path

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://neo4j:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

#OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
#OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")

INPUT_PATH = Path(os.getenv("INPUT_PATH", "/app/input"))
KG_DATA_PATH = Path(os.getenv("KG_DATA_PATH", "/app/data"))
PROBE_GRAPH_FILE = INPUT_PATH / "probe_graph.json"
WORKBOOK_FILE = INPUT_PATH / "probe_a.xlsx"

## Newly added 2026-11-13: Use pydantic_settings for configuration management
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    ALLOW_ORIGINS: str = '*'
    OPENAI_API_KEY: str
    MODEL: str = 'gpt-4o-mini'
    TOKENIZER_ENCODING: str = 'o200k_base'
    EMBEDDING_MODEL: str = 'BAAI/bge-small-en-v1.5'
    EMBEDDING_DIMENSIONS: int = 1024
    REDIS_HOST: str = 'localhost'
    REDIS_PORT: int = 6379
    DOCS_DIR: str = 'data/docs'
    EXPORT_DIR: str = 'data'
    VECTOR_SEARCH_TOP_K: int = 10

    model_config = SettingsConfigDict(env_file='.env')

settings = Settings()

## close the comment block above and add the following lines to configure pydantic_settings