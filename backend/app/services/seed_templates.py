"""Seed system meeting type templates. Run once or idempotently."""
from sqlmodel import Session, select
from app.db.engine import engine
from app.models.base import SummaryTemplate
from app.services.meeting_intelligence import MEETING_TYPE_PROMPTS


def seed_meeting_type_templates():
    """Create or update system templates for each meeting type."""
    with Session(engine) as session:
        for meeting_type, config in MEETING_TYPE_PROMPTS.items():
            existing = session.exec(
                select(SummaryTemplate).where(
                    SummaryTemplate.name == f"Meeting Type: {meeting_type.replace('_', ' ').title()}",
                    SummaryTemplate.template_type == "built_in",
                )
            ).first()

            if existing:
                existing.meeting_type = meeting_type
                existing.output_schema = config["model"].model_json_schema()
                existing.layout_hint = config["layout_hint"]
                existing.body = config["prompt"]
                session.add(existing)
            else:
                template = SummaryTemplate(
                    name=f"Meeting Type: {meeting_type.replace('_', ' ').title()}",
                    body=config["prompt"],
                    template_type="built_in",
                    is_system_default=(meeting_type == "generic"),
                    meeting_type=meeting_type,
                    output_schema=config["model"].model_json_schema(),
                    layout_hint=config["layout_hint"],
                )
                session.add(template)

        session.commit()


if __name__ == "__main__":
    seed_meeting_type_templates()
    print("Meeting type templates seeded successfully.")
