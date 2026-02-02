"""Twilio webhook route handlers"""
import asyncio
import logging
from fastapi import APIRouter, Request, Form, Response
from app.services.twilio import twilio_service
from app.services.warp import warp_service
from app.utils.validators import twilio_validator
from app.utils.errors import SMSError, WarpTimeoutError

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhook", tags=["webhook"])


async def send_completion_sms(task_id: str, to_number: str):
    """
    Background task to poll for Warp completion and send final result via REST API

    Args:
        task_id: The Warp task ID to monitor
        to_number: Phone number to send the result to
    """
    message = None
    try:
        result = await warp_service.wait_for_task_completion(task_id, timeout=300)

        pr_url = result.get("pr_url", "")
        if pr_url and "github.com" in pr_url:
            message = f"Done! PR: {pr_url}"
        else:
            message = f"Done! View: {result.get('session_link', 'Check Warp')}"

    except WarpTimeoutError as e:
        message = e.user_message
    except SMSError as e:
        message = e.user_message
    except Exception as e:
        logger.error(f"Unexpected error in send_completion_sms: {str(e)}")
        message = "Error: Could not complete request"

    try:
        await twilio_service.send_sms(to=to_number, message=message)
        logger.info(f"Sent completion SMS to {to_number}: {message}")
    except Exception as send_error:
        logger.error(f"Failed to send SMS: {str(send_error)}")


@router.post("/sms")
async def handle_sms(
    request: Request,
    From: str = Form(...),
    Body: str = Form(...),
    MessageSid: str = Form(None),
    AccountSid: str = Form(None)
):
    """
    Handle incoming SMS messages from Twilio

    Flow:
    1. Validate Twilio request signature
    2. Start Warp agent task
    3. Return immediate TwiML acknowledgment
    4. Spawn background task to poll for completion and send follow-up SMS
    """
    try:
        form_data = await request.form()
        form_dict = dict(form_data)

        await twilio_validator.validate_request(request, form_dict)

        logger.info(f"Received SMS from {From}: {Body}")

        # Start Warp task (returns immediately with task_id)
        result = await warp_service.process_message(Body, From)

        if result["success"]:
            task_id = result["task_id"]
            # Immediate acknowledgment
            ack_message = f"Working on it... (Task: {task_id[:8]})"

            # Spawn background task to poll and send final result
            asyncio.create_task(send_completion_sms(task_id, From))
        else:
            ack_message = f"Error: {result.get('error', 'Could not start task')}"

        twiml = twilio_service.create_response(ack_message)
        logger.info(f"Sending acknowledgment to {From}: {ack_message}")

        return Response(content=twiml, media_type="application/xml")

    except Exception as e:
        logger.error(f"Error handling SMS: {str(e)}")
        error_response = twilio_service.create_response(
            "Error: Something went wrong. Please try again."
        )
        return Response(content=error_response, media_type="application/xml")


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "texter"}
