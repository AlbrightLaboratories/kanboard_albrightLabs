"""
Maestro API Server

FastAPI application for AI agent communication with Kanboard.
"""
from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Query
from pydantic import BaseModel

from .agent_registry import AgentRegistry
from .story_claims import StoryClaims


# Request/Response models
class AgentRegisterRequest(BaseModel):
    agent_type: str
    capabilities: List[str] = []
    name: Optional[str] = None


class AgentRegisterResponse(BaseModel):
    agent_id: str


class ClaimRequest(BaseModel):
    agent_id: str


class ClaimResponse(BaseModel):
    claimed: bool


class ProgressRequest(BaseModel):
    agent_id: str
    progress: int
    message: str = ""


# Global state (in production, use dependency injection)
_maestro: Optional["MaestroAPI"] = None


def get_maestro() -> "MaestroAPI":
    """Get or create MaestroAPI instance."""
    global _maestro
    if _maestro is None:
        _maestro = MaestroAPI()
    return _maestro


def reset_maestro() -> None:
    """Reset MaestroAPI instance (for testing)."""
    global _maestro
    _maestro = None


class MaestroAPI:
    """Central API controller."""

    def __init__(self):
        """Initialize Maestro API."""
        self.agents = AgentRegistry()
        self.stories = StoryClaims()
        self._websockets: Dict[str, WebSocket] = {}
        self._pending_messages: List[Dict[str, Any]] = []

    def add_story(self, story_id: int, data: Dict[str, Any]) -> None:
        """Add a story."""
        self.stories.add_story(story_id, data)

    def get_story(self, story_id: int) -> Optional[Dict[str, Any]]:
        """Get a story."""
        return self.stories.get_story(story_id)

    def clear_stories(self) -> None:
        """Clear all stories."""
        self.stories.clear_stories()

    def set_agent_last_seen(self, agent_id: str, timestamp: float) -> None:
        """Set agent last_seen (for testing)."""
        self.agents.set_last_seen(agent_id, timestamp)

    def check_stale_agents(self, timeout_seconds: int = 300) -> List[str]:
        """Check and mark stale agents, release their stories."""
        stale = self.agents.check_stale(timeout_seconds)
        for agent_id in stale:
            self.stories.release_agent_stories(agent_id)
        return stale

    def set_request_count(
        self,
        agent_id: str,
        count: int,
        window_start: Optional[float] = None
    ) -> None:
        """Set request count (for testing)."""
        self.agents.set_request_count(agent_id, count, window_start)

    def broadcast(self, message: Dict[str, Any]) -> None:
        """Broadcast message to all connected clients."""
        self._pending_messages.append(message)

    def send_to_agent(self, agent_id: str, message: Dict[str, Any]) -> None:
        """Send message to specific agent."""
        self._pending_messages.append({
            "_target": agent_id,
            **message
        })

    def pop_message(self) -> Optional[Dict[str, Any]]:
        """Pop next pending message."""
        if self._pending_messages:
            return self._pending_messages.pop(0)
        return None


# Create FastAPI app
app = FastAPI(title="Maestro API", version="1.0.0")


@app.post("/agents/register", response_model=AgentRegisterResponse)
def register_agent(request: AgentRegisterRequest):
    """Register a new AI agent."""
    maestro = get_maestro()
    agent_id = maestro.agents.register(
        agent_type=request.agent_type,
        capabilities=request.capabilities,
        name=request.name
    )
    return AgentRegisterResponse(agent_id=agent_id)


@app.get("/agents/{agent_id}")
def get_agent(agent_id: str):
    """Get agent details."""
    maestro = get_maestro()
    agent = maestro.agents.get(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent


@app.get("/agents/{agent_id}/heartbeat")
def agent_heartbeat(agent_id: str):
    """Update agent heartbeat."""
    maestro = get_maestro()

    # Check rate limit
    if maestro.agents.is_rate_limited(agent_id):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    maestro.agents.increment_request_count(agent_id)

    result = maestro.agents.heartbeat(agent_id)
    if not result:
        raise HTTPException(status_code=404, detail="Agent not found")
    return result


@app.get("/stories/available")
def get_available_stories():
    """Get available (unblocked, unclaimed) stories."""
    maestro = get_maestro()
    return maestro.stories.get_available()


@app.post("/stories/{story_id}/claim", response_model=ClaimResponse)
def claim_story(story_id: int, request: ClaimRequest):
    """Claim a story for an agent."""
    maestro = get_maestro()

    story = maestro.stories.get_story(story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    if story.get("blocked", False):
        raise HTTPException(status_code=400, detail="Story is blocked")

    if story.get("claimed", False):
        raise HTTPException(status_code=409, detail="Story already claimed")

    success = maestro.stories.claim(story_id, request.agent_id)
    if success:
        maestro.agents.set_status(request.agent_id, "working")
        maestro.agents.set_current_story(request.agent_id, story_id)

    return ClaimResponse(claimed=success)


@app.get("/stories/{story_id}/prompt")
def get_story_prompt(story_id: int):
    """Get structured prompt for a story."""
    maestro = get_maestro()

    story = maestro.stories.get_story(story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    return {
        "title": story.get("title", ""),
        "description": story.get("description", ""),
        "acceptance_criteria": story.get("acceptance_criteria", []),
        "repo_url": story.get("repo_url"),
        "branch": story.get("branch"),
        "file_paths": story.get("file_paths", []),
        "depends_on": story.get("depends_on", [])
    }


@app.post("/stories/{story_id}/progress")
def update_progress(story_id: int, request: ProgressRequest):
    """Update story progress."""
    maestro = get_maestro()

    story = maestro.stories.get_story(story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")

    if story.get("assigned_agent") != request.agent_id:
        raise HTTPException(status_code=403, detail="Not assigned to this agent")

    maestro.stories.update_progress(story_id, request.progress, request.message)

    # Broadcast progress update
    maestro.broadcast({
        "type": "progress_update",
        "story_id": story_id,
        "progress": request.progress,
        "message": request.message
    })

    return {"updated": True}


@app.websocket("/stream")
async def websocket_stream(
    websocket: WebSocket,
    agent_id: Optional[str] = Query(None)
):
    """WebSocket endpoint for real-time updates."""
    maestro = get_maestro()
    await websocket.accept()

    if agent_id:
        maestro._websockets[agent_id] = websocket

    try:
        while True:
            # Check for messages to send
            message = maestro.pop_message()
            if message:
                target = message.pop("_target", None)
                if target is None or target == agent_id:
                    await websocket.send_json(message)
            else:
                await asyncio.sleep(0.01)

            # Also check for incoming messages
            try:
                data = await asyncio.wait_for(
                    websocket.receive_json(),
                    timeout=0.01
                )
                # Handle incoming messages if needed
            except asyncio.TimeoutError:
                pass

    except WebSocketDisconnect:
        if agent_id and agent_id in maestro._websockets:
            del maestro._websockets[agent_id]
