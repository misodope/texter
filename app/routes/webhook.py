"""Twilio webhook route handlers"""
import logging
from fastapi import APIRouter, Request, Form, Response
from app.services.twilio import twilio_service
from app.services.warp import warp_service
from app.utils.validators import twilio_validator

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/webhook", tags=["webhook"])


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
    
    Args:
        request: FastAPI request object
        From: Sender's phone number
        Body: Message content
        MessageSid: Twilio message ID
        AccountSid: Twilio account ID
        
    Returns:
        TwiML response
    """
    try:
        # Get form data for validation
        form_data = await request.form()
        form_dict = dict(form_data)
        
        # Validate Twilio signature
        await twilio_validator.validate_request(request, form_dict)
        
        logger.info(f"Received SMS from {From}: {Body}")
        
        # Process the message with Warp/MCP to create GitHub PR
        result = await warp_service.process_message(Body, From)
        
        # Construct response message
        if result["success"]:
            response_text = f"{result['message']}\n\nPR: {result['pr_url']}"
        else:
            response_text = f"Sorry, there was an error: {result['error']}"
        
        # Create TwiML response
        twiml = twilio_service.create_response(response_text)
        
        logger.info(f"Sending response to {From}: {response_text}")
        
        return Response(content=twiml, media_type="application/xml")
        
    except Exception as e:
        logger.error(f"Error handling SMS: {str(e)}")
        error_response = twilio_service.create_response(
            "Sorry, something went wrong processing your request."
        )
        return Response(content=error_response, media_type="application/xml")


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "texter"}
