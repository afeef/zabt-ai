from datetime import datetime
from typing import Optional, List
from enum import Enum
from sqlmodel import Field, SQLModel
from sqlalchemy import Column, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy import String


class IntegrationProvider(str, Enum):
    MICROSOFT = "microsoft"
    GOOGLE = "google"


class IntegrationStatus(str, Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"


class Integration(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint("user_id", "provider", name="uq_integration_user_provider"),
    )

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="user.id", index=True)
    provider: IntegrationProvider
    access_token: str
    refresh_token: str
    scopes: List[str] = Field(default_factory=list, sa_column=Column(ARRAY(String)))
    provider_user_id: Optional[str] = None
    provider_email: Optional[str] = None
    status: IntegrationStatus = Field(default=IntegrationStatus.ACTIVE)
    connected_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class IntegrationRead(SQLModel):
    id: int
    provider: IntegrationProvider
    provider_email: Optional[str]
    status: IntegrationStatus
    connected_at: datetime
    scopes: List[str] = []


class IntegrationConnectResponse(SQLModel):
    auth_url: str
