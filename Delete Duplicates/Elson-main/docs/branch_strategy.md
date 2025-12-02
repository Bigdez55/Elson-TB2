---
title: "Branch Strategy"
confidentiality: "PROPRIETARY & CONFIDENTIAL"
---

<\!-- PROPRIETARY NOTICE
This document contains proprietary information of Elson Wealth Management Inc.
Unauthorized use, reproduction, or distribution is strictly prohibited.
Copyright © 2025 Elson Wealth Management Inc. All rights reserved.
-->

# Branch Strategy for Elson Wealth Trading Platform

This document outlines the branching strategy for the Elson Wealth Trading Platform repository. Following these guidelines ensures consistent and reliable development and release processes.

## Branch Structure

The repository uses the following branch structure:

```
main            # Production-ready code
├── beta-*      # Beta release branches (beta-v1.0.0, etc.)
├── develop     # Integration branch for active development
│   ├── feature-* # Feature branches
│   ├── bugfix-*  # Bug fix branches
│   └── hotfix-*  # Critical hotfix branches
```

## Branch Types

### Main Branch

- **Name**: `main`
- **Purpose**: Contains production-ready code
- **Protection**: Protected from direct pushes
- **Merge Requirements**: Only through pull requests with required reviews
- **CI/CD**: Triggers deployment to production environment

### Beta Branches

- **Name Pattern**: `beta-v{major}.{minor}.{patch}`
- **Purpose**: Contains code for beta releases
- **Created From**: `develop`
- **Merges To**: `main` (when beta is complete)
- **Protection**: Protected from direct pushes
- **Merge Requirements**: Pull requests with required reviews
- **CI/CD**: Triggers deployment to beta environment

### Develop Branch

- **Name**: `develop`
- **Purpose**: Integration branch for ongoing development
- **Created From**: `main`
- **Merges To**: `beta-*` branches
- **Protection**: Protected from direct pushes
- **Merge Requirements**: Pull requests with at least one review
- **CI/CD**: Triggers deployment to development environment

### Feature Branches

- **Name Pattern**: `feature-{feature-name}`
- **Purpose**: Implements new features
- **Created From**: `develop`
- **Merges To**: `develop`
- **Protection**: None
- **Lifecycle**: Deleted after merging

### Bugfix Branches

- **Name Pattern**: `bugfix-{issue-number}-{brief-description}`
- **Purpose**: Fixes non-critical bugs
- **Created From**: `develop`
- **Merges To**: `develop`
- **Protection**: None
- **Lifecycle**: Deleted after merging

### Hotfix Branches

- **Name Pattern**: `hotfix-{issue-number}-{brief-description}`
- **Purpose**: Fixes critical bugs in production
- **Created From**: `main`
- **Merges To**: `main` and `develop`
- **Protection**: None
- **Lifecycle**: Deleted after merging
- **CI/CD**: Special fast-track deployment process

## Branch Protection Rules

### Main Branch Protection

- Require pull request reviews before merging
- Require at least 2 approvals
- Dismiss stale pull request approvals when new commits are pushed
- Require status checks to pass before merging:
  - CI pipeline must pass
  - Security scan must pass
  - Code coverage must meet threshold
- Require linear history
- Do not allow force pushes
- Include administrators in these restrictions

### Beta Branch Protection

- Require pull request reviews before merging
- Require at least 1 approval
- Require status checks to pass before merging:
  - CI pipeline must pass
  - Security scan must pass
- Do not allow force pushes
- Include administrators in these restrictions

### Develop Branch Protection

- Require pull request reviews before merging
- Require at least 1 approval
- Require status checks to pass before merging:
  - CI pipeline must pass
- Allow force pushes for administrators only

## Workflow Guidelines

### Starting a New Feature

```bash
# Update develop branch
git checkout develop
git pull origin develop

# Create a new feature branch
git checkout -b feature-new-feature-name

# Make changes, commit, and push
git add .
git commit -m "Description of changes"
git push origin feature-new-feature-name

# Create pull request to develop branch via GitHub UI
```

### Creating a Beta Release

```bash
# Update develop branch
git checkout develop
git pull origin develop

# Create a beta branch
git checkout -b beta-v1.0.0

# Make any beta-specific changes
git add .
git commit -m "Prepare for beta v1.0.0 release"
git push origin beta-v1.0.0

# Create GitHub release via UI with beta tag
```

### Hotfix Process

```bash
# Update main branch
git checkout main
git pull origin main

# Create hotfix branch
git checkout -b hotfix-123-critical-issue

# Make fixes, commit, and push
git add .
git commit -m "Fix critical issue #123"
git push origin hotfix-123-critical-issue

# Create pull request to main branch via GitHub UI
# After merging to main, also merge to develop:

git checkout develop
git pull origin develop
git merge origin/hotfix-123-critical-issue
git push origin develop
```

## Beta Testing Process

During the beta phase, the following workflow applies:

1. Features are developed in feature branches and merged into `develop`
2. When ready for beta testing, create a `beta-v{version}` branch from `develop`
3. Apply beta-specific configurations and documentation to the beta branch
4. Create a GitHub Release from the beta branch with a pre-release tag
5. Deploy to beta environment
6. Collect feedback from beta testers
7. Fix issues in bugfix branches targeting the beta branch
8. Once beta is validated, merge the beta branch to `main`

## Release Versioning

The Elson Wealth Trading Platform follows semantic versioning:

- **Major version**: Incremented for backward-incompatible changes
- **Minor version**: Incremented for backward-compatible feature additions
- **Patch version**: Incremented for backward-compatible bug fixes
- **Pre-release suffix**: `-beta.1`, `-beta.2`, etc. for beta releases

Example: `v1.0.0-beta.1`

## Pull Request Guidelines

All pull requests should:

1. Reference related issues
2. Include comprehensive description of changes
3. Pass all automated checks
4. Include tests for new functionality
5. Update documentation as needed
6. Be reviewed by at least one team member
7. Include screenshots for UI changes

## Commit Message Guidelines

Commit messages should follow the conventional commits format:

```
type(scope): subject

body
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Example**:
```
feat(trading): add circuit breaker for high volatility

Implements an enhanced circuit breaker that responds to four volatility levels:
- LOW: Normal trading allowed
- NORMAL: Normal trading allowed
- HIGH: Restricted trading with position sizing at 0.10
- EXTREME: Highly restricted trading with position sizing at 0.03

Fixes #123
```

## Branch Cleanup

To keep the repository clean:

- Delete feature and bugfix branches after merging
- Archive beta branches after merging to main
- Regularly prune remote tracking branches that have been deleted on the remote