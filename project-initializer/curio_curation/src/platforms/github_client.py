from typing import Dict, List
import logging
from github import Github
from github.Repository import Repository

logger = logging.getLogger(__name__)

class GitHubIntegration:
    def __init__(self, token: str):
        """Initialize GitHub client."""
        self.client = Github(token)
    
    def create_repository(self, name: str, description: str = "", private: bool = False) -> Repository:
        """Create a new GitHub repository."""
        try:
            repo = self.client.get_user().create_repo(
                name=name,
                description=description,
                private=private
            )
            logger.info(f"Created GitHub repository: {name}")
            return repo
        except Exception as e:
            logger.error(f"Failed to create GitHub repository: {str(e)}")
            raise
    
    def create_milestone(self, repo: Repository, title: str, description: str = "") -> str:
        """Create a milestone in the repository."""
        try:
            milestone = repo.create_milestone(
                title=title,
                description=description
            )
            return milestone.number
        except Exception as e:
            logger.error(f"Failed to create GitHub milestone: {str(e)}")
            raise
    
    def create_issue(
        self,
        repo: Repository,
        title: str,
        body: str = "",
        labels: List[str] = None,
        milestone: int = None
    ) -> int:
        """Create an issue in the repository."""
        try:
            issue = repo.create_issue(
                title=title,
                body=body,
                labels=labels,
                milestone=milestone
            )
            return issue.number
        except Exception as e:
            logger.error(f"Failed to create GitHub issue: {str(e)}")
            raise

