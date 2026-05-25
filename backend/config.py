from dotenv import load_dotenv
import os

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")
LANGSMITH_PROJECT = os.getenv("LANGSMITH_PROJECT", "finsight")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

# validate required variables are set
required = ["OPENAI_API_KEY", "DATABASE_URL"]
for var in required:
    if not os.getenv(var):
        raise ValueError(f"Missing required environment variable: {var}")