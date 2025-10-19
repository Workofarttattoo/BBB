"""
Better Business Builder - Licensing and Revenue Share API
Copyright (c) 2025 Joshua Hendricks Cole (DBA: Corporation of Light). All Rights Reserved. PATENT PENDING.
"""
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session
from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, Text

from .database import get_db, User, Base
from .auth import get_current_user

router = APIRouter(prefix="/api/licensing", tags=["Licensing"])


# Database Models
class LicenseAgreement(Base):
    """Revenue share agreement records."""
    __tablename__ = "license_agreements"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    agreement_type = Column(String)  # "revenue_share" or "purchased"
    accepted_at = Column(DateTime)
    ip_address = Column(String)
    user_agent = Column(String)
    company_name = Column(String, nullable=True)
    legal_entity_type = Column(String, nullable=True)
    address = Column(Text, nullable=True)
    phone = Column(String, nullable=True)
    signed_document = Column(Text, nullable=True)  # Base64 encoded signature
    status = Column(String, default="active")  # active, terminated, suspended
    terminated_at = Column(DateTime, nullable=True)
    termination_reason = Column(Text, nullable=True)


class RevenueReport(Base):
    """Monthly revenue reporting for revenue share users."""
    __tablename__ = "revenue_reports"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    report_month = Column(String, index=True)  # YYYY-MM format
    gross_revenue = Column(Float)
    revenue_share_owed = Column(Float)  # 50% of gross
    payment_due_date = Column(DateTime)
    payment_received_date = Column(DateTime, nullable=True)
    payment_amount = Column(Float, nullable=True)
    payment_method = Column(String, nullable=True)
    transaction_id = Column(String, nullable=True)
    status = Column(String, default="pending")  # pending, paid, overdue, disputed
    submitted_at = Column(DateTime)
    notes = Column(Text, nullable=True)

    # Revenue breakdown
    product_sales = Column(Float, default=0.0)
    service_fees = Column(Float, default=0.0)
    subscription_revenue = Column(Float, default=0.0)
    consulting_fees = Column(Float, default=0.0)
    advertising_revenue = Column(Float, default=0.0)
    affiliate_commissions = Column(Float, default=0.0)
    other_revenue = Column(Float, default=0.0)


class PurchasedLicense(Base):
    """Purchased license records."""
    __tablename__ = "purchased_licenses"
    __table_args__ = {"extend_existing": True}

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, index=True)
    license_key = Column(String, unique=True, index=True)
    purchase_date = Column(DateTime)
    purchase_amount = Column(Float)
    payment_method = Column(String)
    transaction_id = Column(String)
    license_type = Column(String)  # starter, professional, enterprise
    max_users = Column(Integer)
    max_businesses = Column(Integer)
    support_level = Column(String)  # basic, premium, enterprise
    support_expires_at = Column(DateTime)
    is_active = Column(Boolean, default=True)
    company_name = Column(String, nullable=True)
    billing_email = Column(String)


# Request/Response Models
class RevenueShareAcceptRequest(BaseModel):
    """Request to accept revenue share agreement."""
    company_name: Optional[str] = None
    legal_entity_type: Optional[str] = None
    address: Optional[str] = None
    phone: Optional[str] = None
    confirmation: str = Field(..., description="Must be: 'I AGREE to 50% revenue share terms'")


class RevenueShareAcceptResponse(BaseModel):
    """Response after accepting agreement."""
    success: bool
    message: str
    agreement_id: int
    license_status: str
    accepted_at: datetime


class RevenueReportSubmitRequest(BaseModel):
    """Monthly revenue report submission."""
    report_month: str = Field(..., description="Format: YYYY-MM")
    product_sales: float = Field(default=0.0, ge=0)
    service_fees: float = Field(default=0.0, ge=0)
    subscription_revenue: float = Field(default=0.0, ge=0)
    consulting_fees: float = Field(default=0.0, ge=0)
    advertising_revenue: float = Field(default=0.0, ge=0)
    affiliate_commissions: float = Field(default=0.0, ge=0)
    other_revenue: float = Field(default=0.0, ge=0)
    notes: Optional[str] = None


class RevenueReportResponse(BaseModel):
    """Revenue report response."""
    success: bool
    report_id: int
    gross_revenue: float
    revenue_share_owed: float
    payment_due_date: datetime
    message: str


class LicenseStatusResponse(BaseModel):
    """Current license status."""
    license_status: str
    license_type: Optional[str] = None
    trial_expires_at: Optional[datetime] = None
    days_remaining: Optional[int] = None
    has_active_agreement: bool
    agreement_type: Optional[str] = None
    total_revenue_reported: float
    total_revenue_share_owed: float
    total_revenue_share_paid: float
    outstanding_balance: float
    overdue_reports: int


class PurchaseLicenseRequest(BaseModel):
    """Request to purchase full license."""
    license_type: str = Field(..., description="starter, professional, or enterprise")
    max_users: int
    max_businesses: int
    support_level: str = Field(..., description="basic, premium, or enterprise")
    company_name: Optional[str] = None
    billing_email: EmailStr


class PurchaseLicenseResponse(BaseModel):
    """Response with purchase details."""
    success: bool
    message: str
    license_key: Optional[str] = None
    amount: Optional[float] = None
    payment_url: Optional[str] = None  # Stripe checkout URL


# API Endpoints

@router.get("/status", response_model=LicenseStatusResponse)
async def get_license_status(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current license status and financial summary."""

    # Get agreement
    agreement = db.query(LicenseAgreement).filter(
        LicenseAgreement.user_id == current_user.id,
        LicenseAgreement.status == "active"
    ).first()

    # Get revenue reports
    reports = db.query(RevenueReport).filter(
        RevenueReport.user_id == current_user.id
    ).all()

    total_reported = sum(r.gross_revenue for r in reports)
    total_owed = sum(r.revenue_share_owed for r in reports)
    total_paid = sum(r.payment_amount or 0.0 for r in reports if r.status == "paid")
    outstanding = total_owed - total_paid

    overdue_count = len([
        r for r in reports
        if r.status == "pending" and r.payment_due_date < datetime.utcnow()
    ])

    # Calculate days remaining in trial
    days_remaining = None
    if current_user.license_status == "trial" and current_user.trial_expires_at:
        delta = current_user.trial_expires_at - datetime.utcnow()
        days_remaining = max(0, delta.days)

    return LicenseStatusResponse(
        license_status=current_user.license_status,
        license_type=getattr(current_user, "subscription_tier", None),
        trial_expires_at=current_user.trial_expires_at,
        days_remaining=days_remaining,
        has_active_agreement=agreement is not None,
        agreement_type=agreement.agreement_type if agreement else None,
        total_revenue_reported=total_reported,
        total_revenue_share_owed=total_owed,
        total_revenue_share_paid=total_paid,
        outstanding_balance=outstanding,
        overdue_reports=overdue_count
    )


@router.post("/accept-revenue-share", response_model=RevenueShareAcceptResponse)
async def accept_revenue_share(
    request: RevenueShareAcceptRequest,
    http_request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Accept 50% revenue share agreement (digital signature)."""

    # Verify confirmation text
    if request.confirmation != "I AGREE to 50% revenue share terms":
        raise HTTPException(
            status_code=400,
            detail="Invalid confirmation. Must type exactly: 'I AGREE to 50% revenue share terms'"
        )

    # Check if user already has an active agreement
    existing = db.query(LicenseAgreement).filter(
        LicenseAgreement.user_id == current_user.id,
        LicenseAgreement.status == "active"
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"You already have an active {existing.agreement_type} agreement"
        )

    # Create agreement record
    agreement = LicenseAgreement(
        user_id=current_user.id,
        agreement_type="revenue_share",
        accepted_at=datetime.utcnow(),
        ip_address=http_request.client.host,
        user_agent=http_request.headers.get("user-agent", ""),
        company_name=request.company_name,
        legal_entity_type=request.legal_entity_type,
        address=request.address,
        phone=request.phone,
        status="active"
    )
    db.add(agreement)

    # Update user license status
    current_user.license_status = "revenue_share"

    db.commit()
    db.refresh(agreement)

    return RevenueShareAcceptResponse(
        success=True,
        message="Revenue share agreement accepted successfully. You now have full access to all 26 quantum features. Monthly revenue reports due by the 15th of each month.",
        agreement_id=agreement.id,
        license_status="revenue_share",
        accepted_at=agreement.accepted_at
    )


@router.post("/submit-revenue-report", response_model=RevenueReportResponse)
async def submit_revenue_report(
    request: RevenueReportSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit monthly revenue report (required for revenue share users)."""

    # Verify user has revenue share agreement
    if current_user.license_status != "revenue_share":
        raise HTTPException(
            status_code=403,
            detail="Revenue reporting is only for revenue share agreement users"
        )

    # Check if report already exists for this month
    existing = db.query(RevenueReport).filter(
        RevenueReport.user_id == current_user.id,
        RevenueReport.report_month == request.report_month
    ).first()

    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Revenue report for {request.report_month} already submitted"
        )

    # Calculate totals
    gross_revenue = (
        request.product_sales +
        request.service_fees +
        request.subscription_revenue +
        request.consulting_fees +
        request.advertising_revenue +
        request.affiliate_commissions +
        request.other_revenue
    )

    revenue_share_owed = gross_revenue * 0.50  # 50%

    # Payment due 15 days after month end
    year, month = map(int, request.report_month.split("-"))
    if month == 12:
        next_month = datetime(year + 1, 1, 1)
    else:
        next_month = datetime(year, month + 1, 1)

    payment_due = next_month + timedelta(days=14)

    # Create report
    report = RevenueReport(
        user_id=current_user.id,
        report_month=request.report_month,
        gross_revenue=gross_revenue,
        revenue_share_owed=revenue_share_owed,
        payment_due_date=payment_due,
        status="pending",
        submitted_at=datetime.utcnow(),
        product_sales=request.product_sales,
        service_fees=request.service_fees,
        subscription_revenue=request.subscription_revenue,
        consulting_fees=request.consulting_fees,
        advertising_revenue=request.advertising_revenue,
        affiliate_commissions=request.affiliate_commissions,
        other_revenue=request.other_revenue,
        notes=request.notes
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    return RevenueReportResponse(
        success=True,
        report_id=report.id,
        gross_revenue=gross_revenue,
        revenue_share_owed=revenue_share_owed,
        payment_due_date=payment_due,
        message=f"Revenue report submitted. Payment of ${revenue_share_owed:,.2f} due by {payment_due.strftime('%Y-%m-%d')}"
    )


@router.get("/revenue-reports")
async def get_revenue_reports(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all revenue reports for current user."""

    reports = db.query(RevenueReport).filter(
        RevenueReport.user_id == current_user.id
    ).order_by(RevenueReport.report_month.desc()).all()

    return {
        "reports": [
            {
                "id": r.id,
                "month": r.report_month,
                "gross_revenue": r.gross_revenue,
                "revenue_share_owed": r.revenue_share_owed,
                "payment_due_date": r.payment_due_date,
                "payment_received_date": r.payment_received_date,
                "status": r.status,
                "breakdown": {
                    "product_sales": r.product_sales,
                    "service_fees": r.service_fees,
                    "subscription_revenue": r.subscription_revenue,
                    "consulting_fees": r.consulting_fees,
                    "advertising_revenue": r.advertising_revenue,
                    "affiliate_commissions": r.affiliate_commissions,
                    "other_revenue": r.other_revenue
                }
            }
            for r in reports
        ]
    }


@router.post("/purchase-license", response_model=PurchaseLicenseResponse)
async def purchase_license(
    request: PurchaseLicenseRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Purchase a full license (no revenue sharing required)."""

    # Calculate pricing based on tier
    pricing = {
        "starter": {"base": 2999, "per_user": 99, "per_business": 149},
        "professional": {"base": 9999, "per_user": 199, "per_business": 299},
        "enterprise": {"base": 29999, "per_user": 299, "per_business": 499}
    }

    if request.license_type not in pricing:
        raise HTTPException(
            status_code=400,
            detail="Invalid license type. Choose: starter, professional, or enterprise"
        )

    tier_pricing = pricing[request.license_type]
    amount = (
        tier_pricing["base"] +
        (request.max_users * tier_pricing["per_user"]) +
        (request.max_businesses * tier_pricing["per_business"])
    )

    # Add support level cost
    support_costs = {"basic": 0, "premium": 1999, "enterprise": 4999}
    amount += support_costs.get(request.support_level, 0)

    # In production, integrate with Stripe/PayPal
    # For now, return payment details

    return PurchaseLicenseResponse(
        success=True,
        message=f"License quote generated. Contact josh@corporationoflight.com to complete purchase.",
        amount=amount,
        payment_url=None  # Would be Stripe checkout URL in production
    )


@router.post("/terminate-agreement")
async def terminate_agreement(
    reason: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Terminate revenue share agreement (must cease using BBB)."""

    agreement = db.query(LicenseAgreement).filter(
        LicenseAgreement.user_id == current_user.id,
        LicenseAgreement.status == "active"
    ).first()

    if not agreement:
        raise HTTPException(
            status_code=404,
            detail="No active agreement found"
        )

    # Mark agreement as terminated
    agreement.status = "terminated"
    agreement.terminated_at = datetime.utcnow()
    agreement.termination_reason = reason

    # Revert user to trial (or unlicensed if trial expired)
    if current_user.trial_expires_at and current_user.trial_expires_at > datetime.utcnow():
        current_user.license_status = "trial"
    else:
        current_user.license_status = "unlicensed"

    db.commit()

    # Check for outstanding payments
    outstanding = db.query(RevenueReport).filter(
        RevenueReport.user_id == current_user.id,
        RevenueReport.status != "paid"
    ).all()

    outstanding_amount = sum(r.revenue_share_owed for r in outstanding)

    return {
        "success": True,
        "message": "Agreement terminated successfully. All use of BBB Software must cease immediately.",
        "outstanding_payments": len(outstanding),
        "outstanding_amount": outstanding_amount,
        "note": "Outstanding payments remain due even after termination."
    }


@router.get("/agreement-document")
async def get_agreement_document(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get signed agreement document for records."""

    agreement = db.query(LicenseAgreement).filter(
        LicenseAgreement.user_id == current_user.id
    ).first()

    if not agreement:
        raise HTTPException(
            status_code=404,
            detail="No agreement found"
        )

    return {
        "agreement_id": agreement.id,
        "type": agreement.agreement_type,
        "accepted_at": agreement.accepted_at,
        "status": agreement.status,
        "ip_address": agreement.ip_address,
        "company_name": agreement.company_name,
        "legal_entity_type": agreement.legal_entity_type,
        "address": agreement.address,
        "phone": agreement.phone,
        "terms": "See REVENUE_SHARE_AGREEMENT.md for full terms"
    }
