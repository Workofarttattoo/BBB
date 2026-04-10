#!/usr/bin/env python3
"""
Mass Business Deployment API - Deploy Real Businesses
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.

Supports:
- Deploying businesses to persistent database
- Real-time status tracking
- Integration with autonomous runner
"""

import asyncio
import hashlib
import time
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from enum import Enum
import random
import json
import uuid

# Add src to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "src"))

from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
import httpx

from blank_business_builder.database import get_db, Business, User, MetricsHistory
from blank_business_builder.config import settings

class BusinessType(str, Enum):
    """Business types for mass deployment."""
    FIVE_GIG = "5_gig"  # Simple, no EIN required
    STANDARD = "standard"  # Traditional business
    ENTERPRISE = "enterprise"  # Full featured

class BusinessStatus(str, Enum):
    """Business lifecycle status."""
    PENDING = "pending"
    ACTIVE = "active"
    FOLDED = "folded"
    REVENUE_GENERATING = "revenue_generating"

class MassDeploymentRequest(BaseModel):
    """Request to deploy multiple businesses."""
    count: int = Field(..., ge=1, le=1000000, description="Number of businesses to create")
    business_type: BusinessType = BusinessType.FIVE_GIG
    owner_email: str = Field(..., description="Owner email for all businesses")
    auto_fold_inactive: bool = Field(default=True, description="Auto-fold inactive businesses")
    template_name: Optional[str] = Field(default="default", description="Business template")

class DeploymentStatus(BaseModel):
    """Status of mass deployment."""
    deployment_id: str
    total_requested: int
    total_created: int
    total_active: int
    total_folded: int
    total_revenue_generating: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str  # running, completed, failed
    error: Optional[str] = None

app = FastAPI(
    title="Mass Business Deployment API",
    description="Deploy real autonomous businesses with persistent storage",
    version="2.0.0"
)

# In-memory tracking for deployment status (jobs), but businesses go to DB
deployments: Dict[str, DeploymentStatus] = {}

def get_or_create_user(db: Session, email: str) -> User:
    """Find existing user or create a new one."""
    user = db.query(User).filter(User.email == email).first()
    if not user:
        # Create new user
        user = User(
            email=email,
            hashed_password="hashed_placeholder_password",  # In real world, send invite email
            full_name="Business Owner",
            subscription_tier="enterprise"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

async def create_business_batch(
    db: Session,
    batch_id: int,
    count: int,
    business_type: BusinessType,
    user_id: uuid.UUID,
    auto_fold: bool
) -> List[Business]:
    """
    Create a batch of businesses in the database.
    """
    created = []

    for i in range(count):
        # Generate unique business details
        biz_uuid = uuid.uuid4()
        timestamp = int(time.time()*1000)

        business = Business(
            id=biz_uuid,
            user_id=user_id,
            business_name=f"Business {batch_id}-{i}-{timestamp}",
            industry="Autonomous Service",
            business_concept=f"Type: {business_type.value}, Auto-fold: {auto_fold}",
            status="pending", # Start as pending
            created_at=datetime.utcnow(),
            description=f"Mass deployed business batch {batch_id}",
            # Initialize metrics
            total_revenue=0,
            total_customers=0,
            total_leads=0,
            conversion_rate=0
        )

        db.add(business)
        created.append(business)

        # Initialize metrics history
        initial_metrics = MetricsHistory(
            business_id=biz_uuid,
            revenue=0,
            customers=0,
            leads=0,
            conversion_rate=0
        )
        db.add(initial_metrics)

    db.commit()
    return created

async def activate_businesses_db(db: Session, business_ids: List[uuid.UUID]) -> int:
    """
    Activate businesses in database.
    """
    activated = 0
    # Process in chunks to avoid huge IN clauses
    chunk_size = 500
    for i in range(0, len(business_ids), chunk_size):
        chunk = business_ids[i:i+chunk_size]
        # Update status
        updated = db.query(Business).filter(Business.id.in_(chunk)).update(
            {Business.status: "active", Business.started_at: datetime.utcnow()},
            synchronize_session=False
        )
        activated += updated

    db.commit()
    return activated

async def process_mass_deployment(
    deployment_id: str,
    request: MassDeploymentRequest,
    actual_count: int
) -> None:
    """
    Background task to process mass deployment.
    """
    # Create a new DB session for this background task
    from blank_business_builder.database import get_db_engine, get_session
    engine = get_db_engine(settings.DATABASE_URL)
    db = get_session(engine)

    try:
        deployment = deployments[deployment_id]
        deployment.status = "running"

        print(f"🚀 Starting mass deployment: {actual_count} businesses for {request.owner_email}")

        # Get/Create User
        user = get_or_create_user(db, request.owner_email)

        batch_size = 100 # Smaller batch size for real DB writes compared to simulated
        num_batches = (actual_count + batch_size - 1) // batch_size

        all_business_ids = []

        for batch_id in range(num_batches):
            batch_count = min(batch_size, actual_count - (batch_id * batch_size))

            # Create batch
            created_businesses = await create_business_batch(
                db,
                batch_id,
                batch_count,
                request.business_type,
                user.id,
                request.auto_fold_inactive
            )

            # Collect IDs
            batch_ids = [b.id for b in created_businesses]
            all_business_ids.extend(batch_ids)

            deployment.total_created += len(batch_ids)

            # Allow some breathing room for DB
            await asyncio.sleep(0.1)

        # Activate businesses
        activated = await activate_businesses_db(db, all_business_ids)
        deployment.total_active = activated

        deployment.completed_at = datetime.now()
        deployment.status = "completed"

        print(f"✅ Deployment {deployment_id}: Created {deployment.total_created} businesses in DB")

    except Exception as e:
        deployment.status = "failed"
        deployment.error = str(e)
        print(f"❌ Deployment {deployment_id} failed: {e}")
    finally:
        db.close()

@app.post("/deploy/mass", response_model=DeploymentStatus)
async def deploy_businesses_mass(
    request: MassDeploymentRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
) -> DeploymentStatus:
    """
    Deploy businesses to persistent database.
    """

    # Generate ID
    deployment_id = f"deploy_{int(time.time()*1000)}_{random.randint(1000, 9999)}"

    deployment = DeploymentStatus(
        deployment_id=deployment_id,
        total_requested=request.count,
        total_created=0,
        total_active=0,
        total_folded=0,
        total_revenue_generating=0,
        started_at=datetime.now(),
        status="queued"
    )

    deployments[deployment_id] = deployment

    # Process in background
    background_tasks.add_task(
        process_mass_deployment,
        deployment_id,
        request,
        request.count
    )

    return deployment

@app.get("/deploy/{deployment_id}", response_model=DeploymentStatus)
async def get_deployment_status(deployment_id: str) -> DeploymentStatus:
    """Get status of a mass deployment."""
    if deployment_id not in deployments:
        raise HTTPException(status_code=404, detail="Deployment not found")
    return deployments[deployment_id]

@app.get("/businesses/stats")
async def get_business_stats(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """Get overall business statistics from DB."""
    total = db.query(Business).count()
    active = db.query(Business).filter(Business.status == "active").count()
    revenue_generating = db.query(Business).filter(Business.total_revenue > 0).count()
    total_revenue = db.query(Business).with_entities(Business.total_revenue).all()

    total_rev_sum = sum([r[0] for r in total_revenue if r[0]])

    return {
        "total_businesses": total,
        "active_businesses": active,
        "revenue_generating": revenue_generating,
        "total_revenue": float(total_rev_sum)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
