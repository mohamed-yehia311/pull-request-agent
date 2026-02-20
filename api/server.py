from fastmcp import FastMCP
from huggingface_hub import HfApi
from ..config import settings
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Any
from .routes import router

app = FastAPI(title="HF Tagging Bot")
app.include_router(router)

tag_operations_store: List[Dict[str, Any]] = []
hf_api = HfApi(token=settings.HF_TOKEN)
mcp = FastMCP("hf-tagging-bot")

app = FastAPI(title="HF Tagging Bot")
app.add_middleware(CORSMiddleware, allow_origins=["*"])
