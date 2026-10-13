from datetime import date, timedelta

WEEKDAY_LOOKUP = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


def next_weekday(reference_date: date, weekday_name: str) -> date:
    target = WEEKDAY_LOOKUP[weekday_name.lower()]
    days_ahead = (target - reference_date.weekday()) % 7
    if days_ahead == 0:
        days_ahead = 7
    return reference_date + timedelta(days=days_ahead)


def parse_deadline_text(deadline_text: str | None, reference_date: date | None = None) -> date | None:
    if not deadline_text:
        return None

    today = reference_date or date.today()
    normalized = deadline_text.strip().lower()

    if normalized == "today":
        return today
    if normalized == "tomorrow":
        return today + timedelta(days=1)
    if normalized == "next week":
        return today + timedelta(days=7)

    for prefix in ("by ", "before "):
        if normalized.startswith(prefix):
            weekday_name = normalized.removeprefix(prefix).strip()
            if weekday_name in WEEKDAY_LOOKUP:
                return next_weekday(today, weekday_name)

    return None


def classify_reminder(deadline_text: str | None, task_status: str, reference_date: date | None = None) -> tuple[str, date | None]:
    due_date = parse_deadline_text(deadline_text, reference_date=reference_date)
    if task_status == "completed":
        return "completed", due_date
    if due_date is None:
        return "no_deadline", None

    today = reference_date or date.today()
    days_until_due = (due_date - today).days
    if days_until_due < 0:
        return "overdue", due_date
    if days_until_due == 0:
        return "due_today", due_date
    if days_until_due <= 3:
        return "due_soon", due_date
    return "upcoming", due_date
