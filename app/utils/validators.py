"""Request validation utilities"""
import logging
from fastapi import Request, HTTPException
from twilio.request_validator import RequestValidator
from app.config import settings

logger = logging.getLogger(__name__)


class TwilioRequestValidator:
    """Validates incoming Twilio webhook requests"""
    
    def __init__(self):
        self.validator = RequestValidator(settings.twilio_auth_token)
    
    async def validate_request(self, request: Request, form_data: dict) -> bool:
        """
        Validate that the request came from Twilio
        
        Args:
            request: FastAPI request object
            form_data: Form data from the request
            
        Returns:
            bool: True if valid, raises HTTPException otherwise
        """
        # Use configured base URL for validation when behind a proxy/tunnel,
        # since the internal Docker URL won't match what Twilio signed against.
        if settings.base_url:
            url = settings.base_url.rstrip("/") + request.url.path
        else:
            url = str(request.url)

        signature = request.headers.get("X-Twilio-Signature", "")

        # Ensure all form values are strings for Twilio validation
        params = {k: str(v) for k, v in form_data.items()}

        logger.debug(f"Twilio validation URL: {url}")
        logger.debug(f"Twilio signature present: {bool(signature)}")
        
        if not self.validator.validate(url, params, signature):
            logger.warning(f"Twilio signature validation failed for URL: {url}")
            raise HTTPException(
                status_code=403,
                detail="Invalid Twilio signature"
            )
        
        return True


twilio_validator = TwilioRequestValidator()
