import re
from functools import lru_cache

from fastapi import HTTPException, status


def split_sentences(text: str) -> list[str]:
    return [sentence.strip() for sentence in re.split(r"(?<=[.!?])\s+", text) if sentence.strip()]


def lightweight_summary(text: str, max_sentences: int = 3) -> str:
    sentences = split_sentences(text)
    if not sentences:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transcript text is empty and cannot be summarized",
        )
    return " ".join(sentences[:max_sentences])


@lru_cache(maxsize=1)
def get_summarizer():
    try:
        from transformers import pipeline

        return pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")
    except Exception:
        return None


def generate_summary(text: str) -> str:
    cleaned = text.strip()
    if not cleaned:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transcript text is empty and cannot be summarized",
        )

    summarizer = get_summarizer()
    if summarizer is None:
        return lightweight_summary(cleaned)

    try:
        result = summarizer(cleaned, max_length=130, min_length=30, do_sample=False)
        summary = result[0]["summary_text"].strip()
        return summary or lightweight_summary(cleaned)
    except Exception:
        return lightweight_summary(cleaned)


def extract_key_discussion_points(text: str, max_points: int = 5) -> list[str]:
    sentences = split_sentences(text)
    return sentences[:max_points] if sentences else []


def build_meeting_notes(title: str, participants: str | None, summary: str, text: str) -> str:
    key_points = extract_key_discussion_points(text)
    participant_line = participants if participants else "Not provided"
    discussion_text = "\n".join(
        f"- {point}" for point in key_points
    ) or "- No key discussion points extracted"

    return (
        f"Meeting Title: {title}\n"
        f"Participants: {participant_line}\n\n"
        f"Summary:\n{summary}\n\n"
        f"Key Discussion Points:\n{discussion_text}\n\n"
        f"Action Items Placeholder:\n- To be identified\n\n"
        f"Deadlines Placeholder:\n- To be identified"
    )
