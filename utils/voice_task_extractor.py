import re
import difflib
from datetime import datetime, timedelta, date

def match_user(name, registered_users):
    """Enhanced user matching for two-word names and fuzzy matching"""
    import difflib
    name_parts = name.lower().split()
    user_names = [u['username'].lower() for u in registered_users]

    # Try full name match first
    full_match = difflib.get_close_matches(name.lower(), user_names, n=1, cutoff=0.5)
    if full_match:
        return next((u for u in registered_users if u['username'].lower() == full_match[0]), None)

    # Try first name only
    if name_parts:
        first_match = difflib.get_close_matches(name_parts[0], user_names, n=1, cutoff=0.6)
        if first_match:
            return next((u for u in registered_users if u['username'].lower() == first_match[0]), None)

    # Try last name only
    if len(name_parts) > 1:
        last_match = difflib.get_close_matches(name_parts[-1], user_names, n=1, cutoff=0.6)
        if last_match:
            return next((u for u in registered_users if u['username'].lower() == last_match[0]), None)

    return None

def extract_voice_tasks(transcript, registered_users):
    """
    Extract tasks from transcript and match to registered users
    Returns list of task dictionaries
    """
    tasks = []
    transcript_lower = transcript.lower()

    # Detect admin speaker
    admin_detected = any(phrase in transcript_lower for phrase in [
        "this is admin", "i am admin", "this is manager",
        "i am the manager", "speaking as admin"
    ])

    # Enhanced task assignment patterns for two-word names and "complete the task of"
    patterns = [
        # "Monish Kumar complete the task of presentation before 15th April"
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:please\s+)?(?:complete|finish|do|handle|prepare|send|submit|create|build|write|make|review|update|fix|check|call|schedule)\s+(?:the\s+)?(?:task\s+of\s+)?(.+?)\s+(?:by|within|before|due|on)\s+(.+?)(?:\.|,|$)',

        # "Monish you need to complete..."
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+you\s+(?:need|have)\s+to\s+(.+?)\s+(?:by|within|before|due|on)\s+(.+?)(?:\.|,|$)',

        # "Monish please complete..."
        r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+please\s+(.+?)\s+(?:by|within|before|due|on)\s+(.+?)(?:\.|,|$)',

        # "ask Monish to complete..."
        r'ask\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+to\s+(.+?)\s+(?:by|within|before|due|on)\s+(.+?)(?:\.|,|$)',

        # "assign ... to Monish by..."
        r'assign\s+(.+?)\s+to\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:by|within|before|due|on)\s+(.+?)(?:\.|,|$)',
    ]

    for pattern in patterns:
        matches = re.finditer(pattern, transcript, re.IGNORECASE)
        for match in matches:
            groups = match.groups()
            if len(groups) >= 3:
                # Determine which group contains the name based on pattern
                if "assign" in pattern.lower():
                    # assign pattern: task, name, deadline
                    task_desc = groups[0].strip()
                    name = groups[1].strip()
                    deadline_str = groups[2].strip()
                else:
                    # other patterns: name, task, deadline
                    name = groups[0].strip()
                    task_desc = groups[1].strip()
                    deadline_str = groups[2].strip()

                # Enhanced user matching
                matched_user = match_user(name, registered_users)

                # Parse deadline
                deadline = parse_deadline(deadline_str)

                tasks.append({
                    "assigned_to_name": name,
                    "matched_user": matched_user,
                    "task_description": task_desc,
                    "deadline_raw": deadline_str,
                    "deadline": deadline,
                    "confidence": "high" if matched_user else "low",
                    "admin_detected": admin_detected
                })

    return tasks


def parse_deadline(deadline_str):
    """Enhanced deadline parsing for "15th April 2026" format"""
    from datetime import date, timedelta
    import re

    today = date.today()
    dl = deadline_str.lower().strip()

    months = {
        "january":1, "february":2, "march":3, "april":4,
        "may":5, "june":6, "july":7, "august":8,
        "september":9, "october":10, "november":11, "december":12,
        "jan":1, "feb":2, "mar":3, "apr":4,
        "jun":6, "jul":7, "aug":8, "sep":9, "oct":10, "nov":11, "dec":12
    }

    # today / tomorrow / next week
    if "today" in dl: return today.isoformat()
    if "tomorrow" in dl: return (today + timedelta(days=1)).isoformat()
    if "next week" in dl: return (today + timedelta(weeks=1)).isoformat()
    if "end of week" in dl: return (today + timedelta(days=4)).isoformat()
    if "end of month" in dl: return today.replace(day=28).isoformat()

    # within X days
    m = re.search(r'within\s+(\d+)\s+days?', dl)
    if m: return (today + timedelta(days=int(m.group(1)))).isoformat()

    # next Monday/Friday etc
    days_map = {"monday":0,"tuesday":1,"wednesday":2,"thursday":3,"friday":4,"saturday":5,"sunday":6}
    for day_name, day_num in days_map.items():
        if day_name in dl:
            diff = day_num - today.weekday()
            if diff <= 0: diff += 7
            return (today + timedelta(days=diff)).isoformat()

    # "15th april 2026" or "april 15 2026" or "15 april 2026"
    patterns = [
        r'(\d{1,2})(?:st|nd|rd|th)?\s+(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|oct|nov|dec)\s+(\d{4})',
        r'(january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|jun|jul|aug|sep|oct|nov|dec)\s+(\d{1,2})(?:st|nd|rd|th)?\s+(\d{4})',
        r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})',
        r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',
    ]

    for pat in patterns:
        m = re.search(pat, dl)
        if m:
            try:
                g = m.groups()
                if g[0].isdigit() and not g[1].isdigit():
                    # "15th april 2026"
                    return date(int(g[2]), months[g[1]], int(g[0])).isoformat()
                elif not g[0].isdigit():
                    # "april 15 2026"
                    return date(int(g[2]), months[g[0]], int(g[1])).isoformat()
                else:
                    # numeric formats
                    return date(int(g[2]), int(g[1]), int(g[0])).isoformat()
            except Exception as e:
                print(f"Date parse error: {e}")
                continue

    # Default: 7 days
    return (today + timedelta(days=7)).isoformat()

