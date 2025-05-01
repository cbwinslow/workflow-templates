import os
import sys
import unittest
import tempfile
import shutil
import yaml
from pathlib import Path

class TestProjectSetup(unittest.TestCase):
    def setUp(self):
        # Main project files location
        self.project_root = Path(__file__).parent.parent
        self.config_dir = self.project_root / 'config'
        self.docs_dir = self.project_root / 'docs'
        self.src_dir = self.project_root / 'src'
        self.platforms_dir = self.src_dir / 'platforms'
        
        # Create a test project directory for ACME Sample Inc.
        self.test_dir = Path(tempfile.mkdtemp(prefix="acme_sample_inc_"))
        self.test_project_dir = self.test_dir / "acme_sample_inc"
        self.test_project_dir.mkdir(exist_ok=True)
    
    def tearDown(self):
        # Clean up the test directory
        if hasattr(self, 'test_dir') and self.test_dir.exists():
            shutil.rmtree(self.test_dir)
    
    def test_directory_structure(self):
        """Test that all required directories exist in the main project"""
        self.assertTrue(self.project_root.exists(), "Project root directory doesn't exist")
        self.assertTrue(self.config_dir.exists(), "Config directory doesn't exist")
        self.assertTrue(self.docs_dir.exists(), "Docs directory doesn't exist")
        self.assertTrue(self.src_dir.exists(), "Source directory doesn't exist")
        self.assertTrue(self.platforms_dir.exists(), "Platforms directory doesn't exist")
    
    def test_required_files(self):
        """Test that all required files exist in the main project"""
        required_files = [
            (self.config_dir / 'config.yml', "Configuration file"),
            (self.docs_dir / 'SAMPLE_BUSINESS_PLAN.md', "Sample business plan"),
            (self.src_dir / 'project_initializer.py', "Main project initializer"),
            (self.src_dir / 'auth.py', "Authentication module"),
            (self.platforms_dir / '__init__.py', "Platforms init file"),
            (self.platforms_dir / 'github_client.py', "GitHub client"),
            (self.platforms_dir / 'trello_client.py', "Trello client")
        ]
        
        for file_path, description in required_files:
            self.assertTrue(file_path.exists(), f"{description} doesn't exist at {file_path}")
    
    def test_config_structure(self):
        """Test configuration file structure"""
        config_path = self.config_dir / 'config.yml'
        try:
            with open(config_path) as f:
                config = yaml.safe_load(f)
            
            required_sections = [
                'credentials',          # API credentials
                'project_settings',     # Project configuration
                'task_categories',      # Task categorization
                'git_platforms',        # Git platform settings
                'task_templates'        # Templates for issues and PRs
            ]
            for section in required_sections:
                self.assertIn(section, config, f"Missing required section '{section}' in config.yml")
                
            # Test credentials structure
            credentials = config['credentials']
            required_platforms = ['trello', 'github']
            for platform in required_platforms:
                self.assertIn(platform, credentials, f"Missing {platform} credentials")
                
            # Test project settings
            settings = config['project_settings']
            required_settings = ['name', 'description', 'board']
            for setting in required_settings:
                self.assertIn(setting, settings, f"Missing project setting '{setting}'")
                
            # Test task categories
            self.assertTrue(len(config['task_categories']) > 0, "No task categories defined")
            
            # Test git platforms
            self.assertIn('github', config['git_platforms'], "GitHub platform configuration missing")
            
            # Test task templates
            templates = config['task_templates']
            required_templates = ['issue_body', 'pr_body']
            for template in required_templates:
                self.assertIn(template, templates, f"Missing template '{template}'")
                
        except Exception as e:
            self.fail(f"Failed to load or validate config.yml: {str(e)}")
    
    def test_business_plan_structure(self):
        """Test business plan template structure"""
        plan_path = self.docs_dir / 'SAMPLE_BUSINESS_PLAN.md'
        try:
            with open(plan_path) as f:
                content = f.read()
            
            required_sections = ['# Project', '## Overview', '## Milestones']
            for section in required_sections:
                self.assertIn(section, content, f"Missing required section '{section}' in business plan")
        except Exception as e:
            self.fail(f"Failed to load or validate SAMPLE_BUSINESS_PLAN.md: {str(e)}")
    
    def test_platform_integrations(self):
        """Test platform integration modules"""
        # Test GitHub client
        from platforms.github_client import GitHubIntegration
        self.assertTrue(hasattr(GitHubIntegration, 'create_repository'), "GitHub client missing create_repository method")
        self.assertTrue(hasattr(GitHubIntegration, 'create_issue'), "GitHub client missing create_issue method")
        
        # Test Trello client
        from platforms.trello_client import TrelloIntegration
        self.assertTrue(hasattr(TrelloIntegration, 'create_board'), "Trello client missing create_board method")
        self.assertTrue(hasattr(TrelloIntegration, 'create_card'), "Trello client missing create_card method")
    
    def test_create_sample_project(self):
        """Test creating a sample ACME Inc. project"""
        # Create sample business plan for ACME Sample Inc.
        acme_plan_file = self.test_project_dir / "ACME_BUSINESS_PLAN.md"
        acme_plan_content = """# ACME Sample Inc. Project Plan

## Overview
ACME Sample Inc. is developing a new e-commerce platform for widgets

## Project Goals
1. Build responsive frontend
2. Develop scalable backend
3. Implement secure payment processing

## Milestones
1. Initial Planning
   - [ ] Requirement gathering
   - [ ] Technical architecture design
   - [ ] Infrastructure setup

2. Development Phase
   - [ ] Frontend implementation
   - [ ] Backend API development
   - [ ] Database design

3. Testing & Deployment
   - [ ] Unit testing
   - [ ] Integration testing
   - [ ] Production deployment

## Timeline
- Phase 1: 2 weeks
- Phase 2: 6 weeks
- Phase 3: 2 weeks
"""
        with open(acme_plan_file, "w") as f:
            f.write(acme_plan_content)
        
        # Test the plan file was created correctly
        self.assertTrue(acme_plan_file.exists(), "ACME business plan file wasn't created")
        with open(acme_plan_file) as f:
            content = f.read()
            self.assertIn("ACME Sample Inc.", content, "Content not properly written to file")

        # Here we would normally invoke the project_initializer with this file,
        # but we'll just verify setup for now
        print(f"\nTest project setup at: {self.test_project_dir}")

if __name__ == '__main__':
    unittest.main()

