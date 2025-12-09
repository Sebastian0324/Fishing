"""Tag helpers: allowed taxonomy and validation utilities.

This module provides a placeholder list of tags (20 entries) and simple
validation/normalization helpers. Replace or extend `DEFAULT_TAGS` with
your preferred taxonomy later.
"""
from typing import List

# Placeholder taxonomy (20 categories). These are examples — replace as needed.
DEFAULT_TAGS: List[str] = [
    "Account Notice",
    "Payment/Invoice",
    "Security Alert",
    "Password Reset",
    "Shipping/Delivery",
    "Subscription",
    "Promotion/Offer",
    "Job Alert",
    "Social Notification",
    "Banking",
    "Legal/Policy",
    "System Alert",
    "Survey/Feedback",
    "News/Newsletter",
    "Authentication",
    "Two-Factor",
    "Travel/Booking",
    "Support/Ticket",
    "Confirmation/Receipt",
    "Other"
]


def get_allowed_tags() -> List[str]:
    """Return the current allowed tags list."""
    return DEFAULT_TAGS


def normalize_tag(tag: str) -> str:
    if tag is None:
        return None
    t = str(tag).strip()
    return t


def is_valid_tag(tag: str) -> bool:
    """Check whether a tag is in the allowed list (case-sensitive exact match).

    If you prefer case-insensitive matching, change to compare lowercased forms.
    """
    if tag is None:
        return False
    t = normalize_tag(tag)
    return t in DEFAULT_TAGS


def suggest_tag_from_parsed(parsed: dict) -> str:
    """Return a suggested tag (string) based on simple heuristics applied to the parsed email.

    This is intentionally lightweight: keyword matching against Subject, Body, Sender, and URLs.
    We can replace or extend this with a more advanced model (rules, ML, or LLM) later.
    """
    if not parsed or not isinstance(parsed, dict):
        return None

    subject = (parsed.get('subject') or parsed.get('Subject') or '')
    body = ''
    try:
        body = parsed.get('body', {}).get('text', '') or ''
    except Exception:
        body = ''
    sender = ''
    try:
        sender = parsed.get('sender', {}).get('email', '') or ''
    except Exception:
        sender = ''

    text = ' '.join([subject, body, sender]).lower()

    # Simple keyword -> tag mapping (small sample). Extend as needed.
    mapping = {
        'password': 'Password Reset',
        'reset your password': 'Password Reset',
        'invoice': 'Payment/Invoice',
        'payment': 'Payment/Invoice',
        'subscription': 'Subscription',
        'ship': 'Shipping/Delivery',
        'delivery': 'Shipping/Delivery',
        'account': 'Account Notice',
        'confirm': 'Confirmation/Receipt',
        'verify': 'Authentication',
        'security': 'Security Alert',
        'bank': 'Banking',
        'newsletter': 'News/Newsletter',
        'job': 'Job Alert',
        'support': 'Support/Ticket'
    }

    for k, tag in mapping.items():
        if k in text:
            # Return the first matching allowed tag
            if tag in DEFAULT_TAGS:
                return tag

    # fallback
    return None
