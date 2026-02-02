# Inpods Conversational Agent

A chat-based assistant for curriculum mapping operations.

## Quick Start

```bash
# 1. Start backend
cd backend_v2 && python app.py

# 2. Serve agent
python -m http.server 8002

# 3. Open
http://localhost:8002/agent_v2/
```

---

## Features

| Feature | Description |
|---------|-------------|
| File Upload | Drag & drop or click to upload CSV/Excel |
| Auto-Detection | Detects mapped vs unmapped questions |
| Dimension Detection | Finds available dimensions in reference file |
| Smart Suggestions | Recommends actions based on file state |
| Progress Tracking | Shows batch progress during processing |
| Visual Results | Displays charts and statistics |

---

## Integration

### Standalone Page

```html
<link rel="stylesheet" href="agent_v2/agent.css">
<div id="agent-container"></div>
<script src="agent_v2/api-client.js"></script>
<script src="agent_v2/agent.js"></script>
<script>
    InpodsAgent.init({
        container: '#agent-container',
        apiUrl: 'http://localhost:5001'
    });
</script>
```

### Floating Chat Widget

```javascript
InpodsAgent.init({
    container: '#agent-container',
    apiUrl: 'http://localhost:5001',
    mode: 'floating',
    onComplete: (result) => {
        console.log('Task completed:', result);
    }
});
```

### Embed in Existing App

```javascript
// In your app
const agent = InpodsAgent.init({
    container: '#sidebar-agent',
    apiUrl: API_URL,
    context: {
        currentFiles: uploadedFiles,
        selectedDimensions: ['competency']
    }
});

// Listen for completion
agent.onComplete = (result) => {
    if (result.type === 'save') {
        refreshLibrary();
    }
};
```

---

## Configuration Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `container` | string | `'#inpods-agent'` | CSS selector for container |
| `apiUrl` | string | `'http://localhost:5001'` | Backend API URL |
| `mode` | string | `'embedded'` | `'embedded'` or `'floating'` |
| `onComplete` | function | `() => {}` | Callback when task completes |
| `context` | object | `{}` | Pre-populated context data |

---

## State Machine

```
IDLE
  ↓ User starts
AWAIT_QUESTION_FILE
  ↓ File uploaded
AWAIT_REFERENCE_FILE
  ↓ File uploaded
ANALYZING
  ↓ Analysis complete
SHOW_OVERVIEW
  ↓ User confirms
AWAIT_ACTION
  ↓ User selects action
PROCESSING
  ↓ Task complete
SHOW_RESULTS
  ↓ User saves/continues
COMPLETE
```

---

## Conversation Examples

### Mapping Unmapped Questions

```
Agent: Hi! Upload your question file.
User:  [uploads questions.csv]
Agent: Now upload your reference file.
User:  [uploads reference.csv]
Agent: Found 46 unmapped questions.
       Reference has: Competency, Blooms
       [Map to Competency] [Map to Blooms]
User:  [clicks Map to Competency]
Agent: Mapping... 80% complete
Agent: Done! 46 mapped, 87% avg confidence
       [Save & Download] [Generate Charts]
```

### Validating Existing Mappings

```
Agent: Found 46 mapped questions.
       [Validate Mappings] [Generate Insights]
User:  [clicks Validate Mappings]
Agent: Validating...
Agent: Results: 38 correct, 5 partial, 3 incorrect
       [Save Corrections] [Generate Charts]
```

---

## API Client

The `InpodsAPIClient` class wraps all backend calls:

```javascript
const api = new InpodsAPIClient('http://localhost:5001');

// Upload files
await api.uploadFiles(questionFile, referenceFile);

// Map questions
await api.mapQuestions(qFile, refFile, ['competency'], 5);

// Rate mappings
await api.rateMappings(mappedFile, refFile, ['competency'], 5);

// Generate insights
await api.generateInsights(mappedFile, refFile, []);

// Save & download
await api.saveAndDownloadMappings(qFile, recs, indices, dims, name);
```

---

## Files

```
agent_v2/
├── index.html      # Demo page
├── agent.css       # Chat UI styles
├── agent.js        # Core logic (state machine)
├── api-client.js   # Backend API wrapper
├── README.md       # This file
└── tests/
    ├── agent.test.js      # Test cases
    ├── test-runner.html   # Browser test runner
    └── README.md          # Test documentation
```

---

## Customization

### Styling

Override CSS variables or classes:

```css
/* Change primary color */
.inpods-agent-header {
    background: linear-gradient(135deg, #your-color, #your-color-2);
}

/* Change message bubble colors */
.inpods-message.agent .inpods-message-content {
    background: #your-bg;
}
```

### Adding Custom Actions

```javascript
// Extend handleQuickAction
handleQuickAction(action) {
    if (action === 'my_custom_action') {
        this.doCustomThing();
        return;
    }
    // ... default handling
}
```

---

## Testing

```bash
# Open test runner
http://localhost:8002/agent_v2/tests/test-runner.html
```

17 test cases covering:
- File upload & validation
- Mapped/unmapped detection
- Dimension detection
- Mapping operations
- Rating operations
- Visualization
- Conversation flow

---

## Dependencies

- **None** - Vanilla JavaScript, no frameworks
- Requires `backend_v2` running on port 5001

---

## Browser Support

- Chrome 80+
- Firefox 75+
- Safari 13+
- Edge 80+
