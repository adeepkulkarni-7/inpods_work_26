# Building the Inpods Curriculum Mapping System with Claude Code

## A Complete Walkthrough: From Prompts to Production

This document chronicles the development journey of the Inpods Curriculum Mapping System, demonstrating effective practices for using Claude Code to build complex applications.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Development Phases](#development-phases)
3. [Key Prompts and Approaches](#key-prompts-and-approaches)
4. [Best Practices Learned](#best-practices-learned)
5. [Technical Architecture](#technical-architecture)
6. [Commit History](#commit-history)

---

## Project Overview

### What We Built

A full-stack AI-powered system for mapping exam questions to curriculum dimensions:

| Component | Technology | Purpose |
|-----------|------------|---------|
| Backend API | Flask + Python | Azure OpenAI integration, file processing |
| Mode A App | HTML/JS | Map unmapped questions to curriculum |
| Mode B App | HTML/JS | Validate existing mappings |
| Mode C App | HTML/JS | Generate visual insights/charts |
| Chat Agent | HTML/JS | Conversational interface for all modes |
| Combined App | HTML/JS | All modes in one interface |

### Final Feature Set

- Multi-dimension mapping (Competency, Objective, Skill, Blooms, Complexity, NMC)
- Batch processing for efficiency
- AI-powered validation with suggestions
- Infographic-style chart generation
- Operation chaining (Map → Validate → Visualize)
- Drag-and-drop file upload
- One-click "Save & Generate Charts" workflow

---

## Development Phases

### Phase 1: Initial System (V2.0)

**User Request:**
> "Create a curriculum mapping system that uses Azure OpenAI to map exam questions to competencies"

**Approach:**
- Started with Flask backend for API
- Integrated Azure OpenAI for intelligent mapping
- Created basic web UI for file upload and results

**Key Files Created:**
- `backend_v2/app.py` - Main Flask server
- `backend_v2/audit_engine.py` - Mapping logic
- `frontend_v2/index.html` - Combined web interface

---

### Phase 2: Multi-Dimension Support (V2.1-V2.3)

**User Request:**
> "Add support for multiple dimensions - not just competency but also objectives, skills, Blooms taxonomy, and complexity"

**Approach:**
- Extended reference file parsing to detect multiple dimensions
- Added dimension checkboxes in UI
- Modified prompts to handle any dimension type
- Created per-dimension coverage analysis

**Key Changes:**
- Added `dimensions` array parameter to API endpoints
- Updated `extract_reference_metadata()` for all dimension types
- Created dimension-specific column naming (`mapped_competency`, `mapped_blooms`, etc.)

---

### Phase 3: Visualization Engine (V2.3)

**User Request:**
> "Add charts and visualizations - executive summary, coverage heatmaps, gap analysis"

**Approach:**
- Created `visualization_engine.py` with Matplotlib
- Designed infographic-style charts
- Added per-dimension chart generation
- Fixed empty/black chart issues with proper facecolor settings

**Charts Added:**
1. Executive Summary - Key metrics dashboard
2. Confidence Gauge - Overall confidence meter
3. Coverage Heatmap - Per-dimension coverage bars
4. Gap Analysis - Three-panel view of gaps/low/good coverage

---

### Phase 4: Standalone Apps (V2.4-V2.5)

**User Request:**
> "Split the monolithic frontend into separate single-page apps for each mode. Also create a conversational agent."

**Approach:**
1. Created shared components folder (`shared/`)
2. Extracted common CSS and utilities
3. Built three standalone apps:
   - `app_mapping/` - Mode A
   - `app_rating/` - Mode B
   - `app_insights/` - Mode C
4. Created conversational agent (`agent_v2/`)

**Planning Process:**
- Used plan mode to design folder structure
- Created detailed implementation plan
- Built shared components first
- Then individual apps
- Finally the agent

---

### Phase 5: Bug Fixes and Polish (Current)

**User Requests (Multiple):**
> "Charts showing 0% - fix it"
> "Rating validation should only suggest within same dimension"
> "Change 'Run Audit' to 'Map Questions'"
> "Add 'Select All Partial' button"
> "Fix black/empty visualization charts"
> "Make chart generation work in the agent"

**Fixes Applied:**
- Column naming: `mapped_id` → `mapped_{dimension}`
- Same-dimension validation constraints in prompts
- UI label improvements
- Chart loading states and error handling
- File path fallbacks for insights endpoint

---

## Key Prompts and Approaches

### Effective Prompt Patterns

#### 1. Feature Request with Context
```
User: "Add support for Blooms taxonomy and Complexity level dimensions"

Why it worked: Clear, specific feature request with named dimensions
```

#### 2. Bug Report with Symptoms
```
User: "Maps still give 0% anyway, do a pipeline documentation"

Why it worked: Described the symptom (0%), asked for debugging help
```

#### 3. Multi-Task Request
```
User: "Fix rating validation to suggest alternatives within SAME dimension only,
make justification required, change button label, add Select All Partial"

Why it worked: Listed all changes needed, Claude tracked and implemented each
```

#### 4. Exploration Request
```
User: "What if I just want them to run the client app on their machine"

Why it worked: Asked about use case, led to creating comprehensive setup docs
```

#### 5. Testing Request
```
User: "Test everything then we move to fix the charts issue"

Why it worked: Asked for verification before moving to next task
```

### Anti-Patterns to Avoid

| Don't | Do Instead |
|-------|------------|
| "Make it better" | "Add loading states to charts, show labels" |
| "Fix all bugs" | "Charts show 0% when they should show coverage" |
| "Build everything" | "Start with Mode A, then B, then C" |
| Long paragraphs | Bullet points or numbered lists |

---

## Best Practices Learned

### 1. Incremental Development

**What Worked:**
- Build core functionality first (mapping engine)
- Add features incrementally (multi-dimension, charts)
- Split monolith last (after core was stable)

**Example:**
```
Session 1: Basic mapping → Session 2: Add dimensions →
Session 3: Add charts → Session 4: Split apps → Session 5: Add agent
```

### 2. Backup Before Major Changes

**What We Did:**
- Created backup folders before each major version
- `backend_v2_v2.0_backup/`, `backend_v2_v2.1_backup/`, etc.
- Easy rollback if something broke

### 3. Test API Endpoints Directly

**Debugging Technique:**
```bash
# Test backend directly with curl
curl -s "http://localhost:5001/api/generate-insights" \
  -H "Content-Type: application/json" \
  -d '{"mapped_file": "test.csv"}' | python -c "import sys,json; print(json.dumps(json.load(sys.stdin), indent=2))"
```

This helped isolate whether bugs were in frontend or backend.

### 4. Use Git Effectively

**Commit Pattern:**
- Commit after each working feature
- Descriptive commit messages
- Push frequently to avoid losing work

```bash
# Good commit messages from this project:
"Fix agent chart rendering and file path handling"
"Add drag-and-drop file upload and improved greeting"
"Improve rating validation and UI labels"
```

### 5. Let Claude Run Background Tasks

**Effective Pattern:**
```
User: "Start the backend server"
[Claude runs in background]
User: "Now test the endpoints while that runs"
[Claude tests without waiting]
```

### 6. Context Continuity

**When Resuming Sessions:**
- Claude Code automatically summarizes previous context
- Reference specific files/functions when asking for changes
- Use "continue with [last task]" to resume

---

## Technical Architecture

### System Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                          │
├─────────────┬─────────────┬─────────────┬─────────────┬────────┤
│  Mode A     │   Mode B    │   Mode C    │   Agent     │Combined│
│  Mapping    │  Validation │  Insights   │   Chat      │  App   │
└──────┬──────┴──────┬──────┴──────┬──────┴──────┬──────┴────────┘
       │             │             │             │
       └─────────────┴─────────────┴─────────────┘
                           │
                    ┌──────▼──────┐
                    │  Flask API  │
                    │  Port 5001  │
                    └──────┬──────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
    ┌─────▼─────┐   ┌─────▼─────┐   ┌─────▼─────┐
    │  Audit    │   │   Viz     │   │  Library  │
    │  Engine   │   │  Engine   │   │  Manager  │
    └─────┬─────┘   └───────────┘   └───────────┘
          │
    ┌─────▼─────┐
    │  Azure    │
    │  OpenAI   │
    └───────────┘
```

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| Flask for backend | Simple, Python ecosystem, easy Azure integration |
| Vanilla JS frontend | No build step, easy to modify, fast iteration |
| Batch processing | Reduce API calls, better token efficiency |
| CSV intermediates | Enable operation chaining between modes |
| PNG charts | Universal compatibility, no JS chart libraries needed |

---

## Commit History

### Full Development Timeline

```
f79dc4f Add status indicator and improved help command
5bcd3ad Add drag-and-drop file upload and improved greeting
eb58a63 Improve agent UX with streamlined chart workflow
1e1385d Fix agent chart rendering and file path handling
405b531 Add UI improvements to combined frontend
ca7c6fe Fix visualization edge cases - prevent black/empty charts
013b5f1 Improve rating validation and UI labels
5e10f13 Fix launcher link to agent, add chart error handling
d059f5b Add setup instructions (credentials shared separately)
7ee5389 V2.5: Add standalone apps, conversational agent, documentation
fe859f5 Add per-dimension insights filtering to Mode C (V2.4)
db59899 Add comprehensive setup and usage documentation
6774be5 V2.3: Async task system, multi-dimension mapping, infographics
ec0e569 Add Blooms and Complexity metadata display
9417d9c Add Blooms taxonomy and Complexity level dimensions
08aba33 Add client setup instructions
7cf2c19 Fix reference metadata extraction and increase UI zoom
cbb3b90 Inpods Curriculum Mapping System V2 - Complete Release
39cf48f Checkpoint: Complete curriculum mapping system with AI agent
```

---

## Sample Conversation Patterns

### Pattern 1: Feature Development

```
USER: "Add Blooms taxonomy support"

CLAUDE: [Reads existing code to understand structure]
        [Identifies files to modify]
        [Updates reference parsing]
        [Adds UI checkboxes]
        [Modifies API endpoints]
        [Tests the changes]
        [Commits with descriptive message]
```

### Pattern 2: Bug Fixing

```
USER: "Charts show 0%"

CLAUDE: [Analyzes the symptom]
        [Traces data flow: upload → process → visualize]
        [Identifies root cause: column naming mismatch]
        [Fixes the mapping logic]
        [Tests with curl to verify API]
        [Updates frontend if needed]
        [Commits the fix]
```

### Pattern 3: Refactoring

```
USER: "Split into separate apps"

CLAUDE: [Creates plan with folder structure]
        [Extracts shared components]
        [Creates each app incrementally]
        [Tests each app independently]
        [Creates launcher page]
        [Documents the changes]
```

---

## Key Takeaways

### For Using Claude Code Effectively

1. **Be Specific** - "Add X to Y" is better than "improve the system"

2. **Provide Context** - Reference file names, function names, error messages

3. **Iterate** - Build one feature, test it, then add the next

4. **Trust but Verify** - Let Claude make changes, then test them

5. **Use Plan Mode** - For complex refactoring, planning first saves time

6. **Commit Often** - Small, focused commits make rollback easy

7. **Test APIs Directly** - Curl/fetch helps isolate frontend vs backend issues

8. **Keep Sessions Focused** - One major feature per session works well

### For This Specific System

- Azure OpenAI works well for classification/mapping tasks
- Batch processing (5 questions/batch) balances speed and quality
- Operation chaining (Map → Validate → Visualize) is powerful
- Conversational agent ties everything together nicely

---

## Files Reference

| File | Purpose | Lines |
|------|---------|-------|
| `backend_v2/app.py` | Main Flask server | ~1200 |
| `backend_v2/audit_engine.py` | Mapping/rating logic | ~600 |
| `backend_v2/visualization_engine.py` | Chart generation | ~550 |
| `agent_v2/agent.js` | Conversational agent | ~1200 |
| `agent_v2/api-client.js` | API wrapper | ~250 |
| `shared/common.css` | Shared styles | ~600 |

---

## Conclusion

This project demonstrates how Claude Code can be used to build a complete, production-ready application through iterative development. Key success factors:

1. Clear, specific prompts
2. Incremental feature development
3. Regular testing and verification
4. Good git hygiene
5. Trusting Claude to make changes while verifying results

Total development time: ~5-6 sessions
Final system: 5 frontend apps, 1 backend API, full documentation

---

*Document generated: 2026-02-03*
*Claude Code + Human collaboration*
