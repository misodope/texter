"""Warp AI service for MCP integration"""
import logging
from typing import Optional
from oz_agent_sdk import AsyncOzAPI
from app.config import settings
from app.utils.errors import WarpTaskError, WarpTimeoutError

logger = logging.getLogger(__name__)


class WarpService:
    """Handles Warp AI and MCP interactions for GitHub operations"""
    
    def __init__(self):
        """Initialize Warp SDK client"""
        self.client = AsyncOzAPI(
            api_key=settings.warp_api_key
        )
        self.environment_id = settings.warp_environment_id
        self.model_id = settings.warp_model_id
        self.github_mcp_id = settings.warp_github_mcp_id
    
    async def process_message(self, message: str, from_number: str) -> dict:
        """
        Process user message and create GitHub PR using Warp/MCP

        Args:
            message: User's SMS message with PR instructions
            from_number: User's phone number

        Returns:
            dict: Result containing task_id and status
        """
        try:
            logger.info(f"Processing message from {from_number}: {message}")

            # Concise prompt optimized for SMS responses
            prompt = f"""SMS request: {message}

Execute the request and respond with ONLY:
- On success: "PR: [full GitHub PR URL]"
- On error: "Error: [one-line description]"

No explanations. No markdown. Just the result."""

            # SMS-optimized agent configuration
            response = await self.client.agent.run(
                prompt=prompt,
                config={
                    "environment_id": self.environment_id,
                    "model_id": self.model_id,
                    "name": f"sms-{from_number[-4:]}",
                    "base_prompt": """You are an SMS bot. Your responses must be:
- Under 160 characters total
- Single line when possible
- Start with "PR:" or "Error:"
- Include full URLs (no markdown formatting)
- No explanations or extra text""",
                    "mcp_servers": {
                        "github": {
                            "warp_id": self.github_mcp_id
                        }
                    }
                }
            )

            logger.info(f"Warp run created: {response.run_id}")

            return {
                "success": True,
                "run_id": response.run_id,
                "error": None
            }

        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return {
                "success": False,
                "run_id": None,
                "error": str(e)[:100]
            }
    
    async def wait_for_run_completion(self, run_id: str, timeout: int = 300) -> dict:
        """
        Poll Warp run until completion or timeout

        Args:
            run_id: The Warp run ID to monitor
            timeout: Maximum time to wait in seconds (default: 5 minutes)

        Returns:
            dict: Result with success status, PR URL or error message
        """
        import asyncio

        elapsed = 0
        poll_interval = 3

        while elapsed < timeout:
            try:
                run = await self.client.agent.runs.retrieve(run_id)

                if run.state == "SUCCEEDED":
                    pr_url = self._extract_pr_url(run)
                    return {
                        "success": True,
                        "pr_url": pr_url,
                        "session_link": run.session_link,
                        "message": run.status_message.message if run.status_message else None
                    }
                elif run.state == "FAILED":
                    error_msg = run.status_message.message if run.status_message else "Run failed"
                    raise WarpTaskError(error_msg)
                # States: QUEUED, PENDING, CLAIMED, INPROGRESS - keep polling

            except WarpTaskError:
                raise
            except Exception as e:
                logger.error(f"Error polling run {run_id}: {str(e)}")

            await asyncio.sleep(poll_interval)
            elapsed += poll_interval

        raise WarpTimeoutError()

    def _extract_pr_url(self, run) -> str:
        """Extract GitHub PR URL from run output"""
        import re

        text_to_search = ""
        if run.status_message and run.status_message.message:
            text_to_search = run.status_message.message

        pr_url_pattern = r'https://github\.com/[\w.-]+/[\w.-]+/pull/\d+'
        matches = re.findall(pr_url_pattern, text_to_search)

        if matches:
            return matches[0]

        return run.session_link if run.session_link else "PR URL not found"
    
    async def create_github_pr(
        self,
        repo: str,
        title: str,
        body: str,
        branch: str,
        base: str = "main"
    ) -> str:
        """
        Create a GitHub PR using MCP (alternative direct method)
        
        Args:
            repo: Repository name (owner/repo)
            title: PR title
            body: PR description
            branch: Source branch
            base: Base branch (default: main)
            
        Returns:
            str: PR URL
        """
        logger.info(f"Creating PR in {repo}: {title}")
        
        prompt = f"""
        Create a GitHub Pull Request with the following details:
        - Repository: {repo}
        - Title: {title}
        - Description: {body}
        - Source branch: {branch}
        - Base branch: {base}
        
        Use the GitHub MCP server to create the PR and return the PR URL.
        """
        
        response = await self.client.agent.run(
            prompt=prompt,
            config={
                "environment_id": self.environment_id,
                "model_id": self.model_id,
                "name": f"create-pr-{repo}",
                "mcp_servers": {
                    "github": {
                        "warp_id": self.github_mcp_id,
                    }
                }
            }
        )
        
        return f"https://app.warp.dev/run/{response.run_id}"


warp_service = WarpService()
