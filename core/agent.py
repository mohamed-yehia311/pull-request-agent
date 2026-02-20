from typing import Dict, Any, List, Optional
import re

from huggingface_hub.inference._mcp.agent import Agent

from ..config import settings
from ..constants import RECOGNIZED_TAGS


tagging_agent: Optional[Agent] = None


async def get_agent() -> Optional[Agent]:
    """Return a singleton MCP agent instance, creating it on first call."""
    global tagging_agent
    if tagging_agent is None and settings.HF_TOKEN:
        # note: if a token isn't provided the agent will not be created
        try:
            tagging_agent = Agent(
                model=settings.HF_MODEL,
                provider=settings.HF_PROVIDER,
                api_key=settings.HF_TOKEN,
                servers=[
                    {
                        "type": "stdio",
                        "command": "python",
                        "args": ["mcp_server.py"],
                        "cwd": ".",
                        "env": {"HF_TOKEN": settings.HF_TOKEN},
                    }
                ],
            )
            await tagging_agent.load_tools()
        except Exception as exc:
            print(f"❌ failed to create agent: {exc}")
            tagging_agent = None
    return tagging_agent


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

    results: List[str] = []
    for tag in all_tags:
        prompt = f"""
        For the repository '{repo_name}', check if the tag '{tag}' already exists.
        If it doesn't exist, add it via a pull request.

        Repository: {repo_name}
        Tag to check/add: {tag}
        """
        try:
            print(f"🤖 asking agent about {tag} in {repo_name}")
            response = await agent.run(prompt)
            if "success" in response.lower():
                results.append(f"✅ Tag '{tag}' processed successfully")
            else:
                results.append(f"⚠️ Issue with tag '{tag}': {response}")
        except Exception as exc:
            error_msg = f"❌ error processing '{tag}': {exc}"
            print(error_msg)
            results.append(error_msg)

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
