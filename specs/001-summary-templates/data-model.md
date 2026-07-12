# Data Model: Summary Templates

**Feature**: `001-summary-templates`
**Date**: 2026-03-04

---

## New Table: `summarytemplate`

```python
class SummaryTemplate(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)                    # e.g., "General Summary", "Meeting Minutes"
    body: str                                         # Markdown template body (max 4000 chars)
    template_type: str = Field(default="custom")      # "built_in" | "custom"
    is_system_default: bool = Field(default=False)    # True for exactly one built_in template
    owner_id: Optional[int] = Field(
        default=None, foreign_key="user.id", index=True
    )                                                 # NULL for built-in templates
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

**Constraints**:
- `template_type` IN ("built_in", "custom")
- `body` length ≤ 4,000 characters (enforced at service layer)
- `is_system_default = True` for exactly one row (the "General Summary" built-in)
- `owner_id` MUST be NULL when `template_type = "built_in"`
- `owner_id` MUST be set when `template_type = "custom"`
- A user MUST NOT modify or delete `built_in` templates

**Indexes**:
- `owner_id` (for "list all templates for user" queries)
- `(template_type, is_system_default)` (for "fetch system default" queries)

---

## Modified Table: `user`

Add one field to the existing `User` model:

```python
# Added to existing User model
default_template_id: Optional[int] = Field(
    default=None, foreign_key="summarytemplate.id"
)
```

**Semantics**:
- `NULL` → user has not set a personal default; system uses the `is_system_default = True` built-in template
- Set → user's chosen default template for all future uploads

---

## Modified Table: `meeting`

Add two fields to the existing `Meeting` model:

```python
# Added to existing Meeting model
template_id: Optional[int] = Field(
    default=None, foreign_key="summarytemplate.id"
)
template_name: Optional[str] = None    # Denormalized; set at summarization time
```

**Semantics**:
- `template_id` → FK to the template used for the most recent summarization of this meeting
- `template_name` → snapshot of `template.name` at summarization time; displayed on summary tab even if template is later deleted
- Both fields are `NULL` until first summarization completes

---

## Entity Relationships

```
User (1) ──────────────────── (0..1) SummaryTemplate   [default_template_id FK]
User (1) ─── owns ──────────── (0..*) SummaryTemplate   [owner_id FK, custom only]
Meeting (0..*) ─── used ──── (0..1) SummaryTemplate   [template_id FK]
```

---

## Seeded Built-in Templates

These four rows are inserted at application startup (idempotent — insert only if name does not exist):

| name | template_type | is_system_default | owner_id |
|---|---|---|---|
| General Summary | built_in | True | NULL |
| Meeting Minutes | built_in | False | NULL |
| Action Items | built_in | False | NULL |
| Retrospective | built_in | False | NULL |

**Template body content** (abbreviated; full bodies defined in `services/template_seed.py`):

**General Summary** (system default):
```markdown
## Overview
[Provide a concise summary of the meeting's purpose and outcome]

## Key Topics Discussed
[List the main topics covered]

## Key Decisions
[List decisions made during the meeting]

## Action Items
[List action items with owners where mentioned]

## Open Questions
[List any unresolved questions]
```

**Meeting Minutes**:
```markdown
## Attendees
[List participants mentioned in the transcript]

## Agenda Items
[List agenda items discussed]

## Decisions Made
[List formal decisions reached]

## Action Items
[List tasks assigned, with owner and due date where mentioned]

## Next Steps
[List follow-up items and next meeting date if mentioned]
```

**Action Items**:
```markdown
## Action Items
Extract and list all action items mentioned in the meeting.
For each item include:
- Task description
- Owner (person responsible, if mentioned)
- Due date or timeline (if mentioned)
- Priority (if indicated)

Format as a numbered list.
```

**Retrospective**:
```markdown
## What Went Well
[List positive outcomes, successes, and things to continue]

## What Could Be Improved
[List challenges, blockers, and areas needing improvement]

## Action Items
[List concrete improvement actions with owners]

## Key Takeaways
[Summarize the main lessons learned]
```

---

## Read Models (API Response Shapes)

### SummaryTemplateRead

```python
class SummaryTemplateRead(SQLModel):
    id: int
    name: str
    body: str
    template_type: str           # "built_in" | "custom"
    is_system_default: bool
    owner_id: Optional[int]
    created_at: datetime
    updated_at: datetime
```

### SummaryTemplateListItem (lightweight, for dropdown)

```python
class SummaryTemplateListItem(SQLModel):
    id: int
    name: str
    template_type: str
    is_system_default: bool
```

### Meeting (extended)

Existing `MeetingRead` gains two additional fields:

```python
template_id: Optional[int]       # FK to template used for latest summary
template_name: Optional[str]     # Denormalized name for display
```

---

## State Transitions

**Template lifecycle (custom)**:
```
[created] → [active] → [set as default] → [default removed] → [deleted]
                 ↕                               ↕
             [edited]                        [edited]
```

**Meeting summarization with template**:
```
upload → [queued] → [processing: summarizing]
       → [completed: template_id=X, template_name="General Summary"]
       → user changes template → confirmation → [processing: summarizing]
       → [completed: template_id=Y, template_name="Meeting Minutes"]
```
