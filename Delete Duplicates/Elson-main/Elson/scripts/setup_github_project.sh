#!/bin/bash
#
# Elson Wealth Trading Platform - GitHub Project Setup Script
#
# This script helps set up a GitHub project board for tracking beta issues and feedback
#

set -e

echo "================================================================================"
echo "      ELSON WEALTH TRADING PLATFORM - GITHUB PROJECT BOARD SETUP SCRIPT        "
echo "================================================================================"
echo ""

# Check for required dependencies
if ! command -v gh &> /dev/null; then
    echo "❌ Error: GitHub CLI (gh) is required but not installed."
    echo "    Please install GitHub CLI first: https://cli.github.com/"
    echo "    On Mac, you can use: brew install gh"
    exit 1
fi

# Check if user is authenticated with GitHub
if ! gh auth status &> /dev/null; then
    echo "You need to authenticate with GitHub to continue."
    echo "Please run 'gh auth login' and follow the instructions."
    exit 1
fi

# Get repository information
read -p "Enter GitHub repository owner/name (e.g., elson-wealth/trading-platform): " repo_name

if [ -z "$repo_name" ]; then
    echo "❌ Error: Repository name cannot be empty."
    exit 1
fi

# Confirm with the user
echo ""
echo "This script will create:"
echo "1. A project board named 'Beta Testing'"
echo "2. Issue templates for bug reports and feature requests"
echo "3. A discussion category for beta feedback"
echo "4. Labels for tracking beta issues"
echo ""
read -p "Do you want to proceed? (y/n): " confirm

if [[ ! $confirm =~ ^[Yy] ]]; then
    echo "Setup cancelled."
    exit 0
fi

# Create project board
echo ""
echo "Creating GitHub project board..."
PROJECT_JSON=$(gh api graphql -f query='
mutation {
  createProjectV2(
    input: {
      ownerId: "'"$(gh api repos/$repo_name | jq -r .owner.id)"'"
      title: "Beta Testing"
      repositoryIds: ["'"$(gh api repos/$repo_name | jq -r .id)"'"]
    }
  ) {
    projectV2 {
      id
      number
    }
  }
}
')

PROJECT_ID=$(echo $PROJECT_JSON | jq -r '.data.createProjectV2.projectV2.id')
PROJECT_NUMBER=$(echo $PROJECT_JSON | jq -r '.data.createProjectV2.projectV2.number')

if [ "$PROJECT_ID" == "null" ]; then
    echo "❌ Error: Failed to create project board."
    exit 1
fi

echo "✅ Project board created successfully (ID: $PROJECT_ID, Number: $PROJECT_NUMBER)"

# Create project fields
echo "Creating project fields..."

# Status field
gh api graphql -f query='
mutation {
  createProjectV2Field(
    input: {
      projectId: "'"$PROJECT_ID"'"
      dataType: SINGLE_SELECT
      name: "Status"
      options: ["Backlog", "To Do", "In Progress", "In Review", "Testing", "Done"]
    }
  ) {
    projectV2Field {
      id
    }
  }
}
'

# Priority field
gh api graphql -f query='
mutation {
  createProjectV2Field(
    input: {
      projectId: "'"$PROJECT_ID"'"
      dataType: SINGLE_SELECT
      name: "Priority"
      options: ["High", "Medium", "Low"]
    }
  ) {
    projectV2Field {
      id
    }
  }
}
'

# Severity field
gh api graphql -f query='
mutation {
  createProjectV2Field(
    input: {
      projectId: "'"$PROJECT_ID"'"
      dataType: SINGLE_SELECT
      name: "Severity"
      options: ["Critical", "Major", "Minor", "Trivial"]
    }
  ) {
    projectV2Field {
      id
    }
  }
}
'

echo "✅ Project fields created successfully"

# Create issue templates
echo "Creating issue templates..."

# Create .github/ISSUE_TEMPLATE directory if it doesn't exist
mkdir -p .github/ISSUE_TEMPLATE

# Create bug report template
cat > .github/ISSUE_TEMPLATE/bug_report.md << 'EOF'
---
name: Bug report
about: Report a bug found during beta testing
title: '[BUG] '
labels: bug, beta-testing
assignees: ''
---

**Bug Description**
A clear and concise description of what the bug is.

**To Reproduce**
Steps to reproduce the behavior:
1. Go to '...'
2. Click on '....'
3. Scroll down to '....'
4. See error

**Expected Behavior**
A clear and concise description of what you expected to happen.

**Screenshots**
If applicable, add screenshots to help explain your problem.

**Test Environment**
- Device: [e.g. MacBook Pro, iPhone 12]
- OS: [e.g. macOS 11.2, Windows 10]
- Browser: [e.g. Chrome 89, Safari 14]
- App Version: [e.g. 1.0.0-beta]

**Additional Context**
- Volatility level: [LOW/NORMAL/HIGH/EXTREME]
- Trading type: [e.g. Paper Trading, Educational]
- Other relevant details

**Impact**
How severe is this bug? [Critical/Major/Minor/Trivial]
EOF

# Create feature request template
cat > .github/ISSUE_TEMPLATE/feature_request.md << 'EOF'
---
name: Feature request
about: Suggest an improvement for the beta
title: '[FEATURE] '
labels: enhancement, beta-testing
assignees: ''
---

**Is your feature request related to a problem? Please describe.**
A clear and concise description of what the problem is. E.g., I'm always frustrated when [...]

**Describe the solution you'd like**
A clear and concise description of what you want to happen.

**Describe alternatives you've considered**
A clear and concise description of any alternative solutions or features you've considered.

**How would this feature improve your trading experience?**
Explain how this feature would benefit you as a user.

**Beta context**
- Is this feature missing from the beta but expected?
- Would this feature help achieve the beta test objectives?
- How critical is this feature for your testing?

**Additional context**
Add any other context or screenshots about the feature request here.
EOF

# Create feedback template
cat > .github/ISSUE_TEMPLATE/beta_feedback.md << 'EOF'
---
name: Beta Feedback
about: Provide general feedback about the beta
title: '[FEEDBACK] '
labels: feedback, beta-testing
assignees: ''
---

**Overall Experience**
Describe your overall experience with the beta so far.

**What's Working Well**
List aspects of the application that are working well.

**Areas for Improvement**
List aspects that could be improved.

**Suggestions**
Any specific suggestions for enhancing the application?

**Volatility Handling**
How well does the system handle market volatility? Any observations?

**Educational Content**
Feedback on the educational content (clarity, usefulness, etc.)

**Additional Comments**
Any other thoughts or feedback not covered above.
EOF

echo "✅ Issue templates created successfully"

# Create labels
echo "Creating labels..."

# Beta-specific labels
gh label create "beta-testing" --color "#0E8A16" --description "Issues related to beta testing" -R "$repo_name" || true
gh label create "beta-blocker" --color "#B60205" --description "Blocks beta testing progress" -R "$repo_name" || true
gh label create "volatility-related" --color "#6344ad" --description "Related to volatility handling" -R "$repo_name" || true
gh label create "user-interface" --color "#1D76DB" --description "Related to user interface" -R "$repo_name" || true
gh label create "educational-content" --color "#FBCA04" --description "Related to educational content" -R "$repo_name" || true
gh label create "model-performance" --color "#D93F0B" --description "Related to trading model performance" -R "$repo_name" || true
gh label create "family-accounts" --color "#5319E7" --description "Related to family/guardian accounts" -R "$repo_name" || true

echo "✅ Labels created successfully"

# Create discussion category
echo "Creating discussion category..."

gh api repos/$repo_name/discussions/categories -f 'name=Beta Feedback' -f 'description=Share your feedback and experience with the beta version' -f 'emoji=🧪' || echo "⚠️ Could not create discussion category. Make sure Discussions are enabled in the repository settings."

echo ""
echo "================================================================================"
echo "✅ GitHub Project Board setup completed!"
echo ""
echo "Project board URL: https://github.com/$repo_name/projects/$PROJECT_NUMBER"
echo ""
echo "Next steps:"
echo "1. Share the project URL with your team"
echo "2. Customize the project view and automation if needed"
echo "3. Update BETA_TESTING_PLAN.md to include project board information"
echo "================================================================================"