from pydantic import BaseModel
from typing import Any, Dict

class WebhookEvent(BaseModel):
    event: Dict[str, str]          # Contains action and scope information
    comment: Dict[str, Any]        # Comment content and metadata
    discussion: Dict[str, Any]     # Discussion information
    repo: Dict[str, str]           # Repository details