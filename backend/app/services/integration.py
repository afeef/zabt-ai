# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
import logging
from datetime import datetime, timedelta
from typing import List, Optional

from cryptography.fernet import Fernet
from sqlmodel import Session, select

from app.core.config import settings
from app.db.engine import engine
from app.models.integration import Integration, IntegrationProvider, IntegrationStatus
from app.services.base import BaseService

logger = logging.getLogger(__name__)


class IntegrationService(BaseService):
    def __init__(self, encryption_key: str = ""):
        key = encryption_key or settings.TOKEN_ENCRYPTION_KEY
        if not key:
            logger.warning(
                "TOKEN_ENCRYPTION_KEY is not set — IntegrationService encryption "
                "will fail at runtime. Generate a key with: "
                'python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"'
            )
            self._fernet = None
        else:
            self._fernet = Fernet(key.encode() if isinstance(key, str) else key)

    def _require_fernet(self) -> Fernet:
        if self._fernet is None:
            raise ValueError(
                "TOKEN_ENCRYPTION_KEY must be set before using encrypt/decrypt. "
                'Generate one with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"'
            )
        return self._fernet

    def encrypt_token(self, token: str) -> str:
        """Encrypt a token string using Fernet symmetric encryption."""
        f = self._require_fernet()
        return f.encrypt(token.encode()).decode()

    def decrypt_token(self, encrypted: str) -> str:
        """Decrypt a Fernet-encrypted token string."""
        f = self._require_fernet()
        return f.decrypt(encrypted.encode()).decode()

    def upsert_from_oauth(
        self,
        user_id: int,
        provider: IntegrationProvider,
        access_token: str,
        refresh_token: str,
        expires_in: int,
        scopes: List[str],
        provider_user_id: Optional[str] = None,
        provider_email: Optional[str] = None,
    ) -> Integration:
        """Create or update an integration from an OAuth callback."""
        encrypted_access = self.encrypt_token(access_token)
        encrypted_refresh = self.encrypt_token(refresh_token)
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in) if expires_in else None
        now = datetime.utcnow()

        with Session(engine) as session:
            statement = select(Integration).where(
                Integration.user_id == user_id,
                Integration.provider == provider,
            )
            existing = session.exec(statement).first()

            if existing:
                existing.access_token = encrypted_access
                existing.refresh_token = encrypted_refresh
                existing.expires_at = expires_at
                existing.scopes = scopes
                existing.provider_user_id = provider_user_id
                existing.provider_email = provider_email
                existing.status = IntegrationStatus.ACTIVE
                existing.updated_at = now
                session.add(existing)
                session.commit()
                session.refresh(existing)
                return existing
            else:
                integration = Integration(
                    user_id=user_id,
                    provider=provider,
                    access_token=encrypted_access,
                    refresh_token=encrypted_refresh,
                    expires_at=expires_at,
                    scopes=scopes,
                    provider_user_id=provider_user_id,
                    provider_email=provider_email,
                    status=IntegrationStatus.ACTIVE,
                    connected_at=now,
                    updated_at=now,
                )
                session.add(integration)
                session.commit()
                session.refresh(integration)
                return integration

    def get_for_user(self, user_id: int) -> List[Integration]:
        """Get all integrations for a user."""
        with Session(engine) as session:
            statement = select(Integration).where(Integration.user_id == user_id)
            return list(session.exec(statement).all())

    def get_by_provider(
        self, user_id: int, provider: IntegrationProvider
    ) -> Optional[Integration]:
        """Get a single integration by user and provider."""
        with Session(engine) as session:
            statement = select(Integration).where(
                Integration.user_id == user_id,
                Integration.provider == provider,
            )
            return session.exec(statement).first()

    def disconnect(self, user_id: int, provider: IntegrationProvider) -> bool:
        """Delete an integration (disconnect)."""
        with Session(engine) as session:
            statement = select(Integration).where(
                Integration.user_id == user_id,
                Integration.provider == provider,
            )
            integration = session.exec(statement).first()
            if not integration:
                return False
            session.delete(integration)
            session.commit()
            return True

    def update_tokens(
        self,
        integration_id: int,
        access_token: str,
        refresh_token: str,
        expires_in: int,
    ) -> Optional[Integration]:
        """Update tokens after a refresh flow."""
        with Session(engine) as session:
            integration = session.get(Integration, integration_id)
            if not integration:
                return None
            integration.access_token = self.encrypt_token(access_token)
            integration.refresh_token = self.encrypt_token(refresh_token)
            integration.expires_at = (
                datetime.utcnow() + timedelta(seconds=expires_in) if expires_in else None
            )
            integration.status = IntegrationStatus.ACTIVE
            integration.updated_at = datetime.utcnow()
            session.add(integration)
            session.commit()
            session.refresh(integration)
            return integration

    def mark_expired(self, integration_id: int) -> Optional[Integration]:
        """Mark an integration as expired (token refresh failed)."""
        with Session(engine) as session:
            integration = session.get(Integration, integration_id)
            if not integration:
                return None
            integration.status = IntegrationStatus.EXPIRED
            integration.updated_at = datetime.utcnow()
            session.add(integration)
            session.commit()
            session.refresh(integration)
            return integration


integration_service = IntegrationService()
