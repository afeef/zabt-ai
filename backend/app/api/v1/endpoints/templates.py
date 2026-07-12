# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
from typing import Any, List
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api import deps
from app.models import SummaryTemplateRead, User
from app.services.template import template_service

router = APIRouter()


class TemplateBody(BaseModel):
    name: str
    body: str


@router.get("/", response_model=List[SummaryTemplateRead])
def list_templates(
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    return template_service.list_for_user(current_user.id)


@router.post("/", response_model=SummaryTemplateRead, status_code=201)
def create_template(
    *,
    payload: TemplateBody,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    return template_service.create_custom(current_user.id, payload.name, payload.body)


@router.get("/{template_id}", response_model=SummaryTemplateRead)
def get_template(
    template_id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    return template_service.get_accessible(template_id, current_user.id)


@router.put("/{template_id}", response_model=SummaryTemplateRead)
def update_template(
    *,
    template_id: int,
    payload: TemplateBody,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    return template_service.update_custom(template_id, current_user.id, payload.name, payload.body)


@router.delete("/{template_id}", status_code=204)
def delete_template(
    template_id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> None:
    template_service.delete_custom(template_id, current_user.id)


@router.post("/{template_id}/set-default", response_model=dict)
def set_default_template(
    template_id: int,
    current_user: User = Depends(deps.get_current_active_user),
) -> Any:
    tmpl = template_service.set_user_default(current_user.id, template_id)
    return {"default_template_id": tmpl.id, "default_template_name": tmpl.name}
