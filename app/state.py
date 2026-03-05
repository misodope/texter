"""In-memory state for tracking pending PRs per phone number"""
import re
import logging

logger = logging.getLogger(__name__)

# Maps phone number -> pending PR URL
_pending_prs: dict[str, str] = {}


def set_pending_pr(phone_number: str, pr_url: str) -> None:
    """Store a pending PR for a phone number"""
    _pending_prs[phone_number] = pr_url
    logger.info(f"Stored pending PR for {phone_number}: {pr_url}")


def get_pending_pr(phone_number: str) -> str | None:
    """Get the pending PR URL for a phone number"""
    return _pending_prs.get(phone_number)


def clear_pending_pr(phone_number: str) -> None:
    """Clear the pending PR for a phone number"""
    _pending_prs.pop(phone_number, None)
    logger.info(f"Cleared pending PR for {phone_number}")


def extract_pr_number(pr_url: str) -> str | None:
    """Extract the PR number from a GitHub PR URL"""
    match = re.search(r'/pull/(\d+)', pr_url)
    return match.group(1) if match else None
