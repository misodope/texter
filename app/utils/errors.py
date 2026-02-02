"""Custom error types for SMS responses"""


class SMSError(Exception):
    """Base error for SMS operations"""
    def __init__(self, message: str, user_message: str = None):
        self.message = message
        self.user_message = user_message or "Error: Please try again"
        super().__init__(self.message)


class WarpTaskError(SMSError):
    """Warp agent task failed"""
    def __init__(self, message: str):
        super().__init__(
            message=message,
            user_message=f"Error: {message[:100]}" if len(message) > 100 else f"Error: {message}"
        )


class WarpTimeoutError(SMSError):
    """Warp task timed out"""
    def __init__(self):
        super().__init__(
            message="Task exceeded 5 minute timeout",
            user_message="Error: Request timed out. Please try again."
        )


class GitHubError(SMSError):
    """GitHub operation failed"""
    def __init__(self, message: str):
        super().__init__(
            message=message,
            user_message="Error: GitHub operation failed"
        )
