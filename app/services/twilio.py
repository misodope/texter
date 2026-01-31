"""Twilio service for SMS operations"""
from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from app.config import settings


class TwilioService:
    """Handles Twilio SMS operations"""
    
    def __init__(self):
        self.client = Client(
            settings.twilio_account_sid,
            settings.twilio_auth_token
        )
        self.from_number = settings.twilio_phone_number
    
    def create_response(self, message: str) -> str:
        """
        Create a TwiML response for Twilio
        
        Args:
            message: Message to send back to user
            
        Returns:
            str: TwiML formatted response
        """
        response = MessagingResponse()
        response.message(message)
        return str(response)
    
    async def send_sms(self, to: str, message: str) -> dict:
        """
        Send an SMS message via Twilio
        
        Args:
            to: Recipient phone number
            message: Message content
            
        Returns:
            dict: Message details
        """
        message = self.client.messages.create(
            body=message,
            from_=self.from_number,
            to=to
        )
        
        return {
            "sid": message.sid,
            "status": message.status,
            "to": message.to,
            "from": message.from_,
        }


twilio_service = TwilioService()
