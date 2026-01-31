"""Request validation utilities"""
from fastapi import Request, HTTPException
from twilio.request_validator import RequestValidator
from app.config import settings


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
        url = str(request.url)
        signature = request.headers.get("X-Twilio-Signature", "")
        
        if not self.validator.validate(url, form_data, signature):
            raise HTTPException(
                status_code=403,
                detail="Invalid Twilio signature"
            )
        
        return True


twilio_validator = TwilioRequestValidator()
