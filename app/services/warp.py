"""Warp AI service for MCP integration"""
import logging
from typing import Optional
from warp_agent_sdk import AsyncWarpAPI
from app.config import settings

logger = logging.getLogger(__name__)


class WarpService:
    """Handles Warp AI and MCP interactions for GitHub operations"""
    
    def __init__(self):
        """Initialize Warp SDK client"""
        self.client = AsyncWarpAPI(
            api_key=settings.warp_api_key
        )
        self.environment_id = settings.warp_environment_id
        self.model_id = settings.warp_model_id
    
    async def process_message(self, message: str, from_number: str) -> dict:
        """
        Process user message and create GitHub PR using Warp/MCP
        
        Args:
            message: User's SMS message with PR instructions
            from_number: User's phone number
            
        Returns:
            dict: Result containing PR URL and status
        """
        try:
            logger.info(f"Processing message from {from_number}: {message}")
            
            # Create a prompt for the Warp agent to create a GitHub PR
            prompt = f"""
            The user sent the following request via SMS:
            {message}
            
            Please:
            1. Interpret the user's request
            2. Create a GitHub Pull Request based on their instructions
            3. Return the PR URL in your response
            
            Use the GitHub MCP server to interact with GitHub.
            """
            
            # Run the Warp agent with GitHub MCP server configuration
            response = await self.client.agent.run(
                prompt=prompt,
                config={
                    "environment_id": self.environment_id,
                    "model_id": self.model_id,
                    "name": f"sms-pr-request-{from_number}",
                    "base_prompt": "You are a helpful coding assistant that creates GitHub PRs based on user requests.",
                    "mcp_servers": {
                        "github": {
                            # Reference the GitHub MCP server configured in Warp
                            # This assumes you have the GitHub MCP server set up
                            "warp_id": "github"  # Use your configured GitHub MCP server ID
                        }
                    }
                }
            )
            
            logger.info(f"Warp task created: {response.task_id}")
            
            # Extract PR URL from the response
            # The actual implementation would parse the agent's output
            # For now, we'll return the task information
            
            result = {
                "success": True,
                "task_id": response.task_id,
                "pr_url": f"https://app.warp.dev/task/{response.task_id}",  # Link to Warp task
                "message": "PR creation task started! Check Warp for details.",
                "error": None
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing message: {str(e)}")
            return {
                "success": False,
                "pr_url": None,
                "message": "Failed to create PR",
                "error": str(e)
            }
    
    async def get_task_result(self, task_id: str, timeout: int = 60) -> Optional[str]:
        """
        Poll for task completion and extract PR URL from results
        
        Args:
            task_id: The Warp task ID
            timeout: Maximum time to wait in seconds
            
        Returns:
            Optional[str]: The GitHub PR URL if found, None otherwise
        """
        import asyncio
        import re
        
        try:
            # Poll for task completion
            # Note: You may need to adjust this based on the actual Warp SDK API
            elapsed = 0
            poll_interval = 5
            
            while elapsed < timeout:
                # Get task details (adjust based on actual SDK API)
                # task = await self.client.tasks.get(task_id)
                # 
                # if task.status == "completed":
                #     # Extract PR URL from task output
                #     # This regex looks for GitHub PR URLs in the response
                #     pr_url_pattern = r'https://github\.com/[\w-]+/[\w-]+/pull/\d+'
                #     matches = re.findall(pr_url_pattern, task.output)
                #     if matches:
                #         return matches[0]
                #     break
                # elif task.status == "failed":
                #     logger.error(f"Task {task_id} failed")
                #     break
                
                await asyncio.sleep(poll_interval)
                elapsed += poll_interval
            
            logger.warning(f"Timeout waiting for task {task_id} completion")
            return None
            
        except Exception as e:
            logger.error(f"Error getting task result: {str(e)}")
            return None
    
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
                        "warp_id": "github"
                    }
                }
            }
        )
        
        return f"https://app.warp.dev/task/{response.task_id}"


warp_service = WarpService()
