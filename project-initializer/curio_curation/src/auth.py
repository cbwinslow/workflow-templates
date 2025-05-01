#!/usr/bin/env python3
"""
Authentication and Credential Management

This module provides a unified interface for handling authentication across multiple platforms:
- Trello (OAuth2)
- GitHub, GitLab, BitBucket (PAT)
- OpenAI API

It loads credentials from config.yml with environment variable fallback
and provides secure credential management with appropriate error handling.
"""

import os
import logging
import time
from typing import Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass
import yaml
import requests
from dotenv import load_dotenv

# Configure logging
logger = logging.getLogger("auth_manager")

# Load environment variables from .env file if it exists
load_dotenv()


@dataclass
class PlatformCredentials:
    """Base class for platform-specific credentials."""
    platform_name: str
    is_valid: bool = False
    error_message: Optional[str] = None


@dataclass
class TrelloCredentials(PlatformCredentials):
    """Trello API credentials."""
    api_key: str = ""
    token: str = ""
    # OAuth2 specific fields
    oauth_secret: Optional[str] = None
    oauth_token: Optional[str] = None
    oauth_token_secret: Optional[str] = None
    oauth_verifier: Optional[str] = None


@dataclass
class GitPlatformCredentials(PlatformCredentials):
    """Git platform (GitHub, GitLab, BitBucket) credentials."""
    token: str = ""
    username: Optional[str] = None
    password: Optional[str] = None  # Only used for Bitbucket app passwords
    api_url: str = ""


@dataclass
class OpenAICredentials(PlatformCredentials):
    """OpenAI API credentials."""
    api_key: str = ""
    organization_id: Optional[str] = None


class CredentialManager:
    """Unified credential management system for all platforms."""
    
    def __init__(self, config_path: str = "config.yml"):
        """Initialize the credential manager.
        
        Args:
            config_path: Path to the configuration YAML file
        """
        self.config_path = config_path
        self.config = {}
        self.trello_creds = TrelloCredentials(platform_name="trello")
        self.github_creds = GitPlatformCredentials(platform_name="github")
        self.gitlab_creds = GitPlatformCredentials(platform_name="gitlab")
        self.bitbucket_creds = GitPlatformCredentials(platform_name="bitbucket")
        self.openai_creds = OpenAICredentials(platform_name="openai")
        
        # Load credentials from config file and environment variables
        self._load_credentials()
    
    def _load_credentials(self) -> None:
        """Load credentials from config file with environment variable fallback."""
        try:
            # Load config file if it exists
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as file:
                    self.config = yaml.safe_load(file) or {}
                logger.info(f"Loaded configuration from {self.config_path}")
            else:
                logger.warning(f"Config file {self.config_path} not found. Using environment variables only.")
                self.config = {}
            
            # Extract credentials section
            creds_config = self.config.get("credentials", {})
            
            # Load Trello credentials
            self._load_trello_credentials(creds_config.get("trello", {}))
            
            # Load Git platform credentials
            git_platforms = self.config.get("git_platforms", {})
            self._load_github_credentials(creds_config.get("github", {}), git_platforms.get("github", {}))
            self._load_gitlab_credentials(creds_config.get("gitlab", {}), git_platforms.get("gitlab", {}))
            self._load_bitbucket_credentials(creds_config.get("bitbucket", {}), git_platforms.get("bitbucket", {}))
            
            # Load OpenAI credentials
            self._load_openai_credentials(creds_config.get("openai", {}))
            
        except Exception as e:
            logger.error(f"Error loading credentials: {e}")
            raise
    
    def _load_trello_credentials(self, trello_config: Dict[str, Any]) -> None:
        """Load Trello credentials from config file with environment variable fallback.
        
        Args:
            trello_config: Trello configuration dict from YAML
        """
        try:
            # Try config file first
            api_key = trello_config.get("api_key", "")
            token = trello_config.get("token", "")
            oauth_secret = trello_config.get("oauth_secret", None)
            
            # Fall back to environment variables
            api_key = api_key or os.environ.get("TRELLO_API_KEY", "")
            token = token or os.environ.get("TRELLO_TOKEN", "")
            oauth_secret = oauth_secret or os.environ.get("TRELLO_OAUTH_SECRET", None)
            
            # OAuth2 tokens may be in environment
            oauth_token = os.environ.get("TRELLO_OAUTH_TOKEN", None)
            oauth_token_secret = os.environ.get("TRELLO_OAUTH_TOKEN_SECRET", None)
            oauth_verifier = os.environ.get("TRELLO_OAUTH_VERIFIER", None)
            
            # Update credentials
            self.trello_creds = TrelloCredentials(
                platform_name="trello",
                api_key=api_key,
                token=token,
                oauth_secret=oauth_secret,
                oauth_token=oauth_token,
                oauth_token_secret=oauth_token_secret,
                oauth_verifier=oauth_verifier,
                is_valid=bool(api_key and (token or oauth_token))
            )
            
            if not self.trello_creds.is_valid:
                self.trello_creds.error_message = "Missing required Trello credentials"
                logger.warning("Trello credentials incomplete. Some features may not work.")
            
        except Exception as e:
            self.trello_creds.is_valid = False
            self.trello_creds.error_message = str(e)
            logger.error(f"Error loading Trello credentials: {e}")
    
    def _load_github_credentials(self, github_config: Dict[str, Any], platform_config: Dict[str, Any]) -> None:
        """Load GitHub credentials with environment variable fallback.
        
        Args:
            github_config: GitHub credentials from config
            platform_config: GitHub platform settings from config
        """
        try:
            # Try config file first
            token = github_config.get("token", "")
            api_url = platform_config.get("api_url", "https://api.github.com")
            
            # Fall back to environment variables
            token = token or os.environ.get("GITHUB_TOKEN", "")
            api_url = api_url or os.environ.get("GITHUB_API_URL", "https://api.github.com")
            
            # Update credentials
            self.github_creds = GitPlatformCredentials(
                platform_name="github",
                token=token,
                api_url=api_url,
                username=platform_config.get("owner", os.environ.get("GITHUB_USERNAME", "")),
                is_valid=bool(token)
            )
            
            if not self.github_creds.is_valid:
                self.github_creds.error_message = "Missing GitHub token"
                logger.warning("GitHub credentials incomplete. GitHub features may not work.")
            
        except Exception as e:
            self.github_creds.is_valid = False
            self.github_creds.error_message = str(e)
            logger.error(f"Error loading GitHub credentials: {e}")
    
    def _load_gitlab_credentials(self, gitlab_config: Dict[str, Any], platform_config: Dict[str, Any]) -> None:
        """Load GitLab credentials with environment variable fallback.
        
        Args:
            gitlab_config: GitLab credentials from config
            platform_config: GitLab platform settings from config
        """
        try:
            # Try config file first
            token = gitlab_config.get("token", "")
            api_url = platform_config.get("api_url", "https://gitlab.com/api/v4")
            
            # Fall back to environment variables
            token = token or os.environ.get("GITLAB_TOKEN", "")
            api_url = api_url or os.environ.get("GITLAB_API_URL", "https://gitlab.com/api/v4")
            
            # Update credentials
            self.gitlab_creds = GitPlatformCredentials(
                platform_name="gitlab",
                token=token,
                api_url=api_url,
                username=platform_config.get("owner", os.environ.get("GITLAB_USERNAME", "")),
                is_valid=bool(token)
            )
            
            if not self.gitlab_creds.is_valid:
                self.gitlab_creds.error_message = "Missing GitLab token"
                logger.warning("GitLab credentials incomplete. GitLab features may not work.")
            
        except Exception as e:
            self.gitlab_creds.is_valid = False
            self.gitlab_creds.error_message = str(e)
            logger.error(f"Error loading GitLab credentials: {e}")
    
    def _load_bitbucket_credentials(self, bitbucket_config: Dict[str, Any], platform_config: Dict[str, Any]) -> None:
        """Load Bitbucket credentials with environment variable fallback.
        
        Args:
            bitbucket_config: Bitbucket credentials from config
            platform_config: Bitbucket platform settings from config
        """
        try:
            # Try config file first
            username = bitbucket_config.get("username", "")
            app_password = bitbucket_config.get("app_password", "")
            api_url = platform_config.get("api_url", "https://api.bitbucket.org/2.0")
            
            # Fall back to environment variables
            username = username or os.environ.get("BITBUCKET_USERNAME", "")
            app_password = app_password or os.environ.get("BITBUCKET_APP_PASSWORD", "")
            api_url = api_url or os.environ.get("BITBUCKET_API_URL", "https://api.bitbucket.org/2.0")
            
            # Update credentials
            self.bitbucket_creds = GitPlatformCredentials(
                platform_name="bitbucket",
                username=username,
                password=app_password,
                api_url=api_url,
                is_valid=bool(username and app_password)
            )
            
            if not self.bitbucket_creds.is_valid:
                self.bitbucket_creds.error_message = "Missing Bitbucket username or app password"
                logger.warning("Bitbucket credentials incomplete. Bitbucket features may not work.")
            
        except Exception as e:
            self.bitbucket_creds.is_valid = False
            self.bitbucket_creds.error_message = str(e)
            logger.error(f"Error loading Bitbucket credentials: {e}")
    
    def _load_openai_credentials(self, openai_config: Dict[str, Any]) -> None:
        """Load OpenAI credentials with environment variable fallback.
        
        Args:
            openai_config: OpenAI configuration dict from YAML
        """
        try:
            # Try config file first
            api_key = openai_config.get("api_key", "")
            org_id = openai_config.get("organization_id", None)
            
            # Fall back to environment variables
            api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
            org_id = org_id or os.environ.get("OPENAI_ORGANIZATION_ID", None)
            
            # Update credentials
            self.openai_creds = OpenAICredentials(
                platform_name="openai",
                api_key=api_key,
                organization_id=org_id,
                is_valid=bool(api_key)
            )
            
            if not self.openai_creds.is_valid:
                self.openai_creds.error_message = "Missing OpenAI API key"
                logger.warning("OpenAI credentials incomplete. AI features may not work.")
            
        except Exception as e:
            self.openai_creds.is_valid = False
            self.openai_creds.error_message = str(e)
            logger.error(f"Error loading OpenAI credentials: {e}")
    
    def get_trello_oauth_url(self) -> Tuple[str, str, str]:
        """Get Trello OAuth authorization URL.
        
        Returns:
            Tuple of (auth_url, oauth_token, oauth_token_secret)
        
        Raises:
            ValueError: If Trello API key or OAuth secret is missing
        """
        if not self.trello_creds.api_key:
            raise ValueError("Trello API key is required for OAuth")
        
        if not self.trello_creds.oauth_secret:
            raise ValueError("Trello OAuth secret is required for OAuth flow")
        
        # Request a request token
        url = f"https://trello.com/1/OAuthGetRequestToken"
        oauth_data = {
            "oauth_consumer_key": self.trello_creds.api_key,
            "oauth_signature_method": "HMAC-SHA1",
            "oauth_timestamp": str(int(time.time())),
            "oauth_nonce": str(int(time.time())),
            "oauth_version": "1.0",
            "oauth_callback": "oob"  # Out of band authentication
        }
        
        try:
            response = requests.post(url, data=oauth_data)
            response.raise_for_status()
            
            # Parse response
            response_parts = response.text.split("&")
            oauth_token = response_parts[0].split("=")[1]
            oauth_token_secret = response_parts[1].split("=")[1]
            
            # Build authorization URL
            auth_url = (
                f"https://trello.com/1/OAuthAuthorizeToken?"
                f"oauth_token={oauth_token}&"
                f"expiration=never&"
                f"scope=read,write&"
                f"name=Project+Initializer"
            )
            
            return auth_url, oauth_token, oauth_token_secret
            
        except Exception as e:
            logger.error(f"Error getting Trello OAuth URL: {e}")
            raise
    
    def complete_trello_oauth(self, oauth_token: str, oauth_token_secret: str, verifier: str) -> str:
        """Complete Trello OAuth flow and get access token.
        
        Args:
            oauth_token: OAuth request token
            oauth_token_secret: OAuth request token secret
            verifier: OAuth verifier code
            
        Returns:
            Trello access token
            
        Raises:
            ValueError: If OAuth parameters are missing or invalid
        """
        if not all([self.trello_creds.api_key, oauth_token, oauth_token_secret, verifier]):
            raise ValueError("Missing required OAuth parameters")
        
        # Request access token
        url = f"https://trello.com/1/OAuthGetAccessToken"
        oauth_data = {
            "oauth_consumer_key": self.trello_creds.api_key,
            "oauth_token": oauth_token,
            "oauth_signature_method": "HMAC-SHA1",
            "oauth_timestamp": str(int(time.time())),
            "oauth_nonce": str(int(time.time())),
            "oauth_version": "1.0",
            "oauth_verifier": verifier
        }
        
        try:
            response = requests.post(url, data=oauth_data)
            response.raise_for_status()
            
            # Parse response
            response_parts = response.text.split("&")
            access_token = response_parts[0].split("=")[1]
            
            # Update credentials
            self.trello_creds.token = access_token
            self.trello_creds.is_valid = True
            
            logger.info("Trello OAuth flow completed successfully")
            return access_token
            
        except Exception as e:
            logger.error(f"Error completing Trello OAuth flow: {e}")
            raise
    
    def configure_openai(self) -> None:
        """Configure the OpenAI client with current credentials.
        
        This function sets the OpenAI API key and organization ID in the openai module.
        
        Examples:
            >>> credential_manager = CredentialManager("config.yml")
            >>> credential_manager.configure_openai()
            # Now the openai module is configured and ready to use
            >>> response = openai.ChatCompletion.create(model="gpt-4", messages=[...])
        """
        try:
            import openai
            
            if not self.openai_creds.is_valid:
                logger.warning("OpenAI credentials invalid, cannot configure")
                return
                
            openai.api_key = self.openai_creds.api_key
            if self.openai_creds.organization_id:
                openai.organization = self.openai_creds.organization_id
                
            logger.info("OpenAI API configured successfully")
            
        except ImportError:
            logger.error("OpenAI module not installed")
        except Exception as e:
            logger.error(f"Error configuring OpenAI: {e}")
    
    def refresh_credentials(self) -> None:
        """Reload credentials from config file and environment variables.
        
        This is useful when credentials have changed in the environment or config file.
        
        Examples:
            >>> credential_manager = CredentialManager("config.yml")
            >>> # After updating config.yml or environment variables
            >>> credential_manager.refresh_credentials()
        """
        old_config = self.config.copy()
        old_trello = self.trello_creds
        old_github = self.github_creds
        old_gitlab = self.gitlab_creds
        old_bitbucket = self.bitbucket_creds
        old_openai = self.openai_creds
        
        try:
            self._load_credentials()
            logger.info("Credentials refreshed successfully")
        except Exception as e:
            # Restore previous credentials on error
            self.config = old_config
            self.trello_creds = old_trello
            self.github_creds = old_github
            self.gitlab_creds = old_gitlab
            self.bitbucket_creds = old_bitbucket
            self.openai_creds = old_openai
            logger.error(f"Error refreshing credentials: {e}")
            raise
    
    def test_credentials(self, platform: str = "all") -> Dict[str, Dict[str, Union[bool, str]]]:
        """Test connectivity with platform credentials.
        
        Args:
            platform: Platform to test ("all", "trello", "github", "gitlab", "bitbucket", "openai")
            
        Returns:
            Dictionary with test results for each platform
            
        Examples:
            >>> credential_manager = CredentialManager("config.yml")
            >>> results = credential_manager.test_credentials()
            >>> print(results["github"]["success"])  # True or False
            >>> 
            >>> # Test only GitHub credentials
            >>> github_results = credential_manager.test_credentials("github")
        """
        results = {}
        
        if platform.lower() in ["all", "trello"]:
            results["trello"] = self._test_trello_connection()
            
        if platform.lower() in ["all", "github"]:
            results["github"] = self._test_github_connection()
            
        if platform.lower() in ["all", "gitlab"]:
            results["gitlab"] = self._test_gitlab_connection()
            
        if platform.lower() in ["all", "bitbucket"]:
            results["bitbucket"] = self._test_bitbucket_connection()
            
        if platform.lower() in ["all", "openai"]:
            results["openai"] = self._test_openai_connection()
        
        return results
    
    def _test_trello_connection(self) -> Dict[str, Union[bool, str]]:
        """Test Trello API connectivity."""
        result = {"success": False, "message": ""}
        
        if not self.trello_creds.is_valid:
            result["message"] = "Trello credentials invalid or missing"
            return result
            
        try:
            # Test API connection
            url = f"https://api.trello.com/1/members/me"
            params = {
                "key": self.trello_creds.api_key,
                "token": self.trello_creds.token
            }
            response = requests.get(url, params=params)
            response.raise_for_status()
            
            # If we get here, connection was successful
            result["success"] = True
            result["message"] = "Trello connection successful"
            
            # Add user info
            user_data = response.json()
            result["username"] = user_data.get("username", "")
            result["full_name"] = user_data.get("fullName", "")
            
        except Exception as e:
            result["message"] = f"Trello connection failed: {str(e)}"
            logger.error(f"Trello connection test failed: {e}")
            
        return result
    
    def _test_github_connection(self) -> Dict[str, Union[bool, str]]:
        """Test GitHub API connectivity."""
        result = {"success": False, "message": ""}
        
        if not self.github_creds.is_valid:
            result["message"] = "GitHub credentials invalid or missing"
            return result
            
        try:
            # Test API connection
            headers = {
                "Authorization": f"token {self.github_creds.token}",
                "Accept": "application/vnd.github.v3+json"
            }
            response = requests.get(f"{self.github_creds.api_url}/user", headers=headers)
            response.raise_for_status()
            
            # If we get here, connection was successful
            result["success"] = True
            result["message"] = "GitHub connection successful"
            
            # Add user info
            user_data = response.json()
            result["username"] = user_data.get("login", "")
            result["name"] = user_data.get("name", "")
            
        except Exception as e:
            result["message"] = f"GitHub connection failed: {str(e)}"
            logger.error(f"GitHub connection test failed: {e}")
            
        return result
    
    def _test_gitlab_connection(self) -> Dict[str, Union[bool, str]]:
        """Test GitLab API connectivity."""
        result = {"success": False, "message": ""}
        
        if not self.gitlab_creds.is_valid:
            result["message"] = "GitLab credentials invalid or missing"
            return result
            
        try:
            # Test API connection
            headers = {"PRIVATE-TOKEN": self.gitlab_creds.token}
            response = requests.get(f"{self.gitlab_creds.api_url}/user", headers=headers)
            response.raise_for_status()
            
            # If we get here, connection was successful
            result["success"] = True
            result["message"] = "GitLab connection successful"
            
            # Add user info
            user_data = response.json()
            result["username"] = user_data.get("username", "")
            result["name"] = user_data.get("name", "")
            
        except Exception as e:
            result["message"] = f"GitLab connection failed: {str(e)}"
            logger.error(f"GitLab connection test failed: {e}")
            
        return result
    
    def _test_bitbucket_connection(self) -> Dict[str, Union[bool, str]]:
        """Test Bitbucket API connectivity."""
        result = {"success": False, "message": ""}
        
        if not self.bitbucket_creds.is_valid:
            result["message"] = "Bitbucket credentials invalid or missing"
            return result
            
        try:
            # Test API connection with basic auth
            auth = (self.bitbucket_creds.username, self.bitbucket_creds.password)
            response = requests.get(f"{self.bitbucket_creds.api_url}/user", auth=auth)
            response.raise_for_status()
            
            # If we get here, connection was successful
            result["success"] = True
            result["message"] = "Bitbucket connection successful"
            
            # Add user info
            user_data = response.json()
            result["username"] = user_data.get("username", "")
            result["display_name"] = user_data.get("display_name", "")
            
        except Exception as e:
            result["message"] = f"Bitbucket connection failed: {str(e)}"
            logger.error(f"Bitbucket connection test failed: {e}")
            
        return result
    
    def _test_openai_connection(self) -> Dict[str, Union[bool, str]]:
        """Test OpenAI API connectivity."""
        result = {"success": False, "message": ""}
        
        if not self.openai_creds.is_valid:
            result["message"] = "OpenAI credentials invalid or missing"
            return result
            
        try:
            # Import OpenAI module
            import openai
            
            # Configure OpenAI
            openai.api_key = self.openai_creds.api_key
            if self.openai_creds.organization_id:
                openai.organization = self.openai_creds.organization_id
                
            # Test API connection with a simple models list request
            response = openai.Model.list()
            
            # If we get here, connection was successful
            result["success"] = True
            result["message"] = "OpenAI connection successful"
            
            # Add model info
            if hasattr(response, "data") and response.data:
                result["available_models"] = [model.id for model in response.data[:5]]
            
        except ImportError:
            result["message"] = "OpenAI module not installed"
            logger.error("OpenAI module not installed")
        except Exception as e:
            result["message"] = f"OpenAI connection failed: {str(e)}"
            logger.error(f"OpenAI connection test failed: {e}")
            
        return result


# Usage examples
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Example 1: Load credentials from config.yml
    creds = CredentialManager("config.yml")
    
    # Example 2: Test credentials
    results = creds.test_credentials()
    for platform, result in results.items():
        print(f"{platform}: {'✅' if result['success'] else '❌'} - {result['message']}")
    
    # Example 3: Configure OpenAI
    creds.configure_openai()
    
    # Example 4: Start Trello OAuth flow (if needed)
    if not creds.trello_creds.is_valid and creds.trello_creds.api_key:
        try:
            auth_url, token, secret = creds.get_trello_oauth_url()
            print(f"Open this URL in your browser to authorize: {auth_url}")
            print(f"Store these values securely:")
            print(f"OAuth Token: {token}")
            print(f"OAuth Secret: {secret}")
            
            verifier = input("Enter the verification code from Trello: ")
            access_token = creds.complete_trello_oauth(token, secret, verifier)
            print(f"Access Token: {access_token}")
            print("Trello authentication complete!")
        except Exception as e:
            print(f"Error in OAuth process: {e}")
