"""Warp AI service for MCP integration"""
import logging
from typing import Optional
from oz_agent_sdk import AsyncOzAPI
from app.config import settings
from app.utils.errors import WarpTaskError, WarpTimeoutError

logger = logging.getLogger(__name__)


# Terminal run states that indicate the agent is done
_TERMINAL_STATES = {"SUCCEEDED", "FAILED", "ERROR", "CANCELLED"}


class WarpService:
    """Handles Warp AI and MCP interactions for GitHub operations"""
    
    def __init__(self):
        """Initialize Warp SDK client"""
        if not settings.warp_api_key:
            raise ValueError("WARP_API_KEY is required")
        if not settings.github_pat:
            raise ValueError("GITHUB_PAT is required — MCP server will crash without it")

        self.client = AsyncOzAPI(
            api_key=settings.warp_api_key
        )
        self.environment_id = settings.warp_environment_id
        self.github_mcp_config = {
            "command": "npx",
            "args": ["-y", "@modelcontextprotocol/server-github"],
            "env": {
                "GITHUB_PERSONAL_ACCESS_TOKEN": settings.github_pat
            }
        }
    
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

            prompt = f"""You are an SMS bot. Keep your final status message under 160 characters.
On success start with "PR:" followed by the full GitHub PR URL.
On error start with "Error:" followed by a one-line description.
No markdown. No explanations.

SMS request: {message}"""

            response = await self.client.agent.run(
                prompt=prompt,
                config={
                    "environment_id": self.environment_id,
                    "mcp_servers": {
                        "github": self.github_mcp_config
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
        last_state = None

        logger.info(f"Polling run {run_id} (timeout={timeout}s)")

        while elapsed < timeout:
            try:
                run = await self.client.agent.runs.retrieve(run_id)
                status_msg = run.status_message.message if run.status_message else None

                # Log state transitions
                if run.state != last_state:
                    logger.info(f"Run {run_id[:8]} state: {last_state} -> {run.state}")
                    if status_msg:
                        logger.info(f"Run {run_id[:8]} status: {status_msg[:200]}")
                    last_state = run.state

                if run.state == "SUCCEEDED":
                    pr_url = self._extract_pr_url(run)
                    return {
                        "success": True,
                        "pr_url": pr_url,
                        "session_link": run.session_link,
                        "message": status_msg
                    }
                elif run.state in _TERMINAL_STATES:
                    error_msg = status_msg or f"Run ended with state: {run.state}"
                    logger.error(f"Run {run_id[:8]} terminal failure [{run.state}]: {error_msg[:300]}")
                    raise WarpTaskError(error_msg)

                # Still in progress — back off gradually
                await asyncio.sleep(poll_interval)
                elapsed += poll_interval
                if poll_interval < 10:
                    poll_interval = min(poll_interval + 1, 10)

            except WarpTaskError:
                raise
            except Exception as e:
                logger.error(f"Error polling run {run_id[:8]}: {str(e)}")
                await asyncio.sleep(poll_interval)
                elapsed += poll_interval

        logger.error(f"Run {run_id[:8]} timed out after {timeout}s (last state: {last_state})")
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
                "mcp_servers": {
                    "github": self.github_mcp_config
                }
            }
        )
        
        return f"https://app.warp.dev/run/{response.run_id}"


warp_service = WarpService()
