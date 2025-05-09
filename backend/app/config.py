import os

# Auth
API_SECRET_KEY = os.getenv("API_SECRET_KEY", "kk")


# PostgreSQL Configurations
POSTGRES_USER = os.environ.get("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "postgres")
POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.environ.get("POSTGRES_PORT", "5432")
POSTGRES_DB = os.environ.get("POSTGRES_DB", "postgres")
DB_POOL_SIZE = int(os.environ.get("DB_POOL_SIZE", 20))

# Backend Configuration
BACKEND_ROOT_PATH = os.environ.get("BACKEND_ROOT_PATH", "./")
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")

# PGVector Configuration
PGVECTOR_VECTOR_SIZE = int(os.environ.get("PGVECTOR_VECTOR_SIZE", 1024))
PGVECTOR_M = os.environ.get("PGVECTOR_M", "16")
PGVECTOR_EF_CONSTRUCTION = os.environ.get("PGVECTOR_EF_CONSTRUCTION", "64")
PGVECTOR_DISTANCE = os.environ.get("PGVECTOR_DISTANCE", "vector_cosine_ops")

# Embedding Configurations
COHERE_API_KEY = os.environ.get("COHERE_API_KEY")
# Remove EMBEDDING_MODEL_NAME as we are using Cohere directly

# Airtable Configurations
AIRTABLE_CONFIGS = {
    "default": {
        "AIRTABLE_BASE_ID": os.environ.get("AIRTABLE_BASE_ID", "appwFDBSURFLcCe1H"),
        "TABLE_NAME": os.environ.get("AIRTABLE_TABLE_NAME", "tble3Kf2oWaRZVLJ7"),
    }
}
AIRTABLE_API_KEY = os.environ.get("AIRTABLE_API_KEY")

# OpenAI Configuration
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY_SA")

# Google API Configurations
SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/devstorage.read_write",
    "https://www.googleapis.com/auth/devstorage.full_control",
]
SERVICE_ACCOUNT_FILE_PATH = os.environ.get(
    "SERVICE_ACCOUNT_FILE_PATH",
    "/Users/markbotterill/secrets/survey-accelerator-c3ff88c19ae3.json",
)

# Other Configurations
MAIN_DOWNLOAD_DIR = "downloaded_gdrives_sa"
