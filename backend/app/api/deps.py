from typing import Generator
from fastapi import Depends, HTTPException, status
from sqlmodel import Session, select

from app.core import security
from app.db.engine import engine
from app.models import User
from app.services.notifications import notify


def get_db() -> Generator:
    with Session(engine) as session:
        yield session


def get_current_user(
    token_payload: dict = Depends(security.verify_supabase_jwt),
    db: Session = Depends(get_db),
) -> User:
    """
    Extract the Supabase user UUID from the verified JWT payload ('sub' claim)
    and perform JIT (Just-In-Time) provisioning into the local User table.
    The user_id is ALWAYS sourced from the token — never from the request body.
    """
    supabase_id = token_payload.get("sub")
    if not supabase_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials: missing sub claim",
        )

    user = db.exec(select(User).where(User.supabase_id == supabase_id)).first()
    if not user:
        # JIT Provisioning: create local profile on first authenticated request
        user = User(
            email=token_payload.get("email", ""),
            supabase_id=supabase_id,
            is_active=True,
        )
        db.add(user)
        db.commit()
        db.refresh(user)
        notify("new_user", user.email or supabase_id)
    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user),
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
