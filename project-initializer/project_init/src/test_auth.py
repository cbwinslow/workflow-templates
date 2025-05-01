#!/usr/bin/env python3
"""
Unit Tests for Authentication Module

This module contains tests for the auth.py module, including:
- Configuration loading
- Environment variable fallback
- Platform-specific credential validation
- Connection testing
"""

import os
import unittest
from unittest.mock import patch, MagicMock
import tempfile
import yaml
import json

# Import the module to test
from auth import CredentialManager


class TestCredentialManager(unittest.TestCase):
    """Test cases for the CredentialManager class."""

    def setUp(self):
        """Set up test environment."""
        # Create a temporary config file for testing
        self.config_file = tempfile.NamedTemporaryFile(delete=False, suffix='.yml')
        self.config_path = self.config_file.name
        
        # Sample configuration to write to the file
        self.test_config = {
            "credentials": {
                "trello": {
                    "api_key": "test_trello_key",
                    "token": "test_trello_token"
                },
                "github": {
                    "token": "test_github_token"
                },
                "gitlab": {
                    "token": "test_gitlab_token"
                },
                "bitbucket": {
                    "username": "test_bitbucket_user",
                    "app_password": "test_bitbucket_password"
                },
                "openai": {
                    "api_key": "test_openai_key"
                }
            },
            "git_platforms": {
                "github": {
                    "owner": "test_github_owner",
                    "repo": "test_github_repo",
                    "api_url": "https://api.github.com"
                },
                "gitlab": {
                    "owner": "test_gitlab_owner",
                    "repo": "test_gitlab_repo",
                    "api_url": "https://gitlab.com/api/v4"
                },
                "bitbucket": {
                    "owner": "test_bitbucket_owner",
                    "repo": "test_bitbucket_repo",
                    "api_url": "https://api.bitbucket.org/2.0"
                }
            }
        }
        
        # Write the configuration to the temporary file
        yaml.dump(self.test_config, self.config_file)
        self.config_file.close()
        
        # Save original environment variables to restore later
        self.original_env = os.environ.copy()
    
    def tearDown(self):
        """Clean up after tests."""
        # Delete the temporary config file
        os.unlink(self.config_path)
        
        # Restore original environment
        os.environ.clear()
        os.environ.update(self.original_env)
    
    def test_load_from_config(self):
        """Test loading credentials from config file."""
        creds = CredentialManager(self.config_path)
        
        # Check if credentials were loaded correctly
        self.assertEqual(creds.trello_creds.api_key, "test_trello_key")
        self.assertEqual(creds.trello_creds.token, "test_trello_token")
        self.assertEqual(creds.github_creds.token, "test_github_token")
        self.assertEqual(creds.gitlab_creds.token, "test_gitlab_token")
        self.assertEqual(creds.bitbucket_creds.username, "test_bitbucket_user")
        self.assertEqual(creds.bitbucket_creds.password, "test_bitbucket_password")
        self.assertEqual(creds.openai_creds.api_key, "test_openai_key")
        
        # Check validity flags
        self.assertTrue(creds.trello_creds.is_valid)
        self.assertTrue(creds.github_creds.is_valid)
        self.assertTrue(creds.gitlab_creds.is_valid)
        self.assertTrue(creds.bitbucket_creds.is_valid)
        self.assertTrue(creds.openai_creds.is_valid)
    
    def test_environment_variable_fallback(self):
        """Test falling back to environment variables when config is missing."""
        # Create an empty config file
        with open(self.config_path, 'w') as f:
            f.write("# Empty config")
        
        # Set environment variables
        os.environ["TRELLO_API_KEY"] = "env_trello_key"
        os.environ["TRELLO_TOKEN"] = "env_trello_token"
        os.environ["GITHUB_TOKEN"] = "env_github_token"
        os.environ["GITLAB_TOKEN"] = "env_gitlab_token"
        os.environ["BITBUCKET_USERNAME"] = "env_bitbucket_user"
        os.environ["BITBUCKET_APP_PASSWORD"] = "env_bitbucket_password"
        os.environ["OPENAI_API_KEY"] = "env_openai_key"
        
        # Load credentials manager
        creds = CredentialManager(self.config_path)
        
        # Check if environment variables were used
        self.assertEqual(creds.trello_creds.api_key, "env_trello_key")
        self.assertEqual(creds.trello_creds.token, "env_trello_token")
        self.assertEqual(creds.github_creds.token, "env_github_token")
        self.assertEqual(creds.gitlab_creds.token, "env_gitlab_token")
        self.assertEqual(creds.bitbucket_creds.username, "env_bitbucket_user")
        self.assertEqual(creds.bitbucket_creds.password, "env_bitbucket_password")
        self.assertEqual(creds.openai_creds.api_key, "env_openai_key")
        
        # Check validity flags
        self.assertTrue(creds.trello_creds.is_valid)
        self.assertTrue(creds.github_creds.is_valid)
        self.assertTrue(creds.gitlab_creds.is_valid)
        self.assertTrue(creds.bitbucket_creds.is_valid)
        self.assertTrue(creds.openai_creds.is_valid)
    
    def test_missing_credentials(self):
        """Test handling of missing credentials."""
        # Create a config with missing credentials
        with open(self.config_path, 'w') as f:
            f.write("credentials:\n  trello:\n    # Missing API key and token")
        
        # Load credentials manager
        creds = CredentialManager(self.config_path)
        
        # Check validity flags
        self.assertFalse(creds.trello_creds.is_valid)
        self.assertFalse(creds.github_creds.is_valid)
        self.assertFalse(creds.gitlab_creds.is_valid)
        self.assertFalse(creds.bitbucket_creds.is_valid)
        self.assertFalse(creds.openai_creds.is_valid)
        
        # Check error messages
        self.assertIsNotNone(creds.trello_creds.error_message)
        self.assertIsNotNone(creds.github_creds.error_message)
        self.assertIsNotNone(creds.gitlab_creds.error_message)
        self.assertIsNotNone(creds.bitbucket_creds.error_message)
        self.assertIsNotNone(creds.openai_creds.error_message)
    
    def test_refresh_credentials(self):
        """Test refreshing credentials after changes."""
        # Load credentials manager
        creds = CredentialManager(self.config_path)
        
        # Update config file with new values
        new_config = self.test_config.copy()
        new_config["credentials"]["trello"]["api_key"] = "updated_trello_key"
        
        with open(self.config_path, 'w') as f:
            yaml.dump(new_config, f)
        
        # Refresh credentials
        creds.refresh_credentials()
        
        # Check if credentials were updated
        self.assertEqual(creds.trello_creds.api_key, "updated_trello_key")
    
    @patch('requests.get')
    def test_trello_connection(self, mock_get):
        """Test Trello connection testing."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "username": "test_user",
            "fullName": "Test User"
        }
        mock_get.return_value = mock_response
        
        # Load credentials manager
        creds = CredentialManager(self.config_path)
        
        # Test the connection
        result = creds._test_trello_connection()
        
        # Check if the mock was called correctly
        mock_get.assert_called_once()
        self.assertTrue('key' in mock_get.call_args[1]['params'])
        self.assertTrue('token' in mock_get.call_args[1]['params'])
        
        # Check result
        self.assertTrue(result["success"])
        self.assertEqual(result["username"], "test_user")
        self.assertEqual(result["full_name"], "Test User")
    
    @patch('requests.get')
    def test_github_connection(self, mock_get):
        """Test GitHub connection testing."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "login": "test_github_user",
            "name": "Test GitHub User"
        }
        mock_get.return_value = mock_response
        
        # Load credentials manager
        creds = CredentialManager(self.config_path)
        
        # Test the connection
        result = creds._test_github_connection()
        
        # Check if the mock was called correctly
        mock_get.assert_called_once()
        self.assertTrue('Authorization' in mock_get.call_args[1]['headers'])
        
        # Check result
        self.assertTrue(result["success"])
        self.assertEqual(result["username"], "test_github_user")
        self.assertEqual(result["name"], "Test GitHub User")
    
    @patch('openai.Model.list')
    def test_openai_connection(self, mock_list):
        """Test OpenAI connection testing."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.data = [
            MagicMock(id="gpt-4"),
            MagicMock(id="gpt-3.5-turbo")
        ]
        mock_list.return_value = mock_response
        
        # Load credentials manager
        creds = CredentialManager(self.config_path)
        
        # Test the connection
        with patch('openai.api_key', new=None):  # Reset API key
            result = creds._test_openai_connection()
        
        # Check if the mock was called correctly
        mock_list.assert_called_once()
        
        # Check result
        self.assertTrue(result["success"])
        self.assertEqual(result["available_models"], ["gpt-4", "gpt-3.5-turbo"])
    
    @patch('requests.post')
    def test_trello_oauth_url(self, mock_post):
        """Test getting Trello OAuth URL."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.text = "oauth_token=test_oauth_token&oauth_token_secret=test_oauth_secret"
        mock_post.return_value = mock_response
        
        # Update config with OAuth secret
        new_config = self.test_config.copy()
        new_config["credentials"]["trello"]["oauth_secret"] = "test_oauth_secret"
        
        with open(self.config_path, 'w') as f:
            yaml.dump(new_config, f)
        
        # Load credentials manager
        creds = CredentialManager(self.config_path)
        
        # Get OAuth URL
        auth_url, token, secret = creds.get_trello_oauth_url()
        
        # Check if the mock was called correctly
        mock_post.assert_called_once()
        
        # Check result
        self.assertTrue("https://trello.com/1/OAuthAuthorizeToken" in auth_url)
        self.assertEqual(token, "test_oauth_token")
        self.assertEqual(secret, "test_oauth_secret")


if __name__ == '__main__':
    unittest.main()

