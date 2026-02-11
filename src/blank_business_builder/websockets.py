"""
Better Business Builder - WebSocket Real-Time Dashboard
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""
from fastapi import WebSocket, WebSocketDisconnect, Depends
from typing import Dict, Set
from sqlalchemy import func, case
from sqlalchemy.orm import Session
from datetime import datetime
import asyncio
import json

from .database import get_db, Business, AgentTask, MetricsHistory
from .auth import AuthService


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""

    def __init__(self):
        # business_id -> Set of WebSocket connections
        self.active_connections: Dict[str, Set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, business_id: str):
        """Connect a client to a business channel."""
        await websocket.accept()

        if business_id not in self.active_connections:
            self.active_connections[business_id] = set()

        self.active_connections[business_id].add(websocket)

    def disconnect(self, websocket: WebSocket, business_id: str):
        """Disconnect a client from a business channel."""
        if business_id in self.active_connections:
            self.active_connections[business_id].discard(websocket)

            # Clean up empty channels
            if not self.active_connections[business_id]:
                del self.active_connections[business_id]

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific client."""
        await websocket.send_json(message)

    async def broadcast(self, message: dict, business_id: str):
        """Broadcast a message to all clients watching a business."""
        if business_id in self.active_connections:
            disconnected_clients = set()

            for connection in self.active_connections[business_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    # Mark for removal if send fails
                    disconnected_clients.add(connection)

            # Remove disconnected clients
            for client in disconnected_clients:
                self.active_connections[business_id].discard(client)


# Global connection manager
manager = ConnectionManager()


async def get_business_metrics(business_id: str, db: Session) -> dict:
    """Get real-time business metrics."""
    business = db.query(Business).filter(Business.id == business_id).first()

    if not business:
        return {"error": "Business not found"}

    # Get task statistics
    task_stats = db.query(
        func.count(AgentTask.id).label('total'),
        func.sum(case((AgentTask.status == 'completed', 1), else_=0)).label('completed'),
        func.sum(case((AgentTask.status == 'pending', 1), else_=0)).label('pending'),
        func.sum(case((AgentTask.status == 'failed', 1), else_=0)).label('failed')
    ).filter(AgentTask.business_id == business_id).first()

    total_tasks = task_stats.total or 0
    completed_tasks = task_stats.completed or 0
    pending_tasks = task_stats.pending or 0
    failed_tasks = task_stats.failed or 0

    # Get recent tasks
    recent_tasks = db.query(AgentTask).filter(
        AgentTask.business_id == business_id
    ).order_by(AgentTask.created_at.desc()).limit(10).all()

    # Get latest metrics
    latest_metric = db.query(MetricsHistory).filter(
        MetricsHistory.business_id == business_id
    ).order_by(MetricsHistory.timestamp.desc()).first()

    business_name = business.business_name or (business.business_concept or "Business")

    return {
        "business_id": str(business.id),
        "business_name": business_name[:50],
        "status": business.status,
        "metrics": {
            "revenue": float(business.total_revenue) if business.total_revenue else 0.0,
            "customers": business.total_customers or 0,
            "leads": business.total_leads or 0,
            "conversion_rate": float(business.conversion_rate) if business.conversion_rate else 0.0
        },
        "tasks": {
            "total": total_tasks,
            "completed": completed_tasks,
            "pending": pending_tasks,
            "failed": failed_tasks,
            "success_rate": (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0.0
        },
        "recent_tasks": [
            {
                "id": str(task.id),
                "agent_role": task.agent_role,
                "task_type": task.task_type,
                "status": task.status,
                "confidence": float(task.confidence) if task.confidence else None,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None
            }
            for task in recent_tasks
        ],
        "timestamp": datetime.utcnow().isoformat()
    }


async def get_agent_activity(business_id: str, db: Session) -> dict:
    """Get real-time agent activity."""
    # Get active agents (tasks in progress)
    active_tasks = db.query(AgentTask).filter(
        AgentTask.business_id == business_id,
        AgentTask.status == "in_progress"
    ).all()

    agents = {}
    for task in active_tasks:
        if task.agent_role not in agents:
            agents[task.agent_role] = {
                "role": task.agent_role,
                "active_tasks": 0,
                "current_task": None
            }

        agents[task.agent_role]["active_tasks"] += 1
        if not agents[task.agent_role]["current_task"]:
            agents[task.agent_role]["current_task"] = {
                "task_type": task.task_type,
                "description": task.description,
                "started_at": task.started_at.isoformat() if task.started_at else None
            }

    return {
        "business_id": str(business_id),
        "agents": list(agents.values()),
        "timestamp": datetime.utcnow().isoformat()
    }


async def websocket_update_loop(business_id: str, websocket: WebSocket, db: Session):
    """Send periodic updates to client."""
    try:
        while True:
            # Get metrics
            metrics = await get_business_metrics(business_id, db)

            # Get agent activity
            activity = await get_agent_activity(business_id, db)

            # Send update
            await manager.send_personal_message({
                "type": "update",
                "data": {
                    "metrics": metrics,
                    "activity": activity
                }
            }, websocket)

            # Wait 5 seconds before next update
            await asyncio.sleep(5)

    except WebSocketDisconnect:
        manager.disconnect(websocket, business_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket, business_id)


async def broadcast_task_update(business_id: str, task: AgentTask):
    """Broadcast task update to all connected clients."""
    message = {
        "type": "task_update",
        "data": {
            "business_id": str(business_id),
            "task": {
                "id": str(task.id),
                "agent_role": task.agent_role,
                "task_type": task.task_type,
                "status": task.status,
                "confidence": float(task.confidence) if task.confidence else None,
                "created_at": task.created_at.isoformat() if task.created_at else None,
                "completed_at": task.completed_at.isoformat() if task.completed_at else None
            },
            "timestamp": datetime.utcnow().isoformat()
        }
    }

    await manager.broadcast(message, str(business_id))


async def broadcast_metrics_update(business_id: str, metrics: dict):
    """Broadcast metrics update to all connected clients."""
    message = {
        "type": "metrics_update",
        "data": {
            "business_id": str(business_id),
            "metrics": metrics,
            "timestamp": datetime.utcnow().isoformat()
        }
    }

    await manager.broadcast(message, str(business_id))


async def websocket_endpoint(
    websocket: WebSocket,
    business_id: str,
    token: str,
    db: Session = Depends(get_db)
):
    """WebSocket endpoint for real-time dashboard updates."""
    # Verify authentication token
    try:
        payload = AuthService.decode_token(token)
        user_id = payload.get("sub")
        if not user_id:
            await websocket.close(code=1008, reason="Invalid authentication")
            return
    except Exception:
        await websocket.close(code=1008, reason="Authentication failed")
        return

    # Verify business ownership
    business = db.query(Business).filter(
        Business.id == business_id,
        Business.user_id == user_id
    ).first()

    if not business:
        await websocket.close(code=1008, reason="Business not found or unauthorized")
        return

    # Connect and start update loop
    await manager.connect(websocket, business_id)

    try:
        # Send initial data
        initial_data = {
            "type": "connected",
            "data": {
                "business_id": str(business_id),
                "message": "Connected to real-time dashboard"
            }
        }
        await manager.send_personal_message(initial_data, websocket)

        # Start update loop
        await websocket_update_loop(business_id, websocket, db)

    except WebSocketDisconnect:
        manager.disconnect(websocket, business_id)
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket, business_id)
