import os
from dotenv import load_dotenv

# 1. Load the .env file from the parent directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(BASE_DIR, '.env'))

class Config:
    # Server
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 5000))
    DEBUG = os.getenv("DEBUG_MODE", "False").lower() == "true"
    
    # Database
    DB_NAME = os.getenv("DB_NAME", "audit_log.db")
    
    # Security
    TIMEOUT = int(os.getenv("EXECUTION_TIMEOUT", 2))
    MAX_MEMORY_MB = int(os.getenv("MAX_MEMORY_MB", 128))
    
    # Paths
    POLICY_FILE = os.path.join(BASE_DIR, os.getenv("POLICY_FILE", "security_policy.json"))
    SANDBOX_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'sandbox.py')

# Create a singleton instance
settings = Config()