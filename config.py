from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

BASE_DIR = Path(__file__).parent

# Instagram
INSTAGRAM_USERNAME = os.getenv("INSTAGRAM_USERNAME", "")
INSTAGRAM_PASSWORD = os.getenv("INSTAGRAM_PASSWORD", "")
INSTAGRAM_SESSION_ID = os.getenv("INSTAGRAM_SESSION_ID", "")
TARGET_INSTAGRAM_PROFILE = os.getenv("TARGET_INSTAGRAM_PROFILE", "blockchainrio")

# YouTube OAuth
YOUTUBE_CLIENT_SECRETS_FILE = BASE_DIR / os.getenv("YOUTUBE_CLIENT_SECRETS_FILE", "auth/client_secrets.json")
YOUTUBE_TOKEN_FILE = BASE_DIR / os.getenv("YOUTUBE_TOKEN_FILE", "auth/token.json")
YOUTUBE_SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]

# Pipeline
DOWNLOAD_DIR = BASE_DIR / os.getenv("DOWNLOAD_DIR", "downloads")
METADATA_FILE = BASE_DIR / os.getenv("METADATA_FILE", "metadata/videos.json")
LOG_FILE = BASE_DIR / os.getenv("LOG_FILE", "logs/pipeline.log")

UPLOAD_HOUR = int(os.getenv("UPLOAD_HOUR", 13))
UPLOAD_MINUTE = int(os.getenv("UPLOAD_MINUTE", 0))
MAX_COLLECT_PER_RUN = int(os.getenv("MAX_COLLECT_PER_RUN", 30))
MAX_UPLOADS_PER_RUN = int(os.getenv("MAX_UPLOADS_PER_RUN", 6))

REPORT_FILE = BASE_DIR / os.getenv("REPORT_FILE", "metadata/report.csv")

# Garante que os diretórios existam
DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
METADATA_FILE.parent.mkdir(parents=True, exist_ok=True)
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
YOUTUBE_TOKEN_FILE.parent.mkdir(parents=True, exist_ok=True)
