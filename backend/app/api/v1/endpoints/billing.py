from fastapi import APIRouter, Depends
from app.api import deps
from app.models import User, SubscriptionTier
from app.services.stripe import stripe_service

router = APIRouter()

@router.post("/checkout")
def create_checkout(
    tier: SubscriptionTier,
    current_user: User = Depends(deps.get_current_active_user),
):
    url = stripe_service.create_checkout_session(current_user.id, tier)
    return {"url": url}

@router.post("/portal")
def customer_portal(
    current_user: User = Depends(deps.get_current_active_user),
):
    # Mock portal URL
    return {"url": "https://billing.stripe.com/p/session/mock"}
