# Agent Workflow Skill (Universal)

**Version:** 1.1.0
**Last Updated:** 2026-01-18
**Purpose:** Mandatory protocol for AI agents to prevent chain-reaction errors

---

## Elson TB2 - Active Agent Configuration

### Current Agents

| Agent | Location | Environment | Primary Role |
|-------|----------|-------------|--------------|
| **GitHub Agent** | Local Mac | Claude Code CLI | Code, scripts, docs, git push |
| **GCP Agent** | `my-vm` (e2-medium, 20GB) | Claude Code on GCP | Training, deployment, git pull |

### GCP VM & GPU Inventory

| VM Name | Zone | Machine Type | GPU | VRAM | Disk | Status | Cost/hr |
|---------|------|--------------|-----|------|------|--------|---------|
| `elson-h100-spot` | us-central1-a | a3-highgpu-1g | 1x NVIDIA H100 | 80GB HBM3 | 200GB | TERMINATED | ~$2.50 (Spot) |
| `elson-dvora-training-l4` | us-east1-b | g2-standard-12 | 1x NVIDIA L4 | 24GB | 200GB | TERMINATED | ~$0.70 |
| `elson-dvora-training-l4-2` | us-west1-a | g2-standard-8 | 1x NVIDIA L4 | 24GB | 200GB | TERMINATED | ~$0.70 |
| `my-vm` | us-central1-a | e2-medium | None (CPU) | - | 20GB | RUNNING | ~$0.03 |

### VM Start Commands

```bash
# H100 (DoRA training - Spot, ~$2.50/hr)
gcloud compute instances start elson-h100-spot --zone=us-central1-a
gcloud compute ssh elson-h100-spot --zone=us-central1-a

# L4 #1 (us-east1-b, ~$0.70/hr)
gcloud compute instances start elson-dvora-training-l4 --zone=us-east1-b
gcloud compute ssh elson-dvora-training-l4 --zone=us-east1-b

# L4 #2 (us-west1-a, ~$0.70/hr)
gcloud compute instances start elson-dvora-training-l4-2 --zone=us-west1-a
gcloud compute ssh elson-dvora-training-l4-2 --zone=us-west1-a

# Claude Code workspace (CPU only, ~$0.03/hr)
gcloud compute ssh my-vm --zone=us-central1-a
```

### Trained Models in GCS

| Model | GCS Location | Status |
|-------|--------------|--------|
| Base (14B merged) | `gs://elson-33a95-elson-models/elson-finance-trading-14b-final/` | Ready |
| LoRA VM1 | `gs://elson-33a95-elson-models/wealth-lora-elson14b-vm1/` | Complete |
| LoRA VM2 | `gs://elson-33a95-elson-models/wealth-lora-elson14b-vm2/` | Complete |
| DoRA H100 | `gs://elson-33a95-elson-models/wealth-dora-elson14b-h100/` | Complete |

### Agent Responsibilities

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        ELSON TB2 AGENT WORKFLOW                          │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   GITHUB AGENT (Local)              GCP AGENT (Cloud)                    │
│   ━━━━━━━━━━━━━━━━━━━━              ━━━━━━━━━━━━━━━━━                    │
│   • Write/edit code                 • Pull latest code                   │
│   • Create scripts                  • Run training jobs                  │
│   • Update documentation            • Deploy models to GCS               │
│   • Manage training data            • Deploy vLLM server                 │
│   • Run local tests                 • Run inference tests                │
│   • Git commit & push               • Request GPU quotas                 │
│                                     • Manage VM lifecycle                │
│          │                                    │                          │
│          │         git push                   │                          │
│          ▼                                    │                          │
│   ┌──────────────┐                           │                          │
│   │    GitHub    │◄──────────────────────────┘                          │
│   │  Repository  │         git pull                                      │
│   └──────────────┘                                                       │
│          │                                                               │
│          │ Triggers CI/CD                                                │
│          ▼                                                               │
│   ┌──────────────┐      ┌──────────────┐      ┌──────────────┐          │
│   │  Cloud Run   │◄─────│   Cloud SQL  │      │  GCS Bucket  │          │
│   │  (Frontend/  │      │ (PostgreSQL) │      │  (Models)    │          │
│   │   Backend)   │      └──────────────┘      └──────────────┘          │
│   └──────────────┘                                   ▲                   │
│                                                      │                   │
│                                              Model Upload                │
│                                                      │                   │
│                                            ┌─────────┴────────┐         │
│                                            │   Training VMs   │         │
│                                            │ H100/L4 (Spot)   │         │
│                                            └──────────────────┘         │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Key Files for Agent Coordination

| File | Purpose | Owner |
|------|---------|-------|
| `GCP_AGENT_SETUP.md` | GCP environment setup, training instructions | GCP Agent reads |
| `MODEL_DEPLOYMENT_STATUS.md` | Deployment status tracking | Both agents |
| `ACTION_PLAN.md` | Current tasks and priorities | GitHub Agent writes |
| `AGENT_WORKFLOW.md` | This file - coordination protocol | Both agents |

### GCP Agent Session Start Protocol

```bash
# EVERY GCP Agent session must start with:
cd ~/Elson-TB2 && git pull origin main
cat GCP_AGENT_SETUP.md | head -100  # Check current status
cat ACTION_PLAN.md | grep -A 20 "Immediate Action"  # See priorities
```

### GitHub Agent Handoff Template

When pushing changes that require GCP Agent action:

```markdown
## HANDOFF TO GCP AGENT

**Commit:** [hash]
**Date:** YYYY-MM-DD

### What Changed
- [File 1]: [description]
- [File 2]: [description]

### GCP Agent Actions Required
1. `cd ~/Elson-TB2 && git pull origin main`
2. [Specific command to run]
3. [Expected output/verification]

### Blocking Issues (if any)
- [ ] L4 GPU quota needed
- [ ] Training data location: `backend/training_data/consolidated_training_data.json`
```

### Current Handoff Status (2026-01-18)

**From:** GitHub Agent
**To:** GCP Agent
**Commit:** `9f798d5`

**What Was Done:**
- Created 6 new scripts (deployment, benchmark, data processing)
- Consolidated 950 Q&A training pairs
- Categorized 830+ URLs to 18 domains
- Updated README and created ACTION_PLAN.md

**GCP Agent Actions Required:**
```bash
# 1. Pull latest
cd ~/Elson-TB2 && git pull origin main

# 2. Check L4 GPU quota status
# If not requested: https://console.cloud.google.com/iam-admin/quotas?project=elson-33a95

# 3. Deploy vLLM (once quota approved)
./scripts/deploy-vllm-dora.sh l4 dora
# OR for cost savings:
./scripts/deploy-vllm-dora.sh spot qdora

# 4. Run benchmark (once vLLM is up)
python scripts/run_evaluation_benchmark.py --api-url http://EXTERNAL_IP:8000

# 5. Optional: Retrain with expanded data (950 pairs vs 408)
# Training data: backend/training_data/consolidated_training_data.json
```

---

## Purpose

This skill is a **mandatory protocol** for all AI agents working on any codebase. It prevents chain-reaction errors caused by incomplete task handoffs, missed file updates, and poor multi-agent coordination.

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
- [ ] Scripts (`/scripts/`)
- [ ] Configuration files
- [ ] API endpoints
- [ ] Database/migrations
- [ ] Infrastructure (cloud, containers)
- [ ] Documentation (README, guides)
- [ ] CI/CD workflows
- [ ] Dependencies (requirements.txt, package.json)

### VERIFICATION CHECKLIST
- [ ] Code compiles/imports without errors
- [ ] Linting passes
- [ ] Unit tests pass
- [ ] Manual verification command: [specify]
- [ ] Changes committed with descriptive message
- [ ] Changes pushed to remote
- [ ] Documentation updated for affected systems

### AGENT HANDOFF (if applicable)
Target Agent: [Agent Name/Type]
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
```bash
# Step 1: Pull latest
git pull origin main

# Step 2: [Specific action]
[command]

# Step 3: [Expected verification]
[command]
# Expected output: [description]
```

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

| When This Happens | Update These Files |
|-------------------|-------------------|
| New script created | Setup guide / README |
| New API endpoint added | API reference docs |
| New config file | Configuration guide |
| Dependency added | requirements.txt AND setup docs |
| Infrastructure change | Deployment/setup guide |
| Any significant file modified | Changelog or session notes |

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
- [ ] Linting passes
- [ ] Type hints present (where applicable)

### Testing
- [ ] Relevant tests pass
- [ ] Manual smoke test performed
- [ ] Edge cases considered

### Documentation
- [ ] Code comments for complex logic
- [ ] Docstrings for public functions
- [ ] README/setup guide updated if needed
- [ ] Project-specific docs updated

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
- Script created → Update setup guide
- Schema changed → Update API endpoint
- Backend endpoint → Update frontend service
- New dependency → Update requirements AND docs

### Pattern 2: The "Future Agent" Check
Before finishing, ask:
> "If another agent started fresh tomorrow, could they use my work without asking questions?"

If no → Add more documentation.

### Pattern 3: The "Rollback" Check
Before committing, ask:
> "If this breaks something, can we easily identify what changed and why?"

If no → Improve commit message and add comments.

---

## Ephemeral Environment Protocol

For environments that don't persist (cloud shells, containers, VMs):

### Session Start Checklist
```bash
# 1. Restore environment
git clone [REPO_URL]
cd [PROJECT_DIR]
[setup commands]

# 2. Verify setup
[verification command]

# 3. Check setup guide for current tasks
cat [SETUP_GUIDE] | grep -A 50 "## Current Tasks"
```

### Session End Checklist
- [ ] All work committed and pushed
- [ ] Setup guide updated with progress
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
| File | Change |
|------|--------|
| `path/file.py` | [description] |

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
```
[exact error]
```

### Suggested Resolution
- Option A: [description]
- Option B: [description]

### Impact
- [What cannot proceed until resolved]
```

---

## Quick Reference Card

### Before Starting Any Task
1. Read existing documentation
2. Create task scope outline
3. Identify affected systems

### During Task Execution
1. Make changes incrementally
2. Test after each significant change
3. Document as you go

### After Completing Task
1. Run full verification checklist
2. Update all affected documentation
3. Write handoff notes if applicable
4. Commit with descriptive message
5. Push and verify

### When Stuck
1. Document what you tried
2. Note exact error messages
3. Suggest possible solutions
4. Request specific help

---

## Verification

To verify this skill is implemented in a project:

```bash
# Check AGENT_WORKFLOW.md exists
ls -la AGENT_WORKFLOW.md

# Verify it contains key sections
grep -c "MANDATORY" AGENT_WORKFLOW.md  # Should be > 0
grep -c "HANDOFF" AGENT_WORKFLOW.md    # Should be > 0
grep -c "CHECKLIST" AGENT_WORKFLOW.md  # Should be > 0
```

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.1.0 | 2026-01-18 | Added Elson TB2 specific agent configuration, workflow diagram, handoff status |
| 1.0.0 | 2026-01-16 | Initial release - extracted from Elson Financial AI project |
