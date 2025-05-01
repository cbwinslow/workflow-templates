#!/usr/bin/env python3
"""
Project Initializer

This script takes a business plan or prompt as input and converts it into:
- Structured project tasks
- Trello cards
- Git issues and pull request templates
- Supporting GitHub, GitLab, and Bitbucket platforms

Usage:
    python project_initializer.py --input business_plan.md --config config.yml

Author: Your Name
License: MIT
"""

import argparse
import logging
import os
import re
import sys
import yaml
from typing import Dict, List, Any

from curio_curation.src.auth import get_auth_token
from curio_curation.src.platforms.github_api_client import GithubAPIClient
from curio_curation.src.platforms.trello_api_client import TrelloAPI
try:
    import openai
    import requests
    from git import Repo
    from trello import TrelloClient
except ImportError:
    print("Error: Required dependencies not installed.")
    print("Install dependencies with: pip install openai requests gitpython py-trello")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("project_initializer.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("project_initializer")

class ConfigManager:
    """Handles loading and validating configuration from YAML files."""
    
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.config = {}
        self.load_config()
        
    def load_config(self) -> None:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as file:
                self.config = yaml.safe_load(file)
            logger.info(f"Configuration loaded from {self.config_path}")
            self.validate_config()
        except FileNotFoundError:
            logger.error(f"Config file not found: {self.config_path}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML: {e}")
            raise
            
    def validate_config(self) -> None:
        """Validate required configuration sections and parameters."""
        required_sections = ["credentials", "project_settings", "task_categories", "git_platforms"]
        for section in required_sections:
            if section not in self.config:
                logger.error(f"Missing required configuration section: {section}")
                raise ValueError(f"Missing required configuration section: {section}")
        
        # Validate credentials
        creds = self.config.get("credentials", {})
        if "trello" in creds and not all(k in creds["trello"] for k in ["api_key", "token"]):
            logger.error("Incomplete Trello credentials")
            raise ValueError("Incomplete Trello credentials")
        
        # Validate at least one git platform is configured
        git_platforms = self.config.get("git_platforms", {})
        if not any(platform in git_platforms for platform in ["github", "gitlab", "bitbucket"]):
            logger.error("No Git platforms configured")
            raise ValueError("At least one Git platform must be configured")
    
    def get_config(self) -> Dict[str, Any]:
        """Return the complete configuration dictionary."""
        return self.config
    
    def get_git_platform_config(self, platform: str) -> Dict[str, Any]:
        """Get configuration for specific Git platform."""
        return self.config.get("git_platforms", {}).get(platform, {})
    
    def get_trello_config(self) -> Dict[str, Any]:
        """Get Trello configuration."""
        return self.config.get("credentials", {}).get("trello", {})


class BusinessPlanParser:
    """Parses business plan or prompt into structured tasks."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.categories = config.get("task_categories", {})
        self.openai_api_key = config.get("credentials", {}).get("openai", {}).get("api_key")
        
    def parse_file(self, file_path: str) -> Dict[str, List[Dict[str, Any]]]:
        """Parse a business plan file into structured tasks."""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            return self.parse_content(content)
        except FileNotFoundError:
            logger.error(f"Business plan file not found: {file_path}")
            raise
    
    def parse_content(self, content: str) -> Dict[str, List[Dict[str, Any]]]:
        """Parse raw content into structured tasks."""
        if not content.strip():
            logger.error("Empty business plan content provided")
            raise ValueError("Empty business plan content provided")
        
        # If OpenAI API key is provided, use AI to parse the plan
        if self.openai_api_key:
            return self._parse_with_ai(content)
        
        # Otherwise, use rule-based parsing
        return self._parse_with_rules(content)
    
    def _parse_with_ai(self, content: str) -> Dict[str, List[Dict[str, Any]]]:
        """Use OpenAI to parse the business plan into tasks."""
        try:
            openai.api_key = self.openai_api_key
            
            # Prepare prompt for OpenAI
            prompt = f"""
            Parse the following business plan into structured tasks.
            For each task, extract:
            1. A descriptive title
            2. A detailed description
            3. A difficulty level (Easy, Medium, Hard)
            4. A category from the following options: {', '.join(self.categories.keys())}
            5. Estimated time to complete (in hours)
            6. Dependencies (other tasks it depends on)
            
            Business Plan:
            {content}
            
            Format the output as a JSON object with categories as keys and lists of tasks as values.
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a project planning assistant that converts business plans into structured tasks."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )
            
            # Extract and parse JSON from the response
            try:
                import json
                result_text = response.choices[0].message.content
                # Find JSON block in response
                json_match = re.search(r'```json\n(.*?)\n```', result_text, re.DOTALL)
                if json_match:
                    result_text = json_match.group(1)
                return json.loads(result_text)
            except (json.JSONDecodeError, AttributeError) as e:
                logger.error(f"Failed to parse AI response as JSON: {e}")
                raise ValueError(f"AI returned invalid task structure: {e}")
        
        except Exception as e:
            logger.error(f"Error using OpenAI API: {e}")
            logger.info("Falling back to rule-based parsing")
            return self._parse_with_rules(content)
    
    def _parse_with_rules(self, content: str) -> Dict[str, List[Dict[str, Any]]]:
        """Use regex and rule-based parsing to extract tasks from content."""
        tasks_by_category = {category: [] for category in self.categories.keys()}
        default_category = next(iter(tasks_by_category.keys()))
        
        # Simple parsing: Extract sections with headers and bullet points
        sections = re.split(r'#{1,6}\s+', content)
        for i, section in enumerate(sections[1:], 1):  # Skip the first split which is text before any header
            lines = section.split('\n')
            if not lines:
                continue
                
            section_title = lines[0].strip()
            # Find matching category or use default
            category = next((cat for cat in self.categories if cat.lower() in section_title.lower()), default_category)
            
            # Extract bullet point items as tasks
            task_items = []
            current_task = None
            
            for line in lines[1:]:
                if re.match(r'^\s*[-*]\s+', line):  # Bullet point
                    if current_task:
                        task_items.append(current_task)
                    task_text = line.strip('- *\t ')
                    current_task = {
                        "title": task_text[:50] + ("..." if len(task_text) > 50 else ""),
                        "description": task_text,
                        "difficulty": "Medium",  # Default
                        "category": category,
                        "estimated_hours": 2,  # Default
                        "dependencies": []
                    }
                elif current_task and line.strip():
                    # Add this line to the description of the current task
                    current_task["description"] += "\n" + line.strip()
            
            # Add the last task if it exists
            if current_task:
                task_items.append(current_task)
            
            # Add all tasks from this section to the appropriate category
            for task in task_items:
                tasks_by_category[category].append(task)
        
        # Return tasks organized by category
        return {k: v for k, v in tasks_by_category.items() if v}  # Filter out empty categories


class TrelloManager:
    """Manages Trello board creation and card management."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        trello_config = config.get("credentials", {}).get("trello", {})
        self.api_key = trello_config.get("api_key")
        self.token = trello_config.get("token")
        self.client = None
        self.board = None
        self.lists = {}
        
        if self.api_key and self.token:
            self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize Trello client with API credentials."""
        try:
            self.client = TrelloClient(
                api_key=self.api_key,
                token=self.token
            )
            logger.info("Trello client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Trello client: {e}")
            raise
    
    def create_board(self, name: str, description: str = "") -> None:
        """Create a new Trello board for the project."""
        if not self.client:
            logger.error("Trello client not initialized")
            return
        
        try:
            self.board = self.client.add_board(
                name=name,
                desc=description
            )
            logger.info(f"Created Trello board: {name}")
            
            # Create standard lists
            list_names = ["Backlog", "To Do", "In Progress", "Review", "Done"]
            for list_name in list_names:
                trello_list = self.board.add_list(list_name)
                self.lists[list_name] = trello_list
                logger.info(f"Created list: {list_name}")
                
        except Exception as e:
            logger.error(f"Failed to create Trello board: {e}")
            raise
    
    def add_tasks_to_board(self, tasks_by_category: Dict[str, List[Dict[str, Any]]]) -> Dict[str, str]:
        """Add tasks to the Trello board and return mapping of task titles to card IDs."""
        if not self.board or not self.lists:
            logger.error("Trello board not initialized")
            return {}
        
        task_to_card_id = {}
        
        try:
            # Get backlog list
            backlog_list = self.lists.get("Backlog")
            if not backlog_list:
                logger.error("Backlog list not found")
                return {}
            
            # Add tasks as cards
            for category, tasks in tasks_by_category.items():
                for task in tasks:
                    card_name = task["title"]
                    card_desc = f"{task['description']}\n\n" \
                               f"**Category:** {category}\n" \
                               f"**Difficulty:** {task['difficulty']}\n" \
                               f"**Estimated Hours:** {task['estimated_hours']}\n"
                    
                    if task["dependencies"]:
                        card_desc += f"**Dependencies:** {', '.join(task['dependencies'])}\n"
                    
                    card = backlog_list.add_card(
                        name=card_name,
                        desc=card_desc
                    )
                    
                    # Add a label for the category if it exists
                    labels = self.board.get_labels()
                    category_label = next((l for l in labels if l.name.lower() == category.lower()), None)
                    if not category_label:
                        # Create a label if it doesn't exist
                        category_label = self.board.add_label(category, color="green")
                    
                    card.add_label(category_label)
                    
                    # Store mapping of task title to card ID
                    task_to_card_id[card_name] = card.id
                    logger.info(f"Added card: {card_name}")
            
            return task_to_card_id
                    
        except Exception as e:
            logger.error(f"Failed to add tasks to Trello board: {e}")
            raise


class GitPlatformManager:
    """Manages integration with Git platforms (GitHub, GitLab, Bitbucket)."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.git_platforms = config.get("git_platforms", {})
        self.repo_path = os.getcwd()  # Default to current directory
        self.repo = None
        
        # Try to initialize Git repo
        try:
            self.repo = Repo(self.repo_path)
            logger.info(f"Git repository found at {self.repo_path}")
        except Exception as e:
            logger.warning(f"Git repository not found: {e}")
    
    def set_repo_path(self, path: str) -> None:
        """Set the repository path and initialize Git repo."""
        if not os.path.exists(path):
            logger.error(f"Repository path does not exist: {path}")
            raise FileNotFoundError(f"Repository path does not exist: {path}")
        
        self.repo_path = path
        try:
            self.repo = Repo(self.repo_path)
            logger.info(f"Git repository found at {self.repo_path}")
        except Exception as e:
            logger.error(f"Failed to initialize Git repository: {e}")
            raise
    
    def create_issues(self, tasks_by_category: Dict[str, List[Dict[str, Any]]],
                      platform: str = "github", task_to_card_id: Dict[str, str] = None) -> Dict[str, str]:
        """Create issues on the specified Git platform."""
        platform_config = self.git_platforms.get(platform, {})
        if not platform_config:
            logger.error(f"Platform {platform} not configured")
            return {}
        
        auth_token = platform_config.get("token")
        if not auth_token:
            logger.error(f"Authentication token not provided for {platform}")
            return

