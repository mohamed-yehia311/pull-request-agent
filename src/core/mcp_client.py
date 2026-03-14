from typing import Dict, Any, List, Optional
import re

from huggingface_hub.inference._mcp.agent import Agent

from ..config import settings
from ..constants import RECOGNIZED_TAGS
from pathlib import Path
import sys

tagging_agent: Optional[Agent] = None


async def get_agent() -> Optional[Agent]:
    """Create and return a new MCP agent instance."""
    if settings.HF_TOKEN:
        if not settings.HF_MODEL:
            print("❌ HF_MODEL is not configured; cannot create agent")
            return None
        try:
            # Get the absolute path to the project root
            project_root = str(Path(__file__).parent.parent.parent.absolute())
            
            agent = Agent(
                model=settings.HF_MODEL,
                provider=settings.HF_PROVIDER,
                api_key=settings.HF_TOKEN,
                servers=[
                    {
                        "type": "stdio",
                        "command": sys.executable,
                        "args": ["run_mcp.py"],
                        "cwd": project_root,
                        "env": {"HF_TOKEN": settings.HF_TOKEN, "PYTHONPATH": project_root},
                    }
                ],
            )
            return agent
        except Exception as exc:
            print(f"❌ failed to create agent: {exc}")
    return None


from ..api.store import tag_operations_store
import datetime

async def process_webhook_comment(webhook_data: Dict[str, Any]) -> List[str]:
    """Evaluate a discussion comment and return a list of status messages.

    The function extracts any recognizable tags from the comment body and
    the discussion title, then asks the MCP agent to ensure each tag exists
    (creating a PR via `add_new_tag` if necessary).
    """
    comment_content = webhook_data.get("comment", {}).get("content", "")
    discussion_title = webhook_data.get("discussion", {}).get("title", "")
    repo_name = webhook_data.get("repo", {}).get("name", "")

    # parse tags from both comment and title
    comment_tags = extract_tags_from_text(comment_content)
    title_tags = extract_tags_from_text(discussion_title)
    all_tags = list(set(comment_tags + title_tags))

    print(f"🔍 extracted tags: {all_tags}")

    if not all_tags:
        return ["No recognizable tags found in the discussion."]

    agent = await get_agent()
    if not agent:
        return ["Error: Agent not configured (missing HF_TOKEN)"]

    # ... agent generation ...
    results: List[str] = []
    
    async with agent:
        # Load tools when agent context is ready
        await agent.load_tools()

        for tag in all_tags:
            prompt = f"""
            For the repository '{repo_name}', check if the tag '{tag}' already exists.
            If it doesn't exist, add it via a pull request.
    
            Repository: {repo_name}
            Tag to check/add: {tag}
            """
            
            operation_log = {
                "timestamp": datetime.datetime.now().isoformat(),
                "repo": repo_name,
                "tag": tag,
                "status": "pending",
                "message": ""
            }
            
            try:
                print(f"🤖 asking agent about {tag} in {repo_name}")
                
                response_text = ""
                async for chunk in agent.run(prompt):
                    if hasattr(chunk, "choices") and chunk.choices:
                        delta = chunk.choices[0].delta
                        if hasattr(delta, "content") and delta.content:
                            response_text += delta.content
                    elif hasattr(chunk, "content") and chunk.content:
                        response_text += chunk.content
                    elif isinstance(chunk, dict) and "choices" in chunk:
                        content = chunk["choices"][0].get("delta", {}).get("content")
                        if content:
                            response_text += content

                print(f"🤖 agent response: {response_text}")

                if "success" in response_text.lower():
                    msg = f"✅ Tag '{tag}' processed successfully"
                    results.append(msg)
                    operation_log["status"] = "success"
                    operation_log["message"] = msg
                else:
                    msg = f"⚠️ Issue with tag '{tag}': {response_text}"
                    results.append(msg)
                    operation_log["status"] = "issue"
                    operation_log["message"] = msg
            except Exception as exc:
                error_msg = f"❌ error processing '{tag}': {exc}"
                print(error_msg)
                results.append(error_msg)
                operation_log["status"] = "error"
                operation_log["message"] = error_msg
                
            # append log history to store
            tag_operations_store.append(operation_log)

    return results


# ---------------------------------------------------------------------------
# tag extraction helper
# ---------------------------------------------------------------------------

def extract_tags_from_text(text: str) -> List[str]:
    """Return a list of valid tags found in the supplied text.

    Recognizes three forms:
    * explicit ``tags: a, b`` syntax
    * ``#hashtag`` tokens
    * any of the known tags listed in ``RECOGNIZED_TAGS``
    """
    text_lower = text.lower()
    explicit_tags: List[str] = []

    # pattern "tag:" or "tags:" followed by comma‑separated values
    tag_pattern = r"tags?:\s*([a-zA-Z0-9-_,\s]+)"
    for match in re.findall(tag_pattern, text_lower):
        explicit_tags.extend([t.strip() for t in match.split(",") if t.strip()])

    # hashtags
    hashtag_pattern = r"#([a-zA-Z0-9-_]+)"
    explicit_tags.extend(re.findall(hashtag_pattern, text_lower))

    # any recognized tag mentioned in the free text
    mentioned = [t for t in RECOGNIZED_TAGS if t in text_lower]

    candidates = set(explicit_tags + mentioned)
    # filter: keep recognized tags or tags explicitly declared
    return [t for t in candidates if t in RECOGNIZED_TAGS or t in explicit_tags]
