# Agent Workflow Skill (ALWAYS IMPLEMENTED)

**Last Updated:** 2026-01-16
**Status:** MANDATORY for all agents

---

## Purpose

This skill is a **mandatory protocol** for all AI agents working on this codebase. It prevents chain-reaction errors caused by incomplete task handoffs, missed file updates, and poor multi-agent coordination.

**This skill must be followed for EVERY task, not just complex ones.**

---

## Core Principles

### 1. ATOMIC TASK COMPLETION

A task is NOT complete until ALL of the following are verified:

- [ ] Code changes made
- [ ] Related documentation updated
- [ ] Tests pass (if applicable)
- [ ] Linting passes
- [ ] Changes committed and pushed
- [ ] Downstream agents can use the changes

### 2. NO ASSUMPTIONS

- Never assume another agent will "figure it out"
- Never assume documentation is optional
- Never assume the user will remember context

### 3. EXPLICIT HANDOFFS

- Every agent transition requires explicit handoff documentation
- Include: commit hash, file paths, expected commands, expected output

---

## Task Request Template

When receiving a task, immediately create this structure:

```markdown
## TASK: [Short description]

### SCOPE

- [ ] What files will be modified?
- [ ] What files will be created?
- [ ] What documentation needs updating?
- [ ] What other agents/systems are affected?

### AFFECTED SYSTEMS (Check ALL that apply)

- [ ] Backend code (`/backend/`)
- [ ] Frontend code (`/frontend/`)
- [ ] Scripts (`/scripts/`, `/backend/scripts/`)
- [ ] Knowledge base (`/backend/app/knowledge_base/`)
- [ ] API endpoints
- [ ] Database/migrations
- [ ] GCP infrastructure
- [ ] Documentation (`GCP_AGENT_SETUP.md`, `README.md`, etc.)
- [ ] CI/CD workflows (`.github/workflows/`)
- [ ] Dependencies (`requirements.txt`, `package.json`)

### VERIFICATION CHECKLIST

- [ ] Code compiles/imports without errors
- [ ] Linting passes (`ruff check`, `eslint`)
- [ ] Unit tests pass (`pytest`, `npm test`)
- [ ] Manual verification command: [specify]
- [ ] Changes committed with descriptive message
- [ ] Changes pushed to remote
- [ ] Documentation updated for affected systems

### AGENT HANDOFF (if applicable)

Target Agent: [GCP Agent / Frontend Agent / etc.]
Commit: [hash]
Required Actions:

1. `git pull origin main`
2. [Specific command]
3. [Expected output]
```

---

## Multi-Agent Coordination Protocol

### When Handing Off to Another Agent

**ALWAYS include:**

```markdown
## AGENT HANDOFF

### From: [This Agent Name/Type]

### To: [Target Agent Name/Type]

### Date: [YYYY-MM-DD]

### Summary

[1-2 sentences describing what was done]

### Commit Details

- Commit Hash: `[full hash]`
- Branch: `main`
- Files Changed:
  - `path/to/file1.py` - [brief description]
  - `path/to/file2.md` - [brief description]

### Required Actions for Target Agent

# Step 1: Pull latest

git pull origin main

# Step 2: [Specific action]

[command]

# Step 3: [Expected verification]

[command]

# Expected output: [description]

### Success Criteria

- [ ] [Criterion 1]
- [ ] [Criterion 2]
- [ ] [Criterion 3]

### If Something Goes Wrong

- Check: [common issue 1]
- Check: [common issue 2]
- Fallback: [recovery steps]
```

---

## Documentation Update Rules

### MANDATORY Documentation Updates

| When This Happens            | Update These Files                              |
| ---------------------------- | ----------------------------------------------- |
| New backend script created   | `GCP_AGENT_SETUP.md` Section 10                 |
| New API endpoint added       | `GCP_AGENT_SETUP.md` Section 6                  |
| New knowledge base file      | `GCP_AGENT_SETUP.md` Section 2                  |
| Dependency added             | `requirements.txt` AND `GCP_AGENT_SETUP.md` S1  |
| GCP quota/resource change    | `GCP_AGENT_SETUP.md` Section 4                  |
| Any file modified            | `GCP_AGENT_SETUP.md` Section 9 (Files Modified) |

### Documentation Format

Always use this format for tracking changes:

```markdown
## X. Section Name

### Subsection

**Command/Action:**

```bash
[exact command]
```

**Expected Output:**

- [bullet point 1]
- [bullet point 2]

**If it fails:**

- Check [thing 1]
- Try [alternative]
```

---

## Pre-Completion Checklist (MANDATORY)

Before marking ANY task complete, verify:

### Code Quality

- [ ] No syntax errors
- [ ] No import errors
- [ ] Linting passes: `ruff check backend/`
- [ ] Type hints present (where applicable)

### Testing

- [ ] Relevant tests pass: `pytest backend/tests/ -v`
- [ ] Manual smoke test performed
- [ ] Edge cases considered

### Documentation

- [ ] Code comments for complex logic
- [ ] Docstrings for public functions
- [ ] README/setup guide updated if needed
- [ ] `GCP_AGENT_SETUP.md` updated if GCP-related

### Version Control

- [ ] All changes staged: `git add -A`
- [ ] Descriptive commit message
- [ ] Pushed to remote: `git push origin main`
- [ ] Verified push succeeded (no conflicts)

### Cross-Agent Communication

- [ ] Handoff documentation written (if needed)
- [ ] Other agents notified of changes
- [ ] Dependencies documented

---

## Error Prevention Patterns

### Pattern 1: The "One More File" Check

After completing any change, ask:

> "What other files might need to be updated because of this change?"

Common pairs:

- Script created -> Update `GCP_AGENT_SETUP.md`
- Schema changed -> Update API endpoint
- Backend endpoint -> Update frontend service
- New dependency -> Update `requirements.txt` AND docs

### Pattern 2: The "Future Agent" Check

Before finishing, ask:

> "If another agent started fresh tomorrow, could they use my work without asking questions?"

If no -> Add more documentation.

### Pattern 3: The "Rollback" Check

Before committing, ask:

> "If this breaks something, can we easily identify what changed and why?"

If no -> Improve commit message and add comments.

---

## GCP Agent Specific Protocol

Since GCP Cloud Shell is **ephemeral**, special care is required:

### Session Start Checklist

```bash
# 1. Restore environment
git clone https://github.com/Bigdez55/Elson-TB2.git
cd Elson-TB2/backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 2. Verify setup
python -c "import app; print('Backend OK')"

# 3. Check GCP_AGENT_SETUP.md for current tasks
cat ../GCP_AGENT_SETUP.md | grep -A 50 "## 10. GCP Agent"
```

### Session End Checklist

- [ ] All work committed and pushed
- [ ] `GCP_AGENT_SETUP.md` updated with progress
- [ ] No uncommitted files: `git status` shows clean
- [ ] Handoff notes written for next session

---

## Communication Templates

### When Reporting Completion

```markdown
## TASK COMPLETE: [Task Name]

### What Was Done

- [Bullet 1]
- [Bullet 2]

### Files Changed

| File            | Change        |
| --------------- | ------------- |
| `path/file.py`  | [description] |

### Verification

- [x] Tests pass
- [x] Linting passes
- [x] Committed: `[hash]`
- [x] Pushed to `main`

### Next Steps (if any)

1. [Step 1]
2. [Step 2]
```

### When Reporting Blockers

```markdown
## BLOCKED: [Task Name]

### Issue

[Clear description of what's blocking]

### What Was Tried

1. [Attempt 1]
2. [Attempt 2]

### Error Message (if applicable)

[exact error]

### Suggested Resolution

- Option A: [description]
- Option B: [description]

### Impact

- [What cannot proceed until resolved]
```

---

## Enforcement

1. This skill is referenced at the start of every agent session
2. Completion checklists are mandatory, not optional
3. Multi-agent handoffs require explicit documentation
4. `GCP_AGENT_SETUP.md` is the source of truth for GCP work

---

## Quick Reference Card

```
BEFORE STARTING:
[ ] Read GCP_AGENT_SETUP.md for context
[ ] Identify all affected files/systems
[ ] Create task scope checklist

DURING WORK:
[ ] Follow "One More File" pattern
[ ] Update docs as you go (not at end)
[ ] Test each change before moving on

BEFORE MARKING COMPLETE:
[ ] Run linting: ruff check backend/
[ ] Run tests: pytest backend/tests/ -v
[ ] Commit with descriptive message
[ ] Push to remote
[ ] Update GCP_AGENT_SETUP.md if needed
[ ] Write handoff docs if needed

HANDOFF REQUIRED INFO:
- Commit hash
- Files changed
- Commands to run
- Expected output
- Troubleshooting tips
```

---

## Verification

To verify this skill is active:

```bash
# Check AGENT_WORKFLOW.md exists
ls -la AGENT_WORKFLOW.md

# Verify it contains key sections
grep -c "MANDATORY" AGENT_WORKFLOW.md  # Should be > 0
grep -c "HANDOFF" AGENT_WORKFLOW.md    # Should be > 0
grep -c "CHECKLIST" AGENT_WORKFLOW.md  # Should be > 0
```
