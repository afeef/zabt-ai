# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
# Re-export everything from base models (preserves all existing imports)
from app.models.base import (
    TranscriptionType,
    TranscriptionBackend,
    SummaryTemplate,
    SummaryTemplateRead,
    SummaryTemplateListItem,
    UserTier,
    UserBase,
    User,
    MeetingBase,
    Meeting,
    TranscriptSegment,
    VisualSegment,
    StyleProfileBase,
    StyleProfile,
    StyleProfileCreate,
    StyleProfileRead,
    SubscriptionTier,
    Subscription,
    MeetingCreate,
    TranscriptWordRead,
    TranscriptSegmentRead,
    SpeakerBreakdown,
    MeetingRead,
    MeetingSummaryUpdate,
)

# Re-export new integration models
from app.models.integration import (
    IntegrationProvider,
    IntegrationStatus,
    Integration,
    IntegrationRead,
    IntegrationConnectResponse,
)

# Re-export email share models
from app.models.email_share import (
    EmailShareStatus,
    EmailShare,
    EmailShareRead,
    EmailShareCreate,
)

# Re-export device models
from app.models.device import (
    Device,
    DeviceCreate,
    DeviceRead,
)

__all__ = [
    # base
    "TranscriptionType",
    "TranscriptionBackend",
    "SummaryTemplate",
    "SummaryTemplateRead",
    "SummaryTemplateListItem",
    "UserTier",
    "UserBase",
    "User",
    "MeetingBase",
    "Meeting",
    "TranscriptSegment",
    "VisualSegment",
    "StyleProfileBase",
    "StyleProfile",
    "StyleProfileCreate",
    "StyleProfileRead",
    "SubscriptionTier",
    "Subscription",
    "MeetingCreate",
    "TranscriptWordRead",
    "TranscriptSegmentRead",
    "SpeakerBreakdown",
    "MeetingRead",
    "MeetingSummaryUpdate",
    # integration
    "IntegrationProvider",
    "IntegrationStatus",
    "Integration",
    "IntegrationRead",
    "IntegrationConnectResponse",
    # email_share
    "EmailShareStatus",
    "EmailShare",
    "EmailShareRead",
    "EmailShareCreate",
    # device
    "Device",
    "DeviceCreate",
    "DeviceRead",
]
