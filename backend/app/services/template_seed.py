# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
from sqlmodel import Session, select
from app.db.engine import engine
from app.models import Meeting, SummaryTemplate

"""
Meeting Summary Templates for LLM-based transcript summarization.

Each template is designed to be injected as a prompt instruction alongside
a raw meeting transcript. The LLM should follow the structure and bracket
instructions to produce a well-organized summary.

Usage:
    Select the appropriate template based on meeting type, then include
    template["body"] in your system or user prompt alongside the transcript.

    Example prompt construction:
        f"Summarize the following meeting transcript using this structure:\n\n"
        f"{template['body']}\n\n"
        f"Transcript:\n{transcript_text}"
"""

BUILT_IN_TEMPLATES = [
    # =========================================================================
    # 1. PROGRAM ROLLOUT MEETING (System Default)
    # =========================================================================
    {
        "name": "Program Rollout Meeting",
        "description": (
            "For cross-functional rollout, implementation, and deployment meetings "
            "involving multiple stakeholders, vendors, and workstreams. Covers "
            "production testing, dealer/client preparation, change management, "
            "environment-specific issues, and compliance topics."
        ),
        "body": (
            "## Meeting Summary – [Extract the meeting date from the transcript]\n\n"
            "## Main Topics Discussed\n\n"
            "[For each major topic area discussed, create a numbered section. "
            "Within each section, use lettered sub-topics (A, B, C...) to group related discussion points. "
            "Capture specific details: system names, environment names, dealer/client names, "
            "state/region references, and any technical specifics mentioned. "
            "Preserve the level of detail — do not over-summarize. "
            "If a participant raised a concern or made a recommendation, attribute it by name or role.]\n\n"
            "### 1. [Topic Area Name]\n"
            "#### A. [Sub-Topic]\n"
            "- [Key finding, discussion point, or status update. Include names of systems, tools, or vendors mentioned.]\n"
            "- [If a problem was identified, state the problem and any proposed solution or workaround.]\n"
            "- [If consensus was reached on this sub-topic, state it explicitly.]\n\n"
            "#### B. [Sub-Topic]\n"
            "- [Continue as above]\n\n"
            "### 2. [Next Topic Area]\n"
            "[Continue the same numbered/lettered structure for every distinct topic area. "
            "Typical rollout topics include: production testing & integration, "
            "dealer/client preparation & workshops, change management & engagement, "
            "bug triage & prioritization, environment-specific or region-specific issues, "
            "timeline adjustments, resource constraints & scaling, "
            "compliance/regulatory/tax items, and vendor coordination.]\n\n"
            "## Action Items\n\n"
            "[Group action items by category. For each action item, extract:\n"
            "- The specific task to be completed\n"
            "- The owner (person or team name, exactly as mentioned in the transcript)\n"
            "- The deadline or target date if mentioned\n"
            "- Any dependency or blocker noted\n"
            "If no deadline was stated, omit the deadline field rather than guessing. "
            "If ownership is ambiguous, note it as 'TBD — raised during [topic]'.]\n\n"
            "### 1. [Action Category]\n"
            "- [Specific action] — **Owner:** [Name/Team] — **Deadline:** [Date if stated]\n"
            "- [Specific action] — **Owner:** [Name/Team]\n\n"
            "### 2. [Action Category]\n"
            "- [Continue as above, grouping logically by workstream or topic]\n\n"
            "## Follow-Up Points & Upcoming Meetings\n"
            "[List any scheduled or proposed follow-up meetings, site visits, workshops, or review sessions. "
            "Include the date (or approximate timing), purpose, and any preconditions mentioned "
            "(e.g., 'pending bug fixes', 'contingent on data from X').]\n"
            "- [Meeting/Event] — [Date/Timing] — [Purpose and any preconditions]\n\n"
            "## Key Decisions & Consensus\n"
            "[List every decision or point of consensus reached during the meeting. "
            "These should be stated as firm conclusions, not open discussion points. "
            "Include the rationale or data cited if it was discussed. "
            "If a decision was deferred or conditional, note it in Open Questions instead.]\n"
            "- [Decision, with brief rationale if discussed]\n\n"
            "## Open Questions & Risks\n"
            "[List any unresolved questions, deferred decisions, identified risks, "
            "or items awaiting external input. Include who is expected to resolve each item if mentioned.]\n"
            "- [Open question or risk] — **Pending:** [Name/Team/External party]\n"
        ),
        "is_system_default": True,
    },

    # =========================================================================
    # 2. TECHNICAL TRIAGE & BUG REVIEW
    # =========================================================================
    {
        "name": "Technical Triage & Bug Review",
        "description": (
            "For bug review sessions, incident triage, hotfix prioritization, "
            "and technical debt discussions. Captures issue severity, root causes, "
            "workarounds, and production deadlines."
        ),
        "body": (
            "## Meeting Summary – [Extract the meeting date from the transcript]\n\n"
            "## Current Release / Sprint Status\n"
            "[State the release name/version or sprint identifier, the original timeline, "
            "current status (on track / delayed / blocked), and the reason for any deviation. "
            "Include the number of open bugs/issues if mentioned.]\n\n"
            "## Bug & Issue Review\n\n"
            "[For each bug or issue discussed, create an entry in the appropriate priority table. "
            "Order by priority: critical first, then high, then medium/low. "
            "Extract exact system names, error descriptions, affected environments (DEV/QA/Pre-Prod/Prod), "
            "and any region/state/client specifics. If an issue ID or ticket number was mentioned, include it.]\n\n"
            "### Critical\n"
            "| Issue | Description | Root Cause | Status | Owner | ETA |\n"
            "|-------|-------------|------------|--------|-------|-----|\n"
            "| [Issue name/ID] | [What is broken and its business impact] | [Root cause if identified, otherwise 'Under investigation'] | [DEV/QA/Pre-Prod/Prod] | [Name] | [Date if stated] |\n\n"
            "### High Priority\n"
            "| Issue | Description | Root Cause | Status | Owner | ETA |\n"
            "|-------|-------------|------------|--------|-------|-----|\n"
            "| [Issue name/ID] | [Description and impact] | [Root cause] | [Status] | [Name] | [Date] |\n\n"
            "### Medium / Low Priority\n"
            "| Issue | Description | Status | Owner | ETA |\n"
            "|-------|-------------|--------|-------|-----|\n"
            "| [Issue name/ID] | [Description] | [Status] | [Name] | [Date] |\n\n"
            "## Prioritization Decisions\n"
            "[Capture any explicit prioritization calls made during the meeting. "
            "Include the reasoning, any data points cited (e.g., '14%% of deals affected vs 2%%'), "
            "trade-offs acknowledged, and what was deprioritized as a result.]\n"
            "- [Decision]: [Reasoning and data cited]\n"
            "- [What was deprioritized]: [Reason]\n\n"
            "## Workarounds in Effect\n"
            "[List any temporary workarounds agreed upon. Include who is responsible for "
            "communicating the workaround to affected users and when the permanent fix is expected.]\n"
            "- **Workaround:** [Description of the temporary process]\n"
            "  - **Scope:** [Who/where it applies]\n"
            "  - **Communicated by:** [Name]\n"
            "  - **Permanent fix ETA:** [Date if known]\n\n"
            "## Root Cause & Process Improvements\n"
            "[If the discussion surfaced systemic issues — late discovery of requirements, "
            "missing test coverage, resource vs. complexity debates, insufficient pre-production validation — "
            "capture them here with any agreed mitigation strategies.]\n"
            "- **Issue:** [Systemic problem identified]\n"
            "- **Mitigation:** [Agreed approach to prevent recurrence]\n\n"
            "## Action Items\n"
            "- [Specific action] — **Owner:** [Name/Team] — **Deadline:** [Date if stated]\n\n"
            "## Production Deadlines & Key Dates\n"
            "[State the hard deadline(s) mentioned and any date-sensitive milestones. "
            "Flag any dates at risk.]\n"
            "- [Milestone]: [Date] — [Conditions or risks noted]\n"
        ),
        "is_system_default": False,
    },

    # =========================================================================
    # 3. DAILY STANDUP / SYNC
    # =========================================================================
    {
        "name": "Standup / Daily Sync",
        "description": (
            "For short daily standups, sync calls, and quick status check-ins "
            "(typically under 30 minutes). Focuses on per-person updates, "
            "blockers, and quick decisions."
        ),
        "body": (
            "## Daily Sync – [Extract the meeting date from the transcript]\n\n"
            "## Team Updates\n"
            "[For each person who gave an update, create an entry. "
            "Keep updates concise and factual. Do not embellish or infer — "
            "only capture what was explicitly stated. If someone did not provide "
            "an update, do not create an entry for them.]\n\n"
            "### [Person Name]\n"
            "- **Completed:** [What they finished since last sync]\n"
            "- **In Progress:** [What they are currently working on]\n"
            "- **Blockers:** [Any blockers or dependencies mentioned, or 'None' if explicitly stated]\n\n"
            "[Repeat for each participant who provided an update]\n\n"
            "## Blockers & Escalations\n"
            "[Consolidate all blockers mentioned across individual updates. "
            "If a resolution path or escalation was discussed, include it. "
            "If no blockers were raised, state 'No blockers raised.']\n"
            "- [Blocker description] — **Raised by:** [Name] — **Resolution:** [Action agreed or 'Unresolved']\n\n"
            "## Decisions Made\n"
            "[Only include this section if decisions were actually made during the sync. "
            "Omit this section entirely if no decisions were made.]\n"
            "- [Decision]\n\n"
            "## Follow-Ups\n"
            "[Any items that need offline discussion or follow-up outside the standup.]\n"
            "- [Topic] — **Between:** [Names involved]\n"
        ),
        "is_system_default": False,
    },

    # =========================================================================
    # 4. SPRINT PLANNING / BACKLOG GROOMING
    # =========================================================================
    {
        "name": "Sprint Planning / Backlog Grooming",
        "description": (
            "For sprint planning, backlog refinement, story review, and estimation "
            "sessions. Captures story details, estimates, commitments, and deferrals."
        ),
        "body": (
            "## Meeting Summary – [Extract the meeting date from the transcript]\n\n"
            "## Sprint Overview\n"
            "- **Sprint:** [Sprint name/number if mentioned]\n"
            "- **Duration:** [Start date – End date if mentioned]\n"
            "- **Sprint Goal:** [The overarching goal if stated, otherwise omit this field]\n"
            "- **Team Capacity Notes:** [Any PTO, reduced capacity, holidays, or resource constraints mentioned. Omit if not discussed.]\n\n"
            "## Stories / Items Reviewed\n"
            "[For each user story or backlog item discussed, create an entry. "
            "Preserve story titles and IDs exactly as stated in the transcript. "
            "If acceptance criteria were discussed, include them as sub-bullets. "
            "If estimation was contentious, note the range of estimates discussed.]\n\n"
            "### [Story ID / Title]\n"
            "- **Description:** [What the story covers]\n"
            "- **Estimate:** [Story points or time estimate if discussed]\n"
            "- **Acceptance Criteria:** [If discussed, list them. Otherwise omit this field.]\n"
            "- **Dependencies:** [Any dependencies identified. Omit if none.]\n"
            "- **Status:** [Committed / Stretch / Deferred / Needs refinement]\n"
            "- **Notes:** [Any discussion points, concerns, or open questions raised]\n\n"
            "[Repeat for each story/item discussed]\n\n"
            "## Committed Work\n"
            "[List all stories/items the team committed to for this sprint, with their estimates.]\n"
            "- [Story ID / Title] — [Estimate]\n\n"
            "## Stretch Goals\n"
            "[Only include if stretch items were identified. Omit if not applicable.]\n"
            "- [Story ID / Title] — [Estimate] — [Condition for inclusion]\n\n"
            "## Deferred / Backlogged\n"
            "[List items explicitly deferred or sent back to the backlog, with the reason.]\n"
            "- [Story ID / Title] — **Reason:** [Why it was deferred]\n\n"
            "## Risks & Dependencies\n"
            "[Cross-cutting risks or external dependencies that affect the sprint.]\n"
            "- [Risk or dependency] — **Impact:** [What it could affect] — **Mitigation:** [If discussed]\n\n"
            "## Action Items\n"
            "- [Action] — **Owner:** [Name] — **Deadline:** [Date if stated]\n"
        ),
        "is_system_default": False,
    },

    # =========================================================================
    # 5. STAKEHOLDER / EXECUTIVE REVIEW
    # =========================================================================
    {
        "name": "Stakeholder / Executive Review",
        "description": (
            "For steering committee meetings, executive updates, stakeholder demos, "
            "and strategic reviews. Includes an executive summary readable standalone."
        ),
        "body": (
            "## Meeting Summary – [Extract the meeting date from the transcript]\n\n"
            "## Executive Summary\n"
            "[Provide a 3-5 sentence high-level summary of the meeting outcome. "
            "Focus on: overall program status, critical escalations or risks surfaced, "
            "key decisions made, and any strategic shifts or timeline changes. "
            "This section must be readable standalone by someone who will not read the full document.]\n\n"
            "## Program / Project Status\n"
            "[For each workstream or project area discussed, provide a structured status update.]\n\n"
            "### [Workstream / Project Name]\n"
            "- **Status:** [On Track / At Risk / Blocked / Completed]\n"
            "- **Summary:** [2-3 sentence status update]\n"
            "- **Key Milestones:** [Upcoming milestones and dates if mentioned]\n"
            "- **Risks / Escalations:** [Any risks raised or escalations needed. Omit if none.]\n\n"
            "[Repeat for each workstream discussed]\n\n"
            "## Demos & Stakeholder Feedback\n"
            "[Only include if feature demos or walkthroughs were presented. "
            "Capture what was shown, stakeholder reactions (both positive and negative), "
            "and any resulting change requests or direction changes.]\n"
            "- **Feature:** [What was demonstrated]\n"
            "- **Feedback:** [Stakeholder reactions and specific comments]\n"
            "- **Action:** [Changes requested or next steps agreed]\n\n"
            "## Decisions Made\n"
            "[List strategic or high-impact decisions. Include who made or endorsed the decision if stated, "
            "and any conditions or caveats attached.]\n"
            "- [Decision] — **Endorsed by:** [Name/Role if mentioned]\n\n"
            "## Escalations & Blockers\n"
            "[Items requiring executive attention or cross-organizational intervention.]\n"
            "- [Escalation] — **Raised by:** [Name] — **Action needed from:** [Name/Role]\n\n"
            "## Resource & Budget Items\n"
            "[Only include if resource allocation, budget, headcount, or staffing was discussed. "
            "Omit this section entirely if not applicable.]\n"
            "- [Item discussed] — **Decision/Action:** [What was agreed]\n\n"
            "## Action Items\n"
            "- [Action] — **Owner:** [Name/Team] — **Deadline:** [Date if stated]\n\n"
            "## Next Review\n"
            "- **Date:** [Next meeting date if scheduled]\n"
            "- **Expected Updates:** [What stakeholders expect to see by then]\n"
        ),
        "is_system_default": False,
    },

    # =========================================================================
    # 6. ONE-ON-ONE / 1:1
    # =========================================================================
    {
        "name": "One-on-One / 1:1",
        "description": (
            "For manager-report 1:1s, mentoring sessions, skip-levels, "
            "and career development conversations."
        ),
        "body": (
            "## 1:1 Summary – [Extract the meeting date from the transcript]\n"
            "**Participants:** [Extract names from the transcript]\n\n"
            "## Topics Discussed\n"
            "[For each topic raised, provide a brief summary. "
            "1:1s often cover a mix of work status, blockers, career development, "
            "feedback, team dynamics, and personal check-ins. "
            "Capture the substance without editorializing. "
            "If sensitive topics were discussed (performance concerns, interpersonal issues, "
            "compensation), summarize factually without adding judgment.]\n\n"
            "### [Topic]\n"
            "- [Key points discussed]\n"
            "- [Any advice given or feedback shared]\n\n"
            "[Repeat for each topic]\n\n"
            "## Feedback Exchanged\n"
            "[Only include if explicit feedback was given in either direction. "
            "Omit this section entirely if no feedback was exchanged.]\n"
            "- **From [Name]:** [Summary of feedback given]\n"
            "- **From [Name]:** [Summary of feedback given]\n\n"
            "## Action Items & Commitments\n"
            "- [Action or commitment] — **Owner:** [Name] — **By:** [Date if stated]\n\n"
            "## Topics for Next Time\n"
            "[Only include if explicitly mentioned during the meeting. Omit if not.]\n"
            "- [Topic to revisit]\n"
        ),
        "is_system_default": False,
    },

    # =========================================================================
    # 7. VENDOR / PARTNER COORDINATION
    # =========================================================================
    {
        "name": "Vendor / Partner Coordination",
        "description": (
            "For meetings with external vendors, integration partners, or "
            "third-party service providers. Separates commitments by party."
        ),
        "body": (
            "## Meeting Summary – [Extract the meeting date from the transcript]\n"
            "**Participants:** [List attendees with their organization affiliation "
            "if identifiable from the transcript]\n\n"
            "## Agenda / Purpose\n"
            "[State the purpose of the meeting if it was mentioned at the start. "
            "If not explicitly stated, infer the primary purpose from the topics discussed.]\n\n"
            "## Discussion Points\n\n"
            "[For each topic area, capture the discussion with attribution to the party "
            "that raised or responded to each point where identifiable.]\n\n"
            "### [Topic Area]\n"
            "- [Key point — attribute to the party that raised it, e.g., 'Vendor confirmed...', 'Our team raised...']\n"
            "- [Commitments made by either party]\n"
            "- [Any disagreements, open negotiations, or unresolved items]\n\n"
            "[Repeat for each topic area]\n\n"
            "## Integration / Technical Status\n"
            "[Only include if technical integration items were discussed. "
            "Capture: API endpoints, environment details, error codes, field mappings, "
            "configuration items, or data format specifics mentioned.]\n"
            "- [Technical item] — **Status:** [Working / Broken / Pending / Under investigation]\n\n"
            "## Commitments & Deliverables\n"
            "[Separate clearly by party so each side has a clear view of their obligations.]\n\n"
            "### Our Commitments\n"
            "- [What we agreed to deliver] — **Owner:** [Name] — **By:** [Date if stated]\n\n"
            "### Vendor / Partner Commitments\n"
            "- [What they agreed to deliver] — **Contact:** [Name if mentioned] — **By:** [Date if stated]\n\n"
            "## Escalations & Blockers\n"
            "[Any items requiring escalation on either side, or cross-party blockers.]\n"
            "- [Escalation] — **Party responsible:** [Us / Vendor / Both]\n\n"
            "## Next Meeting / Follow-Up\n"
            "- **Date:** [If scheduled]\n"
            "- **Expected Agenda:** [Topics or deliverables expected for next session]\n"
        ),
        "is_system_default": False,
    }
]


def seed_built_in_templates() -> None:
    with Session(engine) as session:
        seeded_names = {tmpl["name"] for tmpl in BUILT_IN_TEMPLATES}
        stale = session.exec(
            select(SummaryTemplate).where(
                SummaryTemplate.template_type == "built_in",
                SummaryTemplate.name.not_in(seeded_names),  # type: ignore[attr-defined]
            )
        ).all()
        stale_ids = [s.id for s in stale]
        if stale_ids:
            # Null out FK on meetings referencing stale templates before deleting
            affected_meetings = session.exec(
                select(Meeting).where(Meeting.template_id.in_(stale_ids))  # type: ignore[attr-defined]
            ).all()
            for m in affected_meetings:
                m.template_id = None
            session.flush()
        for s in stale:
            session.delete(s)
        session.flush()

        for tmpl in BUILT_IN_TEMPLATES:
            existing = session.exec(
                select(SummaryTemplate).where(
                    SummaryTemplate.name == tmpl["name"],
                    SummaryTemplate.template_type == "built_in",
                )
            ).first()
            if existing is None:
                session.add(
                    SummaryTemplate(
                        name=tmpl["name"],
                        body=tmpl["body"],
                        template_type="built_in",
                        is_system_default=tmpl["is_system_default"],
                        owner_id=None,
                    )
                )
            else:
                existing.body = tmpl["body"]
                existing.is_system_default = tmpl["is_system_default"]
        session.commit()
