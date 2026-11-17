import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    DATABASE = os.path.join("instance", "cnis.db")
    MAX_CONTENT_LENGTH = 10 * 1024 * 1024
