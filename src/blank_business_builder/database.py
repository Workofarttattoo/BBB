"""
Better Business Builder - Database Models
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""

from sqlalchemy import create_engine, Column, String, Integer, Numeric, DateTime, ForeignKey, Text, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.types import TypeDecorator
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
import uuid
from datetime import datetime
from typing import Optional
import os

Base = declarative_base()

class UUIDType(TypeDecorator):
    """UUID column that stores as TEXT when using SQLite."""

    impl = UUID(as_uuid=True)
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "sqlite":
            return dialect.type_descriptor(String(36))
        return dialect.type_descriptor(UUIDType())

    def process_bind_param(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "sqlite":
            return str(value)
        return value

    def process_result_value(self, value, dialect):
        if value is None:
            return None
        if dialect.name == "sqlite" and value:
            return uuid.UUID(value)
        return value

class JSONType(TypeDecorator):
    """Unified JSON column type compatible with SQLite and Postgres."""

    impl = JSONB
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "sqlite":
            return dialect.type_descriptor(JSON())
        return dialect.type_descriptor(JSONB())


class INETType(TypeDecorator):
    """Network address type that gracefully degrades on SQLite."""

    impl = INET
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "sqlite":
            return dialect.type_descriptor(String(45))
        return dialect.type_descriptor(INET())


class User(Base):
    """User account model"""
    __tablename__ = 'users'

    id = Column(UUIDType(), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    subscription_tier = Column(String(50), default='free')  # free, starter, pro, enterprise
    stripe_customer_id = Column(String(255), unique=True, index=True, nullable=True)
    is_active = Column(Boolean, default=True)
    status = Column(String(50), default='active')  # legacy field for backward compatibility
    license_status = Column(String(50), default='trial')  # trial, revenue_share, licensed, suspended
    license_terms_version = Column(String(20), default='v1')
    license_agreed_at = Column(DateTime, nullable=True)
    trial_expires_at = Column(DateTime, nullable=True)
    revenue_share_percentage = Column(Numeric(5, 2), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    email_verified = Column(Boolean, default=False)
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    businesses = relationship("Business", back_populates="user", cascade="all, delete-orphan")
    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")
    api_integrations = relationship("APIIntegration", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, tier={self.subscription_tier})>"


class Business(Base):
    """Business model - represents an autonomous business"""
    __tablename__ = 'businesses'

    id = Column(UUIDType(), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUIDType(), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    business_name = Column(String(255), nullable=False)
    business_concept = Column(String(500), nullable=True)  # Legacy field for backward compatibility
    industry = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    website_url = Column(String(255), nullable=True)
    status = Column(String(50), default='active')  # active, paused, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)  # Legacy field retained for migrations
    paused_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # Metrics
    total_revenue = Column(Numeric(12, 2), default=0)
    total_customers = Column(Integer, default=0)
    total_leads = Column(Integer, default=0)
    conversion_rate = Column(Numeric(5, 2), default=0)

    # Relationships
    user = relationship("User", back_populates="businesses")
    tasks = relationship("AgentTask", back_populates="business", cascade="all, delete-orphan")
    metrics = relationship("MetricsHistory", back_populates="business", cascade="all, delete-orphan")
    business_plans = relationship("BusinessPlan", back_populates="business", cascade="all, delete-orphan")
    marketing_campaigns = relationship("MarketingCampaign", back_populates="business", cascade="all, delete-orphan")

    def __repr__(self):
        name = self.business_name or (self.business_concept[:50] if self.business_concept else "Unnamed")
        return f"<Business(id={self.id}, name={name}, status={self.status})>"


class BusinessPlan(Base):
    """Business plan generated for a business."""
    __tablename__ = 'business_plans'

    id = Column(UUIDType(), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUIDType(), ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False, index=True)
    plan_name = Column(String(255), nullable=False)
    executive_summary = Column(Text, nullable=True)
    market_analysis = Column(Text, nullable=True)
    financial_projections = Column(JSONType(), nullable=True)
    marketing_strategy = Column(Text, nullable=True)
    operations_plan = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    business = relationship("Business", back_populates="business_plans")

    def __repr__(self):
        return f"<BusinessPlan(id={self.id}, business_id={self.business_id}, name={self.plan_name})>"


class AgentTask(Base):
    """Agent task model - represents work done by autonomous agents"""
    __tablename__ = 'agent_tasks'

    id = Column(UUIDType(), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUIDType(), ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False, index=True)
    agent_role = Column(String(50), nullable=False)  # researcher, marketer, sales, fulfillment, support, finance, orchestrator
    task_type = Column(String(100), nullable=False)
    description = Column(Text)
    status = Column(String(50), default='pending', index=True)  # pending, in_progress, completed, failed
    priority = Column(Integer, default=5)  # 1-10, higher = more urgent
    confidence = Column(Numeric(3, 2))  # 0.00-1.00
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    result = Column(JSONType(), nullable=True)
    error = Column(Text, nullable=True)

    # Relationships
    business = relationship("Business", back_populates="tasks")

    def __repr__(self):
        return f"<AgentTask(id={self.id}, role={self.agent_role}, type={self.task_type}, status={self.status})>"


class MetricsHistory(Base):
    """Time-series metrics for businesses"""
    __tablename__ = 'metrics_history'

    id = Column(UUIDType(), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUIDType(), ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    # Business metrics
    revenue = Column(Numeric(12, 2), default=0)
    customers = Column(Integer, default=0)
    leads = Column(Integer, default=0)
    conversion_rate = Column(Numeric(5, 2), default=0)
    tasks_completed = Column(Integer, default=0)
    tasks_pending = Column(Integer, default=0)
    tasks_failed = Column(Integer, default=0)

    # Relationships
    business = relationship("Business", back_populates="metrics")

    def __repr__(self):
        return f"<MetricsHistory(business_id={self.business_id}, timestamp={self.timestamp}, revenue={self.revenue})>"


class APIIntegration(Base):
    """API integration credentials (encrypted)"""
    __tablename__ = 'api_integrations'

    id = Column(UUIDType(), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUIDType(), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    service = Column(String(100), nullable=False)  # stripe, sendgrid, google_ads, hubspot, openai, buffer
    api_key_encrypted = Column(Text, nullable=False)
    status = Column(String(50), default='inactive')  # active, inactive, error
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used = Column(DateTime, nullable=True)
    config = Column(JSONType(), nullable=True)  # Additional service-specific config

    # Relationships
    user = relationship("User", back_populates="api_integrations")

    def __repr__(self):
        return f"<APIIntegration(id={self.id}, service={self.service}, status={self.status})>"


class AuditLog(Base):
    """Audit log for compliance and security"""
    __tablename__ = 'audit_log'

    id = Column(UUIDType(), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUIDType(), ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    business_id = Column(UUIDType(), ForeignKey('businesses.id', ondelete='SET NULL'), nullable=True)
    action = Column(String(255), nullable=False)  # login, logout, create_business, delete_account, etc.
    details = Column(JSONType(), nullable=True)
    ip_address = Column(INETType(), nullable=True)
    user_agent = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action={self.action}, timestamp={self.timestamp})>"


class Subscription(Base):
    """Stripe subscription model"""
    __tablename__ = 'subscriptions'

    id = Column(UUIDType(), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUIDType(), ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    stripe_customer_id = Column(String(255), unique=True, index=True)
    stripe_subscription_id = Column(String(255), unique=True, index=True)
    plan_name = Column(String(50), nullable=False)  # starter, pro, enterprise
    status = Column(String(50), default='active')  # active, canceled, past_due, incomplete
    current_period_start = Column(DateTime, nullable=True)
    current_period_end = Column(DateTime, nullable=True)
    cancel_at_period_end = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="subscriptions")

    def __repr__(self):
        return f"<Subscription(id={self.id}, user_id={self.user_id}, plan={self.plan_name}, status={self.status})>"


class MarketingCampaign(Base):
    """Marketing campaign records"""
    __tablename__ = 'marketing_campaigns'

    id = Column(UUIDType(), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUIDType(), ForeignKey('businesses.id', ondelete='CASCADE'), nullable=False, index=True)
    campaign_name = Column(String(255), nullable=False)
    platform = Column(String(100), nullable=True)
    campaign_type = Column(String(100), nullable=True)
    content = Column(Text, nullable=True)
    status = Column(String(50), default='draft')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    performance_metrics = Column(JSONType(), nullable=True)

    business = relationship("Business", back_populates="marketing_campaigns")

    def __repr__(self):
        return f"<MarketingCampaign(id={self.id}, business_id={self.business_id}, name={self.campaign_name}, status={self.status})>"


# Database connection helpers
def get_db_engine(database_url: Optional[str] = None):
    """Create database engine"""
    if database_url is None:
        database_url = os.environ.get("DATABASE_URL", "postgresql://bbbuser:password@localhost:5432/bbb_production")

    return create_engine(
        database_url,
        pool_pre_ping=True,  # Verify connections before use
        pool_size=10,  # Connection pool size
        max_overflow=20,  # Max connections beyond pool_size
        echo=False  # Set to True for SQL logging
    )


def get_session_maker(engine):
    """Create session maker"""
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)


def get_session(engine):
    """Get database session"""
    Session = get_session_maker(engine)
    return Session()


def init_db(database_url: Optional[str] = None):
    """Initialize database - create all tables"""
    engine = get_db_engine(database_url)
    Base.metadata.create_all(engine)
    return engine


def drop_db(database_url: Optional[str] = None):
    """Drop all tables - USE WITH CAUTION"""
    engine = get_db_engine(database_url)
    Base.metadata.drop_all(engine)
    return engine


# Dependency for FastAPI
def get_db():
    """FastAPI dependency for database sessions"""
    engine = get_db_engine()
    Session = get_session_maker(engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
