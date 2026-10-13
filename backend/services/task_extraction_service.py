import re
from typing import Iterable

from backend.schemas.meeting import ExtractedTaskDraft, TaskAssigneeOption


TASK_INTENT_KEYWORDS = [
    "should",
    "need to",
    "must",
    "complete",
    "submit",
    "prepare",
    "follow up",
]
DEADLINE_PATTERN = re.compile(
    r"\b(?:by\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)|"
    r"before\s+(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)|"
    r"tomorrow|next\s+week)\b",
    re.IGNORECASE,
)
SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[.!?])\s+|\n+")


def split_sentences(text: str) -> list[str]:
    return [sentence.strip(" -\t") for sentence in SENTENCE_SPLIT_PATTERN.split(text) if sentence.strip()]


def extract_participant_names(participants_text: str | None) -> list[str]:
    if not participants_text:
        return []
    names = []
    for part in re.split(r"[,;\n]", participants_text):
        cleaned = part.strip()
        if cleaned:
            names.append(cleaned)
    return names


def sentence_has_task_intent(sentence: str) -> bool:
    normalized = sentence.lower()
    return any(keyword in normalized for keyword in TASK_INTENT_KEYWORDS)


def detect_deadline(sentence: str) -> str | None:
    match = DEADLINE_PATTERN.search(sentence)
    return match.group(0) if match else None


def detect_assignee_name(sentence: str, candidate_names: Iterable[str]) -> str | None:
    sentence_lower = sentence.lower()
    for name in candidate_names:
        if name.lower() in sentence_lower:
            return name
    return None


def match_assignee_user_id(assignee_name: str | None, assignees: list[TaskAssigneeOption]) -> int | None:
    if not assignee_name:
        return None
    for assignee in assignees:
        if assignee.username.lower() == assignee_name.lower():
            return assignee.id
    return None


def extract_tasks_from_text(
    transcript_text: str,
    participants_text: str | None,
    assignees: list[TaskAssigneeOption],
) -> list[ExtractedTaskDraft]:
    sentences = split_sentences(transcript_text)
    participant_names = extract_participant_names(participants_text)
    candidate_names = participant_names + [user.username for user in assignees]

    extracted_tasks: list[ExtractedTaskDraft] = []
    seen_descriptions: set[str] = set()

    for sentence in sentences:
        if not sentence_has_task_intent(sentence):
            continue

        description = re.sub(r"\s+", " ", sentence).strip()
        normalized_description = description.lower()
        if normalized_description in seen_descriptions:
            continue
        seen_descriptions.add(normalized_description)

        assignee_name = detect_assignee_name(description, candidate_names)
        deadline = detect_deadline(description)
        extracted_tasks.append(
            ExtractedTaskDraft(
                description=description,
                assigned_to=match_assignee_user_id(assignee_name, assignees),
                assigned_to_name=assignee_name,
                deadline=deadline,
                status="pending_approval",
            )
        )

    return extracted_tasks
