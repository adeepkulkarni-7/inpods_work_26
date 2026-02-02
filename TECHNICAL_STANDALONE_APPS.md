# Technical Documentation: Standalone Mode Apps

## Overview

This document describes the architecture and implementation of the standalone single-page applications (SPAs) that were extracted from the combined `frontend_v2/index.html` application.

**Version:** 2.4
**Date:** February 2026
**Backend Compatibility:** Unchanged - all apps use the same backend API on port 5001

---

## Architecture

### Design Goals

1. **Single-purpose apps** - Each app handles one specific workflow without mode switching
2. **Code reuse** - Common functionality extracted to shared modules
3. **Maintainability** - Easier to update individual modes without affecting others
4. **Parallel development** - Teams can work on different apps independently

### Folder Structure

```
inpods-audit_cc/
├── index.html                    # Launcher page
├── TECHNICAL_STANDALONE_APPS.md  # This document
│
├── shared/                       # Shared components
│   ├── common.css               # Global styles (500+ lines)
│   ├── task-manager.js          # Async task tracking (~130 lines)
│   └── utils.js                 # API constants & utilities (~35 lines)
│
├── app_mapping/                  # Mode A: Question Mapping
│   ├── index.html
│   ├── styles.css
│   └── app.js
│
├── app_rating/                   # Mode B: Mapping Validation
│   ├── index.html
│   ├── styles.css
│   └── app.js
│
├── app_insights/                 # Mode C: Insights & Visualization
│   ├── index.html
│   ├── styles.css
│   └── app.js
│
├── frontend_v2/                  # Original combined app (unchanged)
└── backend_v2/                   # Backend API (unchanged)
```

---

## Shared Components (`shared/`)

### common.css

Global stylesheet containing all shared UI components.

**Sections:**
| Section | Lines | Description |
|---------|-------|-------------|
| Reset & Base | 1-30 | CSS reset, body, container styles |
| Typography | 31-55 | Headers, subtitles, version badge |
| Cards | 56-75 | Card containers, section titles |
| Forms | 76-130 | Inputs, selects, labels, form groups |
| Buttons | 131-180 | Primary, secondary, success, danger, small variants |
| Status Messages | 181-210 | Success/error notification styling |
| Tables | 211-280 | Recommendations table, headers, cells |
| Question Display | 281-320 | Question text, full text boxes |
| Badges | 321-370 | Confidence badges, rating badges |
| Dimension Checkboxes | 371-450 | Multi-select dimension picker |
| Loading Spinner | 451-480 | Animated spinner, loading state |
| Token Usage | 481-540 | API usage display bar |
| Modal | 541-580 | Modal overlay, modal box |
| Task Panel | 581-700 | Fixed bottom-right task tracker |

**CSS Variables Used:**
- Primary color: `#00a8cc`
- Success color: `#10b981`
- Warning color: `#f59e0b`
- Error color: `#ef4444`
- Text primary: `#1e293b`
- Text secondary: `#64748b`

---

### task-manager.js

Manages asynchronous task tracking with UI notifications.

**Classes:**

```javascript
TaskState = {
    PENDING: 'pending',
    RUNNING: 'running',
    COMPLETED: 'completed',
    FAILED: 'failed'
}

class TaskManager {
    constructor()           // Initialize task map and counter
    create(type, desc)      // Create new task, returns taskId
    run(taskId, asyncFn)    // Execute async function with progress tracking
    notifyComplete(task)    // Show browser notification + status bar
    getTypeLabel(type)      // Get human-readable task type label
    getActive()             // Get array of running tasks
    getAll()                // Get all tasks sorted by start time
    render()                // Update task panel UI
    formatDur(ms)           // Format duration as "Xs" or "Xm Ys"
}
```

**Task Types:**
- `mapping` - Question Mapping (Mode A)
- `rating` - Mapping Validation (Mode B)
- `insights` - Insights Generation (Mode C)

**Global Functions:**
- `toggleTaskPanel()` - Collapse/expand task panel
- Auto-requests browser notification permission on load

---

### utils.js

Shared utility functions and constants.

```javascript
// API Configuration
const API_URL = 'http://localhost:5001/api';
const BASE_URL = 'http://localhost:5001';

// Functions
showStatus(message, type)           // Display status message (success/error)
getSelectedDimensions(containerId)  // Get checked dimension values from container
formatDimensionName(dim)            // Convert 'nmc_competency' → 'NMC Competency'

// Constants
DIMENSION_LABELS = {
    'competency': 'Competency',
    'objective': 'Objective',
    'skill': 'Skill',
    'nmc_competency': 'NMC Competency',
    'area_topics': 'Topic Areas',
    'blooms': 'Blooms Level',
    'complexity': 'Complexity'
}
```

---

## App: Question Mapping (`app_mapping/`)

### Purpose
Map unmapped questions to curriculum dimensions using AI recommendations.

### User Flow
1. Upload question bank CSV + reference CSV
2. Select dimensions to map (Competency, Blooms, etc.)
3. Configure efficient mode & batch size
4. Click "Upload & Preview" → See file overview
5. Click "Run Audit" → AI processes questions
6. Review recommendations table
7. Select recommendations to keep
8. Click "Save & Download" → Get Excel file

### State Variables

```javascript
let uploadedFiles = { questionFile: null, referenceFile: null };
let recommendations = [];        // Array of recommendation objects
let referenceDefinitions = {};   // Code → Definition mapping
let currentDimensions = [];      // Selected dimension keys
let selectedIndices = [];        // Indices of selected recommendations
let uploadMetadata = null;       // File metadata from upload
let pendingSaveData = null;      // Data pending save confirmation
```

### Key Functions

| Function | Description |
|----------|-------------|
| `uploadAndPreview()` | Upload files, display overview |
| `displayFileOverview(data)` | Render question/reference metadata |
| `backToUpload()` | Return to upload form |
| `runAudit()` | Execute AI mapping via API |
| `displayRecommendations(recs, defs, dims)` | Render results table |
| `displayTokenUsage(usage)` | Show API token consumption |
| `updateSelection()` | Track selected checkboxes |
| `toggleSelectAll()` | Select/deselect all |
| `selectAll()` | Select all recommendations |
| `selectNone()` | Deselect all |
| `selectHighConfidence()` | Select items with confidence ≥ 0.85 |
| `saveAndDownload()` | Open save modal |
| `openSaveModal()` | Display save dialog |
| `closeSaveModal()` | Close save dialog |
| `confirmSaveAndDownload()` | Execute save + trigger download |
| `startOver()` | Reset all state |

### API Endpoints Used

- `POST /api/upload` - Upload question + reference files
- `POST /api/run-audit` - Run standard audit
- `POST /api/run-audit-efficient` - Run batched audit
- `POST /api/apply-and-save` - Save mappings + generate Excel

### Specific Styles (styles.css)

- `.overview-section` - File preview container
- `.overview-stats` - Stats flex container
- `.curriculum-list` - Reference items list
- `.curriculum-item` - Individual curriculum entry (color-coded by type)
- `.sample-questions` - Question preview section
- `.efficient-mode-box` - Green-bordered batch mode settings

---

## App: Mapping Validator (`app_rating/`)

### Purpose
Analyze existing question-curriculum mappings for accuracy and suggest corrections.

### User Flow
1. Upload pre-mapped questions file + reference CSV
2. Select dimensions to validate
3. Configure batch size
4. Click "Upload & Analyze"
5. View rating summary (correct/partial/incorrect counts)
6. Review color-coded results table
7. Select incorrect mappings to fix
8. Click "Save & Download Corrections"

### State Variables

```javascript
let uploadedFiles = { mappedFile: null, referenceFile: null };
let ratings = [];                // All rating results
let recommendations = [];        // Items needing review
let referenceDefinitions = {};   // Code → Definition mapping
let currentDimensions = [];      // Selected dimension keys
let selectedIndices = [];        // Indices of selected corrections
let pendingSaveData = null;      // Data pending save
```

### Key Functions

| Function | Description |
|----------|-------------|
| `uploadAndRate()` | Upload files + run rating analysis |
| `displayTokenUsage(usage)` | Show API consumption |
| `displayRatings(data, defs)` | Render summary + results table |
| `updateSelection()` | Track selected checkboxes |
| `toggleSelectAll()` | Select/deselect all |
| `selectAllIncorrect()` | Select only incorrect ratings |
| `selectNone()` | Deselect all |
| `saveAndDownload()` | Open save modal |
| `openSaveModal()` | Display save dialog |
| `closeSaveModal()` | Close save dialog |
| `confirmSaveAndDownload()` | Execute save + download |
| `startOver()` | Reset all state |

### API Endpoints Used

- `POST /api/upload-mapped` - Upload mapped file + reference
- `POST /api/rate-mappings` - Analyze mapping accuracy
- `POST /api/apply-corrections-and-save` - Save corrections + generate Excel

### Specific Styles (styles.css)

- `.rating-summary` - 3-column summary grid
- `.rating-stat` - Individual stat box (correct/partial/incorrect)
- `.rating-stat.correct` - Green background
- `.rating-stat.partial` - Yellow background
- `.rating-stat.incorrect` - Red background

---

## App: Curriculum Insights (`app_insights/`)

### Purpose
Generate visualizations showing mapping distribution, confidence metrics, and coverage gaps.

### User Flow
1. Upload mapped questions file
2. Optionally upload reference file (for gap analysis)
3. Select dimensions to analyze (or leave empty for auto-detect)
4. Click "Generate Insights"
5. View summary statistics
6. Browse per-dimension charts (heatmaps, gap analysis)
7. Review coverage tables
8. Click "Start Over" to analyze different file

### State Variables

```javascript
let uploadedFiles = { mappedFile: null, referenceFile: null };
```

### Key Functions

| Function | Description |
|----------|-------------|
| `generateInsights()` | Upload files + generate visualizations |
| `displayInsights(data)` | Render stats, charts, tables |
| `startOver()` | Reset all state |

### API Endpoints Used

- `POST /api/upload-mapped` - Upload mapped file
- `POST /api/generate-insights` - Generate charts + statistics

### Specific Styles (styles.css)

- `.summary-stats` - 4-column stats grid
- `.stat-card` - Individual stat box
- `.charts-grid` - 2-column chart layout
- `.chart-container` - Chart wrapper with shadow
- `.chart-container.full-width` - Spans both columns
- `.coverage-table-section` - Coverage analysis wrapper
- `.coverage-table` - Styled data table
- `.gap-row` - Red highlight for gaps
- `.low-row` - Yellow highlight for low coverage
- `.percentage-bar` - Visual bar indicator
- `.dimension-section-header` - Dark header for dimension sections
- `.dimension-badge` - Blue pill badge for dimension names

---

## Launcher Page (`index.html`)

Simple landing page with 3 cards linking to each app.

**Features:**
- Responsive 3-column grid (1-column on mobile)
- Color-coded cards matching mode themes
- Hover animations
- Link to original combined app
- Footer with backend start instructions

---

## Comparison: Combined vs Standalone

| Aspect | Combined App | Standalone Apps |
|--------|--------------|-----------------|
| Navigation | Mode selection cards | Direct to functionality |
| Sidebar | Library sidebar present | No sidebar |
| Header | Generic "Curriculum Mapping" | Mode-specific titles |
| State | All mode states in one file | Only relevant state per app |
| CSS | ~1050 lines in `<style>` tag | Split: 500 shared + ~100 per app |
| JS | ~1400 lines in `<script>` tag | Split: 165 shared + 200-400 per app |
| File size | ~95KB single HTML | ~15-20KB per app + 16KB shared |

---

## Development & Testing

### Running the Apps

```bash
# Start backend (required for all apps)
cd backend_v2
python app.py

# Option 1: Serve from root (use launcher)
cd inpods-audit_cc
python -m http.server 8002
# Open http://localhost:8002

# Option 2: Serve individual app
python -m http.server 8002 --directory app_mapping
# Open http://localhost:8002
```

### Testing Checklist

**Mode A (app_mapping):**
- [ ] Upload CSV files
- [ ] Preview shows question count + reference items
- [ ] Dimension checkboxes work
- [ ] Efficient mode toggle works
- [ ] Audit runs with progress in task panel
- [ ] Recommendations table renders correctly
- [ ] Selection buttons work
- [ ] Save modal opens/closes
- [ ] Excel downloads successfully

**Mode B (app_rating):**
- [ ] Upload mapped + reference files
- [ ] Rating summary shows correct counts
- [ ] Table shows current → suggested mappings
- [ ] Color coding matches rating
- [ ] Select incorrect button works
- [ ] Corrections save and download

**Mode C (app_insights):**
- [ ] Upload mapped file
- [ ] Charts render from API
- [ ] Dimension badges display
- [ ] Per-dimension sections show
- [ ] Coverage table populates
- [ ] Gap/low rows highlighted

---

## Browser Compatibility

Tested on:
- Chrome 120+
- Firefox 120+
- Safari 17+
- Edge 120+

**Required Features:**
- ES6+ (async/await, arrow functions, template literals)
- Fetch API
- CSS Grid
- CSS Custom Properties (optional, not currently used)

---

## Future Improvements

1. **Add service worker** for offline capability
2. **Implement localStorage** to persist state across sessions
3. **Add dark mode** toggle with CSS variables
4. **Create shared header component** to reduce HTML duplication
5. **Add error boundary** handling for API failures
6. **Implement file drag-and-drop** upload
