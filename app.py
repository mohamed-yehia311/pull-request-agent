import os
import json
from fastmcp import FastMCP
from huggingface_hub import HfApi, model_info, ModelCard, ModelCardData
from huggingface_hub.utils import HfHubHTTPError
from .config import settings


hf_api = HfApi(token=settings.HF_TOKEN)
mcp = FastMCP("hf-tagging-bot")

