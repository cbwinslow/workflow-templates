# Project Initializer

This workflow template automates the process of converting a business plan or project prompt into actionable tasks across multiple platforms including Trello and Git-based services (GitHub, GitLab, Bitbucket).

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

1. Copy the `project-initializer` directory to your project
2. Install required dependencies:

```bash
pip install openai requests gitpython py-trello pyyaml
```

3. Configure `config.yml` with your API credentials and project settings

## Usage

### Command-Line Usage

```bash
python project_initializer.py --input business_plan.md --config config.yml
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
python project_initializer.py --input ecommerce_plan.md --config config.yml --create-trello --platform github --create-issues
```

## License

MIT

