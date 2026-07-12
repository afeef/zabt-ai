# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
from app.models import SubscriptionTier

class StripeService:
    def create_checkout_session(self, user_id: int, tier: SubscriptionTier) -> str:
        """
        Mock Stripe Checkout Session creation.
        Returns a mock URL.
        """
        return f"https://checkout.stripe.com/mock-session?user={user_id}&tier={tier}"

    def get_subscription_status(self, stripe_sub_id: str) -> dict:
        """
        Mock status check.
        """
        return {"status": "active", "current_period_end": 1735689600}

stripe_service = StripeService()
