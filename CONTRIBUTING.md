# Contributing to Agent Collaboration Platform

Thank you for your interest in contributing! This document provides guidelines and instructions.

## Code of Conduct

- Be respectful and inclusive
- Focus on constructive feedback
- Welcome diverse perspectives

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/yourusername/agent-collaboration-platform.git`
3. Create a feature branch: `git checkout -b feature/your-feature-name`
4. Set up your development environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # or: venv\Scripts\activate on Windows
   pip install -r requirements.txt
   ```

## Development Guidelines

### Code Style

We follow PEP 8. Use tools to help:

```bash
# Format with Black
pip install black
black src/

# Lint with Pylint
pip install pylint
pylint src/
```

### Commits

- Use clear, descriptive commit messages
- Reference issues when applicable: `Fixes #123`
- Keep commits focused and atomic

Example:
```
Fix: Correct timeout handling in analyst service

- Add retry logic for Groq API calls
- Improve error messages
- Add timeout configuration option

Fixes #42
```

### Pull Requests

1. Ensure tests pass: `pytest`
2. Update documentation for significant changes
3. Provide a clear description of what changed and why
4. Reference related issues

PR Template:
```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## How to Test
Steps to verify the changes work

## Checklist
- [ ] Code follows style guidelines
- [ ] Tests pass
- [ ] Documentation updated
- [ ] No new warnings generated
```

## Areas for Contribution

### High Priority

1. **Persistent Storage**
   - Migrate MCP Registry to PostgreSQL
   - Add migration scripts

2. **Testing**
   - Unit tests for all services
   - Integration test suite
   - Performance benchmarks

3. **Documentation**
   - API documentation improvements
   - Tutorial walkthroughs
   - Deployment guides

### Medium Priority

1. **Features**
   - Additional LLM providers (OpenAI, Anthropic, etc.)
   - Advanced routing policies
   - Message filtering and search

2. **Operations**
   - Kubernetes manifests
   - Helm charts
   - Monitoring dashboards
   - Health check endpoints

### Low Priority

1. **Polish**
   - Frontend UI improvements
   - Error message enhancements
   - Code cleanup refactoring

## Testing

### Running Tests

```bash
pytest
```

### Writing Tests

Create test files in `tests/` directory:

```python
import pytest
from src.services.analyst_service import analyze_document

def test_analyze_document():
    text = "Sample document"
    result = analyze_document(text)
    assert "summary" in result
    assert "kpis" in result
```

## Documentation

### Updating Docs

- Update README.md for user-facing changes
- Update ARCHITECTURE.md for system design changes
- Add docstrings to new functions:

```python
def process_message(message):
    """
    Process an A2A message.
    
    Args:
        message (dict): Message with keys: sender, receiver, type, payload, conv_id
        
    Returns:
        dict: Processing result with status and optional error
        
    Raises:
        ValueError: If message format is invalid
    """
    pass
```

## Reporting Issues

### Bug Reports

Include:
- Description of the bug
- Steps to reproduce
- Expected behavior
- Actual behavior
- Environment (OS, Python version, etc.)
- Error messages or logs

### Feature Requests

Include:
- Use case description
- Proposed solution (if any)
- Alternative approaches considered

## Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes
- CONTRIBUTORS.md file

## Questions?

- Open an issue with label `question`
- Check existing issues for similar topics
- Review the documentation

Thank you for contributing!
