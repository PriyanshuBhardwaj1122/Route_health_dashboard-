"""
Keyword-based classifier for passenger feedback comments.

Classifies free-text comments into categories:
Crowding, Punctuality, Cleanliness, Driver Behaviour, Overall Experience, Other.

This is a lightweight rule-based classifier that can be swapped for an
LLM-based classifier later without changing the API contract.
"""

CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "Crowding": [
        "crowd", "packed", "full", "standing", "no seat", "overcrowd",
        "squeeze", "jam", "stuffed", "sardine", "can't move",
        "too many", "overload", "crush", "cramped",
    ],
    "Punctuality": [
        "late", "delay", "wait", "behind schedule", "early",
        "on time", "punctual", "schedule", "slow", "timing",
        "arrival", "depart", "missed", "long wait", "frequency",
    ],
    "Cleanliness": [
        "dirty", "clean", "trash", "garbage", "smell", "stain",
        "mess", "litter", "filthy", "hygiene", "dusty", "gross",
        "graffiti", "vandal", "spill", "debris", "sticky",
    ],
    "Driver Behaviour": [
        "driver", "rude", "aggressive", "brake", "swerve",
        "phone", "texting", "unsafe", "reckless", "courteous",
        "helpful", "skip", "skipped", "passed", "ignored",
        "stop", "disrespect", "attitude", "yell", "honk",
    ],
    "Overall Experience": [
        "experience", "service", "overall", "general", "impression",
        "comfortable", "recommend", "pleasant", "terrible", "awful",
        "great", "good", "bad", "worst", "best", "horrible",
        "excellent", "poor", "fine", "okay", "satisfactory",
    ],
}

# Bonus phrases — multi-word phrases that get extra weight (2 points each)
BONUS_PHRASES: dict[str, list[str]] = {
    "Crowding": ["too crowded", "no seats", "standing room", "packed bus", "can't board"],
    "Punctuality": ["behind schedule", "long wait", "came late", "didn't come", "no show"],
    "Cleanliness": ["bad smell", "dirty bus", "trash everywhere"],
    "Driver Behaviour": [
        "skipped stop", "skipped my stop", "rude driver", "bad driver",
        "drove past", "passed my stop", "didn't stop", "aggressive driving",
    ],
    "Overall Experience": ["worst experience", "terrible service", "great service"],
}


def classify_comment(text: str) -> str:
    """
    Classify a free-text comment into a feedback category.

    Returns the category with the most keyword matches.
    Falls back to 'Other' if nothing matches.
    """
    if not text:
        return "Other"

    lower = text.lower()
    scores: dict[str, int] = {}

    for category, keywords in CATEGORY_KEYWORDS.items():
        count = sum(1 for kw in keywords if kw in lower)
        if count > 0:
            scores[category] = count

    # Bonus for multi-word phrases
    for category, phrases in BONUS_PHRASES.items():
        bonus = sum(2 for ph in phrases if ph in lower)
        if bonus > 0:
            scores[category] = scores.get(category, 0) + bonus

    if not scores:
        return "Other"

    return max(scores, key=scores.get)
