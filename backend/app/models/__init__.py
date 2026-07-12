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

# Re-export new calendar event models
from app.models.calendar_event import (
    ConferencingPlatform,
    BotStatus,
    CalendarEvent,
    CalendarEventRead,
    CalendarEventUpdate,
)

# Re-export bot job models
from app.models.bot_job import (
    BotJobStatus,
    BotJobInfra,
    BotJob,
    BotJobRead,
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
    # calendar_event
    "ConferencingPlatform",
    "BotStatus",
    "CalendarEvent",
    "CalendarEventRead",
    "CalendarEventUpdate",
    # bot_job
    "BotJobStatus",
    "BotJobInfra",
    "BotJob",
    "BotJobRead",
    # device
    "Device",
    "DeviceCreate",
    "DeviceRead",
]
