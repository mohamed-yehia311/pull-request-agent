from typing import List, Dict, Any

# Shared in-memory list for storing tag operations history
# moved here to avoid circular imports between server and routes

tag_operations_store: List[Dict[str, Any]] = []
