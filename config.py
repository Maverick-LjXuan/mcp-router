import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# OpenAI Configuration
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")

# DashScope Configuration
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY")

# DashVector Configuration
DASHVECTOR_API_KEY = os.getenv("DASHVECTOR_API_KEY")
DASHVECTOR_ENDPOINT = os.getenv("DASHVECTOR_ENDPOINT")
COLLECTION_NAME = os.getenv("COLLECTION_NAME", "mcp_services_collection")
EMBEDDING_DIMENSION = int(os.getenv("EMBEDDING_DIMENSION", "1024"))