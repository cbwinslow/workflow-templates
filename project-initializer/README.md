# Curio Curation

## Project Overview

Curio Curation is a powerful project initialization and management tool designed to bridge the gap between business planning and technical execution. It transforms abstract business plans or project ideas into concrete, actionable tasks distributed across your preferred project management and development platforms.

### Purpose

In today's fast-paced development environment, teams often struggle to effectively translate business requirements into technical tasks. Curio Curation solves this critical problem by:

- Eliminating the manual, error-prone process of task creation and distribution
- Ensuring consistent project structure across teams and initiatives
- Creating traceable links between business requirements and technical implementation
- Reducing the time from project conception to active development

### Value Proposition

Curio Curation delivers significant benefits to development teams and organizations:

- **Time Savings**: Automates hours of manual task creation and platform setup
- **Improved Accuracy**: Ensures all business requirements are captured as technical tasks
- **Better Visibility**: Provides stakeholders clear views into project progress
- **Enhanced Consistency**: Standardizes project structures and workflows
- **Cross-Platform Integration**: Unifies task management across multiple tools

### Applications and Use Cases

Curio Curation excels in various scenarios:

- **New Product Development**: Quickly scaffold projects from concept to execution
- **Agile Sprints**: Transform sprint planning documents into tracked tasks
- **Project Handoffs**: Ensure consistent knowledge transfer between teams
- **Client Projects**: Convert client requirements into development roadmaps
- **Open Source Initiatives**: Structure community contributions effectively
- **Educational Settings**: Help students learn project management fundamentals

By automating the critical translation process between business planning and technical execution, Curio Curation allows teams to focus on what matters most: building great software.

## Features

- Parses business plans or project prompts into structured tasks
- Creates Trello boards and cards for task management
- Generates Git issues with appropriate labels and milestones
- Creates pull request/merge request templates
- Supports multiple Git platforms: GitHub, GitLab, Bitbucket
- AI-powered task parsing with OpenAI (optional)
- Configurable task categories and templates

## Prerequisites

- Python 3.8 or higher
- Trello account with API key and token (optional)
- GitHub/GitLab/Bitbucket account with access tokens
- OpenAI API key (optional, for enhanced parsing)

## Installation

1. Copy the `curio_curation` directory to your project
2. Install required dependencies:

```bash
pip install openai requests gitpython py-trello pyyaml
```

3. Configure `config.yml` with your API credentials and project settings

## Usage

### Command-Line Usage

```bash
python -m curio_curation.src.project_initializer --input business_plan.md --config config.yml
```

### Options

- `--input`: Path to business plan/prompt file (required)
- `--config`: Path to configuration file (required)
- `--parse-only`: Only parse the business plan, don't create tasks
- `--create-trello`: Create Trello board and cards
- `--platform`: Specify Git platform (github, gitlab, bitbucket)
- `--create-issues`: Create issues on Git platform
- `--create-pr-templates`: Create PR templates
- `--tasks-file`: Path to pre-parsed tasks JSON file
- `--generate-report`: Generate project initialization report

### GitHub Actions Workflow

You can also use the included GitHub Actions workflow to automate the process:

1. Place your business plan in a Markdown file
2. Configure the `config.yml` file with your credentials
3. Run the workflow via GitHub Actions UI, providing the path to your business plan and config file

## Configuration

The `config.yml` file contains settings for:

- API credentials for various services
- Project metadata and settings
- Task categorization rules
- Git platform-specific configurations
- Task template formats

See the sample configuration file for details.

## Examples

### Example Business Plan

```markdown
# Project: E-commerce Platform

## Frontend Development
- Create responsive homepage
- Implement product search functionality
- Design cart and checkout flow

## Backend Development
- Set up user authentication
- Build product catalog API
- Implement payment processing
```

### Example Command

```bash
python -m curio_curation.src.project_initializer --input ecommerce_plan.md --config config.yml --create-trello --platform github --create-issues
```

## License

MIT

