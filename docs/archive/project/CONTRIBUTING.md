# Contributing to Elson Wealth Trading Platform

Thank you for your interest in contributing to the Elson Wealth Trading Platform! This document provides guidelines and instructions for beta testers and contributors.

## Beta Testing Guidelines

### Reporting Issues

When filing issues, please follow these steps:

1. **Check for duplicates** - Search the existing issues to avoid creating duplicates
2. **Use the issue templates** - We provide templates for bug reports and feature requests
3. **Provide detailed information** - Include your environment, steps to reproduce, actual vs. expected behavior
4. **Include logs** - If applicable, include relevant logs or screenshots
5. **Tag appropriately** - Use labels like `bug`, `enhancement`, `high-volatility`, etc.

### Bug Report Format

Please include the following information in your bug reports:

- **Environment**: OS, browser version, screen size/resolution
- **Steps to Reproduce**: Numbered steps to reproduce the issue
- **Expected Behavior**: What you expected to happen
- **Actual Behavior**: What actually happened
- **Volatility Context**: Was this during high/extreme volatility?
- **Screenshots/Videos**: If applicable
- **Logs**: Console errors or backend logs if available

## Pull Request Process

If you're contributing code changes, please follow these guidelines:

1. **Create a branch** from the `beta` branch with a descriptive name
2. **Make your changes** following our code style
3. **Add tests** for new functionality
4. **Ensure all tests pass** locally before submitting
5. **Update documentation** if necessary
6. **Create a pull request** with a clear description of the changes

## Code Style and Standards

### Python

- Follow PEP 8 style guide
- Use type hints
- Document functions and classes with docstrings
- Maximum line length: 100 characters
- Use f-strings for string formatting when possible

### TypeScript/JavaScript

- Follow the ESLint configuration in the project
- Use TypeScript interfaces for data structures
- Use functional components with hooks for React components
- Use async/await rather than Promises directly

### General Guidelines

- Write unit tests for new functionality
- Keep functions and methods focused on a single responsibility
- Use meaningful variable and function names
- Comment complex logic, but prefer self-explanatory code

## Beta Testing Focus Areas

During the beta testing phase, we're particularly interested in feedback on:

1. **Performance during high volatility** - How does the system perform when markets are volatile?
2. **Circuit breaker functionality** - Does the circuit breaker engage appropriately?
3. **Latency and response times** - Are there any performance bottlenecks?
4. **User interface for volatility indicators** - Is the UI clear and helpful?
5. **Error handling** - Are errors handled gracefully?

## Communication Channels

- **GitHub Issues**: For bug reports and feature requests
- **Discord Channel**: For real-time discussion and support
- **Beta Tester Email List**: For announcements and updates

## Beta Confidentiality

As a beta tester, you agree to:

1. Keep all access credentials secure
2. Not share screenshots or details of the platform publicly without permission
3. Not use the platform for actual trading during the beta phase

## Acknowledgments

We appreciate all contributions to the Elson Wealth Trading Platform. Beta testers will be acknowledged in our release notes and documentation.

Thank you for helping make the Elson Wealth Trading Platform better!