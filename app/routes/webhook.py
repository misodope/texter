"""Twilio webhook route handlers"""
import asyncio
import logging
from fastapi import APIRouter, Request, Form, Response
from app.services.twilio import twilio_service
from app.services.warp import warp_service
from app.utils.validators import twilio_validator
from app.utils.errors import SMSError, WarpTimeoutError
from app.config import settings
from app.state import set_pending_pr, get_pending_pr, clear_pending_pr, extract_pr_number

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhook", tags=["webhook"])


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/sms")
async def handle_sms(
    request: Request,
    From: str = Form(...),
    Body: str = Form(...),
    MessageSid: str = Form(None),
    AccountSid: str = Form(None),
):
    """
    Handle incoming SMS messages from Twilio.

    Message flow:
        test (personal number)  -> echo test response
        "1" (pending PR)        -> merge PR
        other (pending PR)      -> forward as change request
        anything else           -> new Warp agent run
    """
    try:
        form_data = await request.form()
        form_dict = dict(form_data)
        await twilio_validator.validate_request(request, form_dict)

        logger.info(f"Received SMS from {From}: {Body}")

        body_trimmed = Body.strip()
        is_personal = (
            settings.personal_phone_number
            and From == settings.personal_phone_number
        )

        # --- Test ping from personal number ---
        if is_personal and body_trimmed.lower() == "test":
            logger.info(f"Test message from personal number: {From}")
            return _handle_test(Body)

        pending_pr = get_pending_pr(From)

        # --- Merge a pending PR ---
        if pending_pr and body_trimmed == "1":
            logger.info(f"Merge requested by {From} for {pending_pr}")
            return _handle_merge_reply(From, pending_pr)

        # --- Change request on a pending PR ---
        if pending_pr:
            logger.info(f"Change request from {From} for {pending_pr}: {body_trimmed}")
            return await _handle_change_request(From, body_trimmed, pending_pr)

        # --- New request ---
        return await _handle_new_request(From, Body)

    except Exception as e:
        logger.error(f"Error handling SMS: {str(e)}")
        return _twiml_response("Error: Something went wrong. Please try again.")


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "texter"}


# ---------------------------------------------------------------------------
# Inline SMS handlers (called from the route, return a TwiML Response)
# ---------------------------------------------------------------------------

def _twiml_response(message: str) -> Response:
    """Build a TwiML XML response."""
    return Response(
        content=twilio_service.create_response(message),
        media_type="application/xml",
    )


def _handle_test(body: str) -> Response:
    """Echo back a test message for the personal number."""
    return _twiml_response(f"Test received! You said: {body}")


def _handle_merge_reply(from_number: str, pr_url: str) -> Response:
    """Kick off a background merge and acknowledge immediately."""
    asyncio.create_task(_poll_merge_and_notify(pr_url, from_number))
    pr_number = extract_pr_number(pr_url)
    ack = f"Merging PR #{pr_number}..." if pr_number else "Merging..."
    return _twiml_response(ack)


async def _handle_change_request(from_number: str, body: str, pr_url: str) -> Response:
    """Forward change-request text to Warp with PR context."""
    clear_pending_pr(from_number)
    prompt = f"Apply these changes to the PR at {pr_url}: {body}"
    return await _start_warp_run(prompt, from_number)


async def _handle_new_request(from_number: str, body: str) -> Response:
    """Start a brand-new Warp agent run."""
    return await _start_warp_run(body, from_number)


async def _start_warp_run(message: str, from_number: str) -> Response:
    """Shared helper: process a message through Warp and spawn the poll task."""
    result = await warp_service.process_message(message, from_number)

    if result["success"]:
        run_id = result["run_id"]
        asyncio.create_task(_poll_and_notify(run_id, from_number))
        ack = f"Working on it... (Run: {run_id[:8]})"
    else:
        ack = f"Error: {result.get('error', 'Could not start run')}"

    return _twiml_response(ack)


# ---------------------------------------------------------------------------
# Background tasks
# ---------------------------------------------------------------------------

async def _poll_and_notify(run_id: str, to_number: str):
    """
    Poll a Warp run until completion and send the result via SMS.
    If a PR is produced, stores it as pending so the user can reply to merge.
    """
    message = None
    try:
        result = await warp_service.wait_for_run_completion(run_id, timeout=300)

        pr_url = result.get("pr_url", "")
        if pr_url and "github.com" in pr_url:
            set_pending_pr(to_number, pr_url)
            message = (
                f"\u2705 Your code is ready!\n"
                f"PR: {pr_url}\n"
                f"Reply 1 for LGTM\n"
                f"Reply anything else to request changes"
            )
        else:
            message = f"Done! View: {result.get('session_link', 'Check Warp')}"

    except WarpTimeoutError as e:
        message = e.user_message
    except SMSError as e:
        message = e.user_message
    except Exception as e:
        logger.error(f"Unexpected error in _poll_and_notify: {str(e)}")
        message = "Error: Could not complete request"

    await _send_sms(to_number, message)


async def _poll_merge_and_notify(pr_url: str, to_number: str):
    """
    Merge a PR via Warp, poll until completion, and send a confirmation SMS.
    """
    pr_number = extract_pr_number(pr_url)
    message = None
    try:
        result = await warp_service.merge_pr(pr_url)

        if result["success"]:
            merge_result = await warp_service.wait_for_run_completion(
                result["run_id"], timeout=120
            )
            if merge_result.get("success"):
                clear_pending_pr(to_number)
                message = f"\U0001f680 Merged! #{pr_number}" if pr_number else "\U0001f680 Merged!"
            else:
                message = f"Error merging PR #{pr_number}"
        else:
            message = f"Error: {result.get('error', 'Could not start merge')}"

    except WarpTimeoutError:
        message = "Error: Merge timed out. Please try again."
    except SMSError as e:
        message = e.user_message
    except Exception as e:
        logger.error(f"Error in _poll_merge_and_notify: {str(e)}")
        message = f"Error merging PR #{pr_number}"

    await _send_sms(to_number, message)


async def _send_sms(to_number: str, message: str):
    """Send an SMS and log the result."""
    try:
        await twilio_service.send_sms(to=to_number, message=message)
        logger.info(f"Sent SMS to {to_number}: {message}")
    except Exception as e:
        logger.error(f"Failed to send SMS to {to_number}: {str(e)}")
