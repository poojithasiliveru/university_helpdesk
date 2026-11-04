
import os
from pathlib import Path
from dotenv import load_dotenv

# Project settings
SEED = 20261022
NUM_REQUESTERS = 500
NUM_TICKETS = 5000
NUM_ARTICLES = 200
NUM_MESSAGES = 20000
NUM_POLICIES = 40

OUTPUT_FOLDER = "dataset"

# Project root directory
BASE_DIR = Path(__file__).resolve().parents[1]

# Load database credentials
load_dotenv(BASE_DIR / "backend" / ".env")

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME")
}
