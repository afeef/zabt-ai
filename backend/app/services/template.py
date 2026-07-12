from datetime import datetime
from typing import List, Optional
from fastapi import HTTPException, status
from sqlmodel import Session, select, or_
from app.db.engine import engine
from app.models import SummaryTemplate, User
from app.services.base import BaseService


class TemplateService(BaseService):
    def list_for_user(self, user_id: int) -> List[SummaryTemplate]:
        with Session(engine) as session:
            statement = select(SummaryTemplate).where(
                or_(
                    SummaryTemplate.template_type == "built_in",
                    SummaryTemplate.owner_id == user_id,
                )
            )
            return list(session.exec(statement).all())

    def get_accessible(self, template_id: int, user_id: int) -> SummaryTemplate:
        with Session(engine) as session:
            tmpl = session.get(SummaryTemplate, template_id)
            if tmpl is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found.")
            if tmpl.template_type == "built_in":
                return tmpl
            if tmpl.owner_id != user_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
            return tmpl

    def create_custom(self, user_id: int, name: str, body: str) -> SummaryTemplate:
        self._validate_body(body)
        self._validate_name(name)
        tmpl = SummaryTemplate(
            name=name,
            body=body,
            template_type="custom",
            is_system_default=False,
            owner_id=user_id,
        )
        return self.save(tmpl)

    def update_custom(self, template_id: int, user_id: int, name: str, body: str) -> SummaryTemplate:
        self._validate_body(body)
        self._validate_name(name)
        with Session(engine) as session:
            tmpl = session.get(SummaryTemplate, template_id)
            if tmpl is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found.")
            if tmpl.template_type == "built_in":
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Built-in templates cannot be modified.")
            if tmpl.owner_id != user_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
            tmpl.name = name
            tmpl.body = body
            tmpl.updated_at = datetime.utcnow()
            session.add(tmpl)
            session.commit()
            session.refresh(tmpl)
            return tmpl

    def delete_custom(self, template_id: int, user_id: int) -> None:
        with Session(engine) as session:
            tmpl = session.get(SummaryTemplate, template_id)
            if tmpl is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found.")
            if tmpl.template_type == "built_in":
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Built-in templates cannot be deleted.")
            if tmpl.owner_id != user_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")
            # Clear personal default if it points to this template
            user = session.get(User, user_id)
            if user and user.default_template_id == template_id:
                user.default_template_id = None
                session.add(user)
            session.delete(tmpl)
            session.commit()

    def set_user_default(self, user_id: int, template_id: int) -> SummaryTemplate:
        tmpl = self.get_accessible(template_id, user_id)
        with Session(engine) as session:
            user = session.get(User, user_id)
            if user is None:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")
            user.default_template_id = template_id
            session.add(user)
            session.commit()
        return tmpl

    def get_active_default(self, user_id: int) -> Optional[SummaryTemplate]:
        with Session(engine) as session:
            user = session.get(User, user_id)
            if user and user.default_template_id:
                tmpl = session.get(SummaryTemplate, user.default_template_id)
                if tmpl:
                    return tmpl
            # Fall back to system default
            tmpl = session.exec(
                select(SummaryTemplate).where(
                    SummaryTemplate.is_system_default == True,
                    SummaryTemplate.template_type == "built_in",
                )
            ).first()
            return tmpl

    @staticmethod
    def _validate_body(body: str) -> None:
        if not body or not body.strip():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Template body cannot be empty.")
        if len(body) > 4000:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Template body must not exceed 4000 characters.")

    @staticmethod
    def _validate_name(name: str) -> None:
        if not name or not name.strip():
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Template name cannot be empty.")
        if len(name) > 100:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Template name must not exceed 100 characters.")


template_service = TemplateService()
