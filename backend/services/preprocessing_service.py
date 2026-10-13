import re
from typing import Dict

from fastapi import HTTPException, status


FILLER_PATTERNS = [
    r"\bum\b",
    r"\buh\b",
    r"\byou know\b",
    r"\blike\b",
]
NAME_PATTERN = re.compile(r"\b(?:[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\b")
DEADLINE_PATTERN = re.compile(
    r"\b(?:"
    r"\d{1,2}[/-]\d{1,2}(?:[/-]\d{2,4})?"
    r"|\d{4}-\d{2}-\d{2}"
    r"|(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\s+\d{1,2}(?:,\s*\d{4})?"
    r"|\d{1,2}:\d{2}\s*(?:am|pm)"
    r"|\b(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b"
    r"|\b(?:today|tomorrow|next week|next month|deadline)\b"
    r")\b",
    re.IGNORECASE,
)
SENTENCE_SPLIT_PATTERN = re.compile(r"(?<=[.!?])\s+")
MULTISPACE_PATTERN = re.compile(r"\s+")


def preserve_important_terms(text: str) -> tuple[str, Dict[str, str]]:
    placeholders: Dict[str, str] = {}

    def replace_match(match: re.Match[str]) -> str:
        placeholder = f"__KEEP_{len(placeholders)}__"
        placeholders[placeholder] = match.group(0)
        return placeholder

    text = NAME_PATTERN.sub(replace_match, text)
    text = DEADLINE_PATTERN.sub(replace_match, text)
    return text, placeholders


def lowercase_text(text: str) -> str:
    return text.lower()


def remove_filler_words(text: str) -> str:
    cleaned = text
    for pattern in FILLER_PATTERNS:
        cleaned = re.sub(pattern, " ", cleaned, flags=re.IGNORECASE)
    return cleaned


def remove_extra_spaces(text: str) -> str:
    cleaned = MULTISPACE_PATTERN.sub(" ", text)
    cleaned = re.sub(r"\s+([,.!?;:])", r"\1", cleaned)
    return cleaned.strip()


def split_into_sentences(text: str) -> list[str]:
    parts = SENTENCE_SPLIT_PATTERN.split(text)
    return [part.strip() for part in parts if part.strip()]


def restore_important_terms(text: str, placeholders: Dict[str, str]) -> str:
    restored = text
    for placeholder, original in placeholders.items():
        restored = restored.replace(placeholder.lower(), original)
        restored = restored.replace(placeholder, original)
    return restored


def preprocess_transcript_text(raw_text: str) -> str:
    if not raw_text or not raw_text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transcript text is empty and cannot be preprocessed",
        )

    protected_text, placeholders = preserve_important_terms(raw_text)
    normalized_text = lowercase_text(protected_text)
    normalized_text = remove_filler_words(normalized_text)
    normalized_text = remove_extra_spaces(normalized_text)

    sentences = split_into_sentences(normalized_text)
    if not sentences:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transcript did not contain usable text after preprocessing",
        )

    cleaned_text = "\n".join(sentences)
    cleaned_text = restore_important_terms(cleaned_text, placeholders)
    cleaned_text = remove_extra_spaces(cleaned_text.replace("\n", " \n ")).replace(" \n ", "\n")
    return cleaned_text
