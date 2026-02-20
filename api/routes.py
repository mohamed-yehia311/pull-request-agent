from ..config import settings
from fastapi import BackgroundTasks, Request, APIRouter
from tools import process_webhook_comment, get_agent
import datetime
from ..constants import tag_operations_store
router = APIRouter()

@router.get("/")
async def root():
    """Root endpoint with basic information"""
    return {
        "name": "HF Tagging Bot",
        "status": "running",
        "description": "Webhook listener for automatic model tagging",
        "endpoints": {
            "webhook": "/webhook",
            "health": "/health",
            "operations": "/operations"
        }
    }

@router.get("/health")
async def health_check():
    """Health check endpoint for monitoring"""
    agent = await get_agent()
    
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "components": {
            "webhook_secret": "configured" if settings.WEBHOOK_SECRET else "missing",
            "hf_token": "configured" if settings.HF_TOKEN else "missing",
            "mcp_agent": "ready" if agent else "not_ready"
        }
    }

@router.get("/operations")
async def get_operations():
    """Get recent tag operations for monitoring"""
    # Return last 50 operations
    recent_ops = tag_operations_store[-50:] if tag_operations_store else []
    return {
        "total_operations": len(tag_operations_store),
        "recent_operations": recent_ops
    }

@router.post("/webhook")
async def webhook_handler(request: Request, background_tasks: BackgroundTasks):
    """
    Handle incoming webhooks from Hugging Face Hub
    Following the pattern from: https://raw.githubusercontent.com/huggingface/hub-docs/refs/heads/main/docs/hub/webhooks-guide-discussion-bot.md
    """
    print("🔔 Webhook received!")
    
    # Step 1: Validate webhook secret (security)
    webhook_secret = request.headers.get("X-Webhook-Secret")
    if webhook_secret != settings.WEBHOOK_SECRET:
        print("❌ Invalid webhook secret")
        return {"error": "incorrect secret"},
        # Step 2: Parse webhook data
    try:
        webhook_data = await request.json()
        print(f"📥 Webhook data: {json.dumps(webhook_data, indent=2)}")
    except Exception as e:
        print(f"❌ Error parsing webhook data: {str(e)}")
        return {"error": "invalid JSON"}, 400
    
    # Step 3: Validate event structure
    event = webhook_data.get("event", {})
    if not event:
        print("❌ No event data in webhook")
        return {"error": "missing event data"}, 400
    # Step 4: Check if this is a discussion comment creation
    # Following the webhook guide pattern:
    if (
        event.get("action") == "create" and 
        event.get("scope") == "discussion.comment"
    ):
        print("✅ Valid discussion comment creation event")
        
        # Process in background to return quickly to Hub
        background_tasks.add_task(process_webhook_comment, webhook_data)
        
        return {
            "status": "accepted",
            "message": "Comment processing started",
            "timestamp": datetime.now().isoformat()
        }
    else:
        print(f"ℹ️ Ignoring event: action={event.get('action')}, scope={event.get('scope')}")
        return {
            "status": "ignored",
            "reason": "Not a discussion comment creation"
        }