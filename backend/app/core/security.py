# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
import httpx
from jose import jwt, JWTError, jwk
from jose.utils import base64url_decode
from fastapi import HTTPException, status, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings
import threading

security = HTTPBearer()

# ── JWKS cache ────────────────────────────────────────────────────────────────
# Cache the JWKS keys from Supabase to avoid fetching on every request.
_jwks_cache: list[dict] | None = None
_jwks_lock = threading.Lock()


def _get_jwks() -> list[dict]:
    """Fetch and cache Supabase's public JWKS keys."""
    global _jwks_cache
    if _jwks_cache is not None:
        return _jwks_cache

    with _jwks_lock:
        if _jwks_cache is not None:
            return _jwks_cache

        jwks_url = f"{settings.SUPABASE_URL}/auth/v1/.well-known/jwks.json"
        try:
            response = httpx.get(
                jwks_url,
                timeout=10,
                headers={"apikey": settings.SUPABASE_ANON_KEY},
            )
            response.raise_for_status()
            data = response.json()
            # Supabase returns {"keys": [...]}
            _jwks_cache = data.get("keys", [])
        except Exception as e:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=f"Could not fetch authentication keys: {str(e)}",
            )

    return _jwks_cache


def _clear_jwks_cache() -> None:
    """Clear the JWKS cache (call this to force a refresh)."""
    global _jwks_cache
    _jwks_cache = None


def verify_supabase_jwt(
    credentials: HTTPAuthorizationCredentials = Security(security),
) -> dict:
    """
    Verify a Supabase-issued JWT.

    Supports both:
    - New asymmetric keys (RS256 / ES256) via JWKS endpoint
    - Legacy symmetric secret (HS256) as a fallback
    """
    token = credentials.credentials

    # ── Try JWKS-based asymmetric verification first ──────────────────────────
    try:
        keys = _get_jwks()
        if keys:
            # Decode the header to find which key to use
            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header.get("kid")
            alg = unverified_header.get("alg", "RS256")

            # Find matching key by kid, or try all keys
            matching_keys = [k for k in keys if not kid or k.get("kid") == kid]
            if not matching_keys:
                matching_keys = keys  # try all if no kid match

            last_error = None
            for key_data in matching_keys:
                try:
                    payload = jwt.decode(
                        token,
                        key_data,
                        algorithms=[alg, "ES256", "RS256"],
                        options={"verify_aud": False},
                    )
                    return payload
                except JWTError as e:
                    last_error = e
                    continue

            if last_error:
                raise last_error
    except HTTPException:
        raise
    except JWTError:
        pass  # Fall through to legacy HS256 below
    except Exception:
        pass  # JWKS fetch failed or key error — try legacy fallback

    # ── Fallback: legacy HS256 symmetric secret ───────────────────────────────
    try:
        payload = jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
        return payload
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}",
            headers={"WWW-Authenticate": "Bearer"},
        )


# Keep backward-compatible alias used by other modules
verify_token = verify_supabase_jwt
