/**
 * Inpods Conversational Agent
 * Main agent logic with state machine and conversation handling
 */

const AgentState = {
    IDLE: 'IDLE',
    AWAIT_QUESTION_FILE: 'AWAIT_QUESTION_FILE',
    AWAIT_REFERENCE_FILE: 'AWAIT_REFERENCE_FILE',
    ANALYZING: 'ANALYZING',
    SHOW_OVERVIEW: 'SHOW_OVERVIEW',
    AWAIT_ACTION: 'AWAIT_ACTION',
    PROCESSING: 'PROCESSING',
    SHOW_RESULTS: 'SHOW_RESULTS',
    COMPLETE: 'COMPLETE'
};

const DIMENSION_INFO = {
    competency: { label: 'Competency', code: 'C1-C6', color: '#00a8cc' },
    objective: { label: 'Objective', code: 'O1-O6', color: '#00d4aa' },
    skill: { label: 'Skill', code: 'S1-S5', color: '#ffa600' },
    nmc_competency: { label: 'NMC Competency', code: 'MI1-MI3', color: '#ef4444' },
    area_topics: { label: 'Topic Areas', code: 'Topic/Subtopic', color: '#9333ea' },
    blooms: { label: 'Blooms Level', code: 'KL1-KL6', color: '#3b82f6' },
    complexity: { label: 'Complexity', code: 'Easy/Med/Hard', color: '#f59e0b' }
};

class InpodsAgent {
    constructor(options = {}) {
        this.container = options.container || '#inpods-agent';
        this.apiUrl = options.apiUrl || 'http://localhost:5001';
        this.mode = options.mode || 'embedded'; // 'embedded' or 'floating'
        this.onComplete = options.onComplete || (() => {});
        this.context = options.context || {};

        this.api = new InpodsAPIClient(this.apiUrl);
        this.state = AgentState.IDLE;
        this.messages = [];

        // File state
        this.questionFile = null;
        this.questionFileName = null;
        this.referenceFile = null;
        this.referenceFileName = null;
        this.uploadedQuestionFile = null;
        this.uploadedReferenceFile = null;

        // Analysis state
        this.fileOverview = null;
        this.isMapped = false;
        this.detectedDimensions = [];
        this.selectedDimensions = [];

        // Results state
        this.recommendations = [];
        this.ratings = null;
        this.insights = null;
        this.selectedIndices = [];
        this.savedMappedFile = null;
        this.lastAction = null;

        this.init();
    }

    // =========================================================================
    // INITIALIZATION
    // =========================================================================

    init() {
        this.render();
        this.bindEvents();
        this.addAgentMessage(this.getGreeting(), {
            fileUpload: { type: 'question' }
        });
        this.state = AgentState.AWAIT_QUESTION_FILE;
    }

    render() {
        const containerEl = document.querySelector(this.container);
        if (!containerEl) {
            console.error('Agent container not found:', this.container);
            return;
        }

        const floatingClass = this.mode === 'floating' ? 'floating' : '';

        containerEl.innerHTML = `
            <div class="inpods-agent ${floatingClass}">
                <div class="inpods-agent-header">
                    <div class="inpods-agent-avatar">🤖</div>
                    <div class="inpods-agent-title">
                        <h3>Curriculum Mapping Assistant</h3>
                        <span>Powered by Inpods</span>
                    </div>
                    <div class="inpods-agent-status"></div>
                </div>
                <div class="inpods-agent-messages" id="agentMessages"></div>
                <div class="inpods-agent-input">
                    <div class="inpods-input-wrapper">
                        <textarea
                            class="inpods-input-field"
                            id="agentInput"
                            placeholder="Type a message..."
                            rows="1"
                        ></textarea>
                    </div>
                    <button class="inpods-send-btn" id="agentSendBtn">➤</button>
                </div>
            </div>
        `;

        this.messagesEl = document.getElementById('agentMessages');
        this.inputEl = document.getElementById('agentInput');
        this.sendBtn = document.getElementById('agentSendBtn');
        this.statusEl = document.querySelector('.inpods-agent-status');
    }

    updateStatus(status) {
        if (!this.statusEl) return;
        const statusConfig = {
            'ready': { color: '#4ade80', title: 'Ready', pulse: true },
            'processing': { color: '#fbbf24', title: 'Processing...', pulse: true },
            'error': { color: '#f87171', title: 'Error', pulse: false },
            'complete': { color: '#60a5fa', title: 'Complete', pulse: false }
        };
        const config = statusConfig[status] || statusConfig['ready'];
        this.statusEl.style.backgroundColor = config.color;
        this.statusEl.title = config.title;
        this.statusEl.style.animation = config.pulse ? 'pulse 2s infinite' : 'none';
    }

    setState(newState) {
        this.state = newState;
        // Update status indicator based on state
        if (newState === AgentState.PROCESSING || newState === AgentState.ANALYZING) {
            this.updateStatus('processing');
        } else if (newState === AgentState.COMPLETE) {
            this.updateStatus('complete');
        } else {
            this.updateStatus('ready');
        }
    }

    bindEvents() {
        // Send button
        this.sendBtn.addEventListener('click', () => this.handleSend());

        // Enter key (shift+enter for newline)
        this.inputEl.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.handleSend();
            }
        });

        // Auto-resize textarea
        this.inputEl.addEventListener('input', () => {
            this.inputEl.style.height = 'auto';
            this.inputEl.style.height = Math.min(this.inputEl.scrollHeight, 100) + 'px';
        });

        // Delegate clicks for quick actions and file inputs
        this.messagesEl.addEventListener('click', (e) => {
            if (e.target.classList.contains('inpods-quick-btn')) {
                this.handleQuickAction(e.target.dataset.action);
            }
            if (e.target.classList.contains('inpods-file-dropzone') ||
                e.target.closest('.inpods-file-dropzone')) {
                const input = e.target.closest('.inpods-file-upload')?.querySelector('.inpods-file-input');
                if (input) input.click();
            }
            if (e.target.classList.contains('inpods-file-selected-remove')) {
                this.handleFileRemove(e.target.dataset.type);
            }
        });

        // File input change
        this.messagesEl.addEventListener('change', (e) => {
            if (e.target.classList.contains('inpods-file-input')) {
                this.handleFileSelect(e.target.files[0], e.target.dataset.type);
            }
        });

        // Drag and drop support
        this.messagesEl.addEventListener('dragover', (e) => {
            e.preventDefault();
            const dropzone = e.target.closest('.inpods-file-dropzone');
            if (dropzone) dropzone.classList.add('dragover');
        });

        this.messagesEl.addEventListener('dragleave', (e) => {
            const dropzone = e.target.closest('.inpods-file-dropzone');
            if (dropzone) dropzone.classList.remove('dragover');
        });

        this.messagesEl.addEventListener('drop', (e) => {
            e.preventDefault();
            const dropzone = e.target.closest('.inpods-file-dropzone');
            if (dropzone) {
                dropzone.classList.remove('dragover');
                const type = dropzone.dataset.type;
                const file = e.dataTransfer?.files?.[0];
                if (file) this.handleFileSelect(file, type);
            }
        });
    }

    // =========================================================================
    // MESSAGE HANDLING
    // =========================================================================

    addMessage(content, type = 'agent', options = {}) {
        const message = { content, type, options, timestamp: Date.now() };
        this.messages.push(message);
        this.renderMessage(message);
        this.scrollToBottom();
    }

    addAgentMessage(content, options = {}) {
        this.addMessage(content, 'agent', options);
    }

    addUserMessage(content) {
        this.addMessage(content, 'user');
    }

    renderMessage(message) {
        const div = document.createElement('div');
        div.className = `inpods-message ${message.type}`;

        let html = `<div class="inpods-message-content">${message.content}`;

        // Add special components based on options
        if (message.options.fileUpload) {
            html += this.renderFileUpload(message.options.fileUpload);
        }
        if (message.options.quickActions) {
            html += this.renderQuickActions(message.options.quickActions);
        }
        if (message.options.overview) {
            html += this.renderOverview(message.options.overview);
        }
        if (message.options.progress) {
            html += this.renderProgress(message.options.progress);
        }
        if (message.options.results) {
            html += this.renderResults(message.options.results);
        }
        if (message.options.charts) {
            html += this.renderCharts(message.options.charts);
        }

        html += '</div>';
        div.innerHTML = html;
        this.messagesEl.appendChild(div);
    }

    renderFileUpload(config) {
        return `
            <div class="inpods-file-upload">
                <div class="inpods-file-dropzone" data-type="${config.type}">
                    <div class="inpods-file-dropzone-icon">📁</div>
                    <div class="inpods-file-dropzone-text">
                        <strong>Click to upload</strong> or drag and drop<br>
                        CSV, XLSX, XLS, ODS
                    </div>
                </div>
                <input type="file" class="inpods-file-input" data-type="${config.type}" accept=".csv,.xlsx,.xls,.ods">
            </div>
        `;
    }

    renderQuickActions(actions) {
        const buttons = actions.map(action => {
            const primaryClass = action.primary ? 'primary' : '';
            return `<button class="inpods-quick-btn ${primaryClass}" data-action="${action.action}">${action.label}</button>`;
        }).join('');
        return `<div class="inpods-quick-actions">${buttons}</div>`;
    }

    renderOverview(overview) {
        let html = '';

        // Question file overview
        if (overview.questions) {
            html += `
                <div class="inpods-overview-card">
                    <h4>📄 Question Bank</h4>
                    <div class="stat"><span class="stat-label">Questions:</span><span class="stat-value">${overview.questions.count}</span></div>
                    <div class="stat"><span class="stat-label">Columns:</span><span class="stat-value">${overview.questions.columns}</span></div>
                    ${overview.questions.samples ? `
                        <div class="inpods-sample-questions">
                            ${overview.questions.samples.slice(0, 2).map(s => `
                                <div class="inpods-sample-question">
                                    <strong>Q${s.number}:</strong> ${s.text}
                                </div>
                            `).join('')}
                        </div>
                    ` : ''}
                </div>
            `;
        }

        // Reference file overview
        if (overview.reference) {
            html += `
                <div class="inpods-overview-card">
                    <h4>📚 Curriculum Reference</h4>
                    <div class="stat"><span class="stat-label">Total Items:</span><span class="stat-value">${overview.reference.totalItems}</span></div>
                    ${overview.reference.dimensions ? `
                        <div class="inpods-dimension-tags">
                            ${overview.reference.dimensions.map(d => `
                                <span class="inpods-dimension-tag">${DIMENSION_INFO[d]?.label || d}</span>
                            `).join('')}
                        </div>
                    ` : ''}
                </div>
            `;
        }

        // Mapping status
        if (overview.status) {
            const statusClass = overview.status === 'mapped' ? 'mapped' : 'unmapped';
            const statusText = overview.status === 'mapped'
                ? '✓ Questions are already mapped'
                : '⚠ Questions are unmapped';
            html += `<div class="inpods-status-badge ${statusClass}">${statusText}</div>`;
        }

        return html;
    }

    renderProgress(progress) {
        return `
            <div class="inpods-progress">
                <div class="inpods-progress-bar">
                    <div class="inpods-progress-fill" style="width: ${progress.percent}%"></div>
                </div>
                <div class="inpods-progress-text">${progress.text}</div>
            </div>
        `;
    }

    renderResults(results) {
        if (results.type === 'mapping') {
            return `
                <div class="inpods-results-summary">
                    <div class="inpods-result-stat">
                        <div class="value">${results.total}</div>
                        <div class="label">Mapped</div>
                    </div>
                    <div class="inpods-result-stat">
                        <div class="value">${results.highConfidence}</div>
                        <div class="label">High Conf</div>
                    </div>
                    <div class="inpods-result-stat">
                        <div class="value">${Math.round(results.avgConfidence * 100)}%</div>
                        <div class="label">Avg Conf</div>
                    </div>
                </div>
            `;
        }
        if (results.type === 'rating') {
            return `
                <div class="inpods-results-summary">
                    <div class="inpods-result-stat correct">
                        <div class="value">${results.correct}</div>
                        <div class="label">Correct</div>
                    </div>
                    <div class="inpods-result-stat partial">
                        <div class="value">${results.partial}</div>
                        <div class="label">Partial</div>
                    </div>
                    <div class="inpods-result-stat incorrect">
                        <div class="value">${results.incorrect}</div>
                        <div class="label">Incorrect</div>
                    </div>
                </div>
            `;
        }
        return '';
    }

    renderCharts(charts) {
        console.log('renderCharts called with:', charts);
        if (!charts || Object.keys(charts).length === 0) {
            console.warn('No charts to render');
            return `<div class="inpods-charts-error">No charts generated. Try uploading a mapped file with more data.</div>`;
        }

        const chartEntries = Object.entries(charts).filter(([key, url]) => url && !key.includes('table'));
        console.log('Filtered chart entries:', chartEntries);

        if (chartEntries.length === 0) {
            return `<div class="inpods-charts-error">No chart images available.</div>`;
        }

        // Sort to show executive_summary first
        chartEntries.sort((a, b) => {
            if (a[0] === 'executive_summary') return -1;
            if (b[0] === 'executive_summary') return 1;
            return 0;
        });

        const chartHtml = chartEntries.slice(0, 4).map(([key, url]) => {
            const fullWidth = key === 'executive_summary' ? 'full-width' : '';
            const chartUrl = this.api.getChartUrl(url);
            const chartLabel = this.formatChartLabel(key);
            console.log(`Chart ${key}: ${chartUrl}`);
            return `
                <div class="inpods-chart-thumb ${fullWidth}" data-chart-url="${chartUrl}" onclick="window.open('${chartUrl}', '_blank')">
                    <div class="inpods-chart-loading">Loading...</div>
                    <img src="${chartUrl}" alt="${chartLabel}"
                         onload="this.previousElementSibling.style.display='none'; this.style.display='block';"
                         onerror="console.error('Failed to load:', '${chartUrl}'); this.previousElementSibling.innerHTML='⚠️ Failed to load';"
                         style="display:none; min-height: 80px; cursor: pointer;">
                    <div class="inpods-chart-label">${chartLabel}</div>
                </div>
            `;
        }).join('');

        return `
            <div class="inpods-charts-grid">${chartHtml}</div>
            <div class="inpods-charts-hint">Click any chart to view full size</div>
        `;
    }

    formatChartLabel(key) {
        const labels = {
            'executive_summary': 'Summary',
            'confidence_gauge': 'Confidence',
            'coverage_heatmap': 'Coverage',
            'gap_analysis': 'Gap Analysis'
        };
        // Handle dimension-specific charts like coverage_heatmap_competency
        for (const [prefix, label] of Object.entries(labels)) {
            if (key.startsWith(prefix)) return label;
        }
        return key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
    }

    showTyping() {
        const div = document.createElement('div');
        div.className = 'inpods-message agent';
        div.id = 'typingIndicator';
        div.innerHTML = `
            <div class="inpods-message-content">
                <div class="inpods-typing">
                    <div class="inpods-typing-dot"></div>
                    <div class="inpods-typing-dot"></div>
                    <div class="inpods-typing-dot"></div>
                </div>
            </div>
        `;
        this.messagesEl.appendChild(div);
        this.scrollToBottom();
    }

    hideTyping() {
        const typing = document.getElementById('typingIndicator');
        if (typing) typing.remove();
    }

    scrollToBottom() {
        this.messagesEl.scrollTop = this.messagesEl.scrollHeight;
    }

    updateLastMessage(content, options = {}) {
        const lastMessage = this.messagesEl.lastElementChild;
        if (lastMessage && lastMessage.classList.contains('agent')) {
            const contentEl = lastMessage.querySelector('.inpods-message-content');
            if (contentEl) {
                let html = content;
                if (options.progress) html += this.renderProgress(options.progress);
                if (options.quickActions) html += this.renderQuickActions(options.quickActions);
                contentEl.innerHTML = html;
            }
        }
    }

    // =========================================================================
    // GREETING & PROMPTS
    // =========================================================================

    getGreeting() {
        return `Welcome to Inpods Curriculum Mapping! 👋

I'll help you:
• <strong>Map</strong> questions to competencies, objectives, or skills
• <strong>Validate</strong> existing mappings and suggest corrections
• <strong>Generate</strong> visual coverage reports and charts

<strong>Quick start:</strong> Upload your question file (CSV or Excel) to begin.`;
    }

    // =========================================================================
    // USER INPUT HANDLING
    // =========================================================================

    handleSend() {
        const text = this.inputEl.value.trim();
        if (!text) return;

        this.addUserMessage(text);
        this.inputEl.value = '';
        this.inputEl.style.height = 'auto';

        this.processUserInput(text);
    }

    processUserInput(text) {
        const lower = text.toLowerCase();

        // Start over
        if (lower.includes('start over') || lower.includes('reset') || lower.includes('restart')) {
            this.resetState();
            this.addAgentMessage("No problem! Let's start fresh. Please upload your question file.", {
                fileUpload: { type: 'question' }
            });
            this.state = AgentState.AWAIT_QUESTION_FILE;
            return;
        }

        // Help
        if (lower === 'help' || lower === '?') {
            this.addAgentMessage(`<strong>Available Commands:</strong>

• Type <strong>"start over"</strong> or <strong>"reset"</strong> to begin fresh
• Type <strong>"help"</strong> to see this message

<strong>Workflow:</strong>
1. Upload question file (CSV/Excel)
2. Upload reference/curriculum file
3. Choose: Map, Validate, or Generate Insights
4. Save results and view charts

<strong>Supported Dimensions:</strong>
• Competency (C1-C6)
• Objective (O1-On)
• Skill (S1-Sn)
• Blooms Level (KL1-KL6)
• NMC Competency
• Complexity (Easy/Medium/Hard)

<strong>Tips:</strong>
• Drag & drop files directly onto upload zone
• Click charts to view full-size
• Use "Save & Generate Charts" for one-click results`, {
                quickActions: [
                    { label: 'Start Over', action: 'start_over', primary: true }
                ]
            });
            return;
        }

        // Handle based on current state
        switch (this.state) {
            case AgentState.IDLE:
                this.addAgentMessage("Let's get started! Please upload your question file.", {
                    fileUpload: { type: 'question' }
                });
                this.state = AgentState.AWAIT_QUESTION_FILE;
                break;

            case AgentState.AWAIT_ACTION:
                this.handleActionSelection(text);
                break;

            case AgentState.SHOW_RESULTS:
                this.handleResultsAction(text);
                break;

            default:
                this.addAgentMessage("I'm waiting for a file upload. Please use the upload button above, or type \"start over\" to begin again.");
        }
    }

    handleQuickAction(action) {
        switch (action) {
            case 'upload_question':
                // Trigger file input
                break;

            case 'map_competency':
                this.selectedDimensions = ['competency'];
                this.startMapping();
                break;

            case 'map_blooms':
                this.selectedDimensions = ['blooms'];
                this.startMapping();
                break;

            case 'map_multiple':
                this.addAgentMessage("Which dimensions would you like to map to?", {
                    quickActions: this.detectedDimensions.map(d => ({
                        label: DIMENSION_INFO[d]?.label || d,
                        action: `toggle_dim_${d}`
                    })).concat([{ label: 'Start Mapping', action: 'start_mapping', primary: true }])
                });
                break;

            case 'validate':
                this.selectedDimensions = this.detectedDimensions.slice(0, 2);
                this.startRating();
                break;

            case 'insights':
                this.startInsights();
                break;

            case 'save':
                this.saveResults();
                break;

            case 'visualize':
                this.startInsightsAfterMapping();
                break;

            case 'save_and_visualize':
                this.saveAndGenerateCharts();
                break;

            case 'validate_new':
                this.validateNewMappings();
                break;

            case 'start_over':
                this.resetState();
                this.addAgentMessage("Let's start fresh! Please upload your question file.", {
                    fileUpload: { type: 'question' }
                });
                this.state = AgentState.AWAIT_QUESTION_FILE;
                break;

            default:
                if (action.startsWith('toggle_dim_')) {
                    const dim = action.replace('toggle_dim_', '');
                    if (this.selectedDimensions.includes(dim)) {
                        this.selectedDimensions = this.selectedDimensions.filter(d => d !== dim);
                    } else {
                        this.selectedDimensions.push(dim);
                    }
                    this.addUserMessage(`Selected: ${this.selectedDimensions.map(d => DIMENSION_INFO[d]?.label).join(', ') || 'None'}`);
                } else if (action === 'start_mapping') {
                    if (this.selectedDimensions.length > 0) {
                        this.startMapping();
                    } else {
                        this.addAgentMessage("Please select at least one dimension first.");
                    }
                }
        }
    }

    handleActionSelection(text) {
        const lower = text.toLowerCase();

        if (lower.includes('map') && lower.includes('competen')) {
            this.selectedDimensions = ['competency'];
            this.startMapping();
        } else if (lower.includes('map') && lower.includes('bloom')) {
            this.selectedDimensions = ['blooms'];
            this.startMapping();
        } else if (lower.includes('map')) {
            this.selectedDimensions = this.detectedDimensions.slice(0, 2);
            this.startMapping();
        } else if (lower.includes('valid') || lower.includes('rate') || lower.includes('check')) {
            this.startRating();
        } else if (lower.includes('insight') || lower.includes('visual') || lower.includes('chart')) {
            this.startInsights();
        } else {
            this.addAgentMessage("I didn't quite understand. Would you like to:", {
                quickActions: this.getActionButtons()
            });
        }
    }

    handleResultsAction(text) {
        const lower = text.toLowerCase();

        if (lower.includes('save') || lower.includes('download')) {
            this.saveResults();
        } else if (lower.includes('visual') || lower.includes('chart') || lower.includes('insight')) {
            this.startInsights();
        } else if (lower.includes('start over') || lower.includes('new')) {
            this.handleQuickAction('start_over');
        } else {
            this.addAgentMessage("What would you like to do next?", {
                quickActions: [
                    { label: 'Save & Download', action: 'save', primary: true },
                    { label: 'Generate Charts', action: 'visualize' },
                    { label: 'Start Over', action: 'start_over' }
                ]
            });
        }
    }

    // =========================================================================
    // FILE HANDLING
    // =========================================================================

    handleFileSelect(file, type) {
        if (!file) return;

        const allowedExtensions = ['csv', 'xlsx', 'xls', 'ods'];
        const ext = file.name.split('.').pop().toLowerCase();

        if (!allowedExtensions.includes(ext)) {
            this.addAgentMessage(`Sorry, I can only accept CSV or Excel files. You uploaded a .${ext} file.`);
            return;
        }

        if (type === 'question') {
            this.questionFile = file;
            this.questionFileName = file.name;
            this.addUserMessage(`Uploaded: ${file.name}`);

            if (this.state === AgentState.AWAIT_QUESTION_FILE || this.state === AgentState.IDLE) {
                this.addAgentMessage(`Great! Now please upload your <strong>reference/curriculum file</strong>.`, {
                    fileUpload: { type: 'reference' }
                });
                this.state = AgentState.AWAIT_REFERENCE_FILE;
            }
        } else if (type === 'reference') {
            this.referenceFile = file;
            this.referenceFileName = file.name;
            this.addUserMessage(`Uploaded: ${file.name}`);

            if (this.state === AgentState.AWAIT_REFERENCE_FILE) {
                this.analyzeFiles();
            }
        }
    }

    handleFileRemove(type) {
        if (type === 'question') {
            this.questionFile = null;
            this.questionFileName = null;
        } else if (type === 'reference') {
            this.referenceFile = null;
            this.referenceFileName = null;
        }
    }

    // =========================================================================
    // CORE OPERATIONS
    // =========================================================================

    async analyzeFiles() {
        this.setState(AgentState.ANALYZING);
        this.showTyping();

        try {
            // Determine if the question file looks mapped or unmapped
            const result = await this.api.uploadFiles(this.questionFile, this.referenceFile);

            this.uploadedQuestionFile = result.question_file;
            this.uploadedReferenceFile = result.reference_file;
            this.fileOverview = result;

            // Detect if mapped
            this.isMapped = this.detectMappedStatus(result);
            this.detectedDimensions = this.detectDimensions(result.reference_metadata);

            this.hideTyping();

            // Build overview
            const overview = {
                questions: {
                    count: result.question_metadata?.total_questions || result.question_count,
                    columns: result.question_metadata?.columns?.length || 0,
                    samples: result.question_metadata?.sample_questions
                },
                reference: {
                    totalItems: this.countReferenceItems(result.reference_metadata),
                    dimensions: this.detectedDimensions
                },
                status: this.isMapped ? 'mapped' : 'unmapped'
            };

            this.addAgentMessage(`Here's what I found:`, { overview });

            // Suggest actions
            this.state = AgentState.AWAIT_ACTION;
            setTimeout(() => {
                this.addAgentMessage("What would you like to do?", {
                    quickActions: this.getActionButtons()
                });
            }, 500);

        } catch (error) {
            this.hideTyping();
            this.addAgentMessage(`Oops! There was an error analyzing your files: ${error.message}

Please check your files and try again.`, {
                quickActions: [{ label: 'Start Over', action: 'start_over' }]
            });
            this.state = AgentState.IDLE;
        }
    }

    getActionButtons() {
        if (this.isMapped) {
            return [
                { label: 'Validate Mappings', action: 'validate', primary: true },
                { label: 'Generate Insights', action: 'insights' },
                { label: 'Re-map Questions', action: 'map_multiple' }
            ];
        } else {
            const buttons = [];
            if (this.detectedDimensions.includes('competency')) {
                buttons.push({ label: 'Map to Competency', action: 'map_competency', primary: true });
            }
            if (this.detectedDimensions.includes('blooms')) {
                buttons.push({ label: 'Map to Blooms', action: 'map_blooms' });
            }
            buttons.push({ label: 'Map to Multiple...', action: 'map_multiple' });
            return buttons;
        }
    }

    async startMapping() {
        this.setState(AgentState.PROCESSING);
        const dimLabels = this.selectedDimensions.map(d => DIMENSION_INFO[d]?.label).join(', ');

        this.addAgentMessage(`Mapping your questions to: <strong>${dimLabels}</strong>

This may take a moment...`, { progress: { percent: 0, text: 'Starting...' } });

        try {
            // Simulate progress updates
            let progress = 0;
            const progressInterval = setInterval(() => {
                progress = Math.min(progress + Math.random() * 15, 90);
                this.updateLastMessage(`Mapping your questions to: <strong>${dimLabels}</strong>`, {
                    progress: { percent: progress, text: `Processing... ${Math.round(progress)}%` }
                });
            }, 800);

            const result = await this.api.mapQuestions(
                this.uploadedQuestionFile,
                this.uploadedReferenceFile,
                this.selectedDimensions,
                5
            );

            clearInterval(progressInterval);
            this.recommendations = result.recommendations || [];

            // Calculate stats
            const highConfidence = this.recommendations.filter(r => r.confidence >= 0.85).length;
            const avgConfidence = this.recommendations.reduce((sum, r) => sum + (r.confidence || 0), 0) / this.recommendations.length;

            this.setState(AgentState.SHOW_RESULTS);
            this.lastAction = 'mapping';
            this.addAgentMessage(`Done! Mapped ${this.recommendations.length} questions with ${Math.round(avgConfidence * 100)}% average confidence.`, {
                results: {
                    type: 'mapping',
                    total: this.recommendations.length,
                    highConfidence: highConfidence,
                    avgConfidence: avgConfidence
                },
                quickActions: [
                    { label: 'Save & Generate Charts', action: 'save_and_visualize', primary: true },
                    { label: 'Save Only', action: 'save' },
                    { label: 'Validate First', action: 'validate_new' },
                    { label: 'Start Over', action: 'start_over' }
                ]
            });

        } catch (error) {
            this.addAgentMessage(`Error during mapping: ${error.message}`, {
                quickActions: [{ label: 'Try Again', action: 'map_multiple' }, { label: 'Start Over', action: 'start_over' }]
            });
            this.state = AgentState.AWAIT_ACTION;
        }
    }

    async startRating() {
        this.setState(AgentState.PROCESSING);

        if (!this.selectedDimensions.length) {
            this.selectedDimensions = this.detectedDimensions.slice(0, 2);
        }
        const dimLabels = this.selectedDimensions.map(d => DIMENSION_INFO[d]?.label).join(', ');

        this.addAgentMessage(`Validating your mappings for: <strong>${dimLabels}</strong>

Analyzing each question...`, { progress: { percent: 0, text: 'Starting...' } });

        try {
            // Need to re-upload as mapped file
            const uploadResult = await this.api.uploadMappedFile(this.questionFile, this.referenceFile);
            this.uploadedQuestionFile = uploadResult.mapped_file;
            this.uploadedReferenceFile = uploadResult.reference_file;

            let progress = 0;
            const progressInterval = setInterval(() => {
                progress = Math.min(progress + Math.random() * 15, 90);
                this.updateLastMessage(`Validating your mappings for: <strong>${dimLabels}</strong>`, {
                    progress: { percent: progress, text: `Analyzing... ${Math.round(progress)}%` }
                });
            }, 800);

            const result = await this.api.rateMappings(
                this.uploadedQuestionFile,
                this.uploadedReferenceFile,
                this.selectedDimensions,
                5
            );

            clearInterval(progressInterval);
            this.ratings = result;
            this.recommendations = result.recommendations || [];

            this.setState(AgentState.SHOW_RESULTS);
            const correct = result.summary?.correct || 0;
            const partial = result.summary?.partially_correct || 0;
            const incorrect = result.summary?.incorrect || 0;
            const total = correct + partial + incorrect;
            const accuracy = total > 0 ? Math.round((correct / total) * 100) : 0;

            this.addAgentMessage(`Validation complete! ${accuracy}% accuracy (${correct}/${total} correct)`, {
                results: {
                    type: 'rating',
                    correct: correct,
                    partial: partial,
                    incorrect: incorrect
                },
                quickActions: [
                    { label: 'Save & Generate Charts', action: 'save_and_visualize', primary: true },
                    { label: 'Save Corrections Only', action: 'save' },
                    { label: 'Start Over', action: 'start_over' }
                ]
            });

        } catch (error) {
            this.addAgentMessage(`Error during validation: ${error.message}`, {
                quickActions: [{ label: 'Try Again', action: 'validate' }, { label: 'Start Over', action: 'start_over' }]
            });
            this.state = AgentState.AWAIT_ACTION;
        }
    }

    async startInsights() {
        this.setState(AgentState.PROCESSING);
        this.addAgentMessage(`Generating visualizations...`, { progress: { percent: 30, text: 'Creating charts...' } });

        try {
            // Re-upload if needed
            if (!this.uploadedQuestionFile) {
                const uploadResult = await this.api.uploadMappedFile(this.questionFile, this.referenceFile);
                this.uploadedQuestionFile = uploadResult.mapped_file;
                this.uploadedReferenceFile = uploadResult.reference_file;
            }

            const result = await this.api.generateInsights(
                this.uploadedQuestionFile,
                this.uploadedReferenceFile,
                this.selectedDimensions
            );

            this.insights = result;

            this.setState(AgentState.COMPLETE);
            this.addAgentMessage(`Charts generated!`, {
                charts: result.charts,
                quickActions: [
                    { label: 'Start Over', action: 'start_over' }
                ]
            });

            this.onComplete({ type: 'insights', data: result });

        } catch (error) {
            this.addAgentMessage(`Error generating charts: ${error.message}`, {
                quickActions: [{ label: 'Try Again', action: 'visualize' }, { label: 'Start Over', action: 'start_over' }]
            });
            this.setState(AgentState.SHOW_RESULTS);
        }
    }

    async saveResults() {
        const name = `Mapping_${new Date().toISOString().slice(0, 10)}`;
        this.selectedIndices = this.recommendations.map((_, i) => i); // Select all

        this.addAgentMessage(`Saving and preparing download...`);

        try {
            let result;
            if (this.ratings) {
                // Mode B - corrections
                result = await this.api.saveAndDownloadCorrections(
                    this.uploadedQuestionFile,
                    this.recommendations,
                    this.selectedIndices,
                    this.selectedDimensions,
                    name
                );
            } else {
                // Mode A - mappings
                result = await this.api.saveAndDownloadMappings(
                    this.uploadedQuestionFile,
                    this.recommendations,
                    this.selectedIndices,
                    this.selectedDimensions,
                    name
                );
            }

            this.api.downloadFile(result.download_url);

            // Store the saved file for subsequent operations (like chart generation)
            if (result.saved_file) {
                this.savedMappedFile = result.saved_file;
            }

            this.setState(AgentState.COMPLETE);
            this.addAgentMessage(`Saved! Your Excel file is downloading.

Would you like to generate charts from this data?`, {
                quickActions: [
                    { label: 'Generate Charts', action: 'visualize', primary: true },
                    { label: 'Start Over', action: 'start_over' }
                ]
            });

            this.onComplete({ type: 'save', data: result });

        } catch (error) {
            this.addAgentMessage(`Error saving: ${error.message}`, {
                quickActions: [{ label: 'Try Again', action: 'save' }, { label: 'Start Over', action: 'start_over' }]
            });
        }
    }

    // =========================================================================
    // POST-MAPPING OPERATIONS (uses in-memory recommendations)
    // =========================================================================

    async validateNewMappings() {
        // First, save the mappings to create a mapped file
        this.setState(AgentState.PROCESSING);
        this.addAgentMessage(`Preparing to validate...`, { progress: { percent: 10, text: 'Saving mappings...' } });

        try {
            const name = `Temp_Mapping_${Date.now()}`;
            this.selectedIndices = this.recommendations.map((_, i) => i);

            // Save mappings to get a proper mapped file
            const saveResult = await this.api.saveAndDownloadMappings(
                this.uploadedQuestionFile,
                this.recommendations,
                this.selectedIndices,
                this.selectedDimensions,
                name
            );

            // Now use the saved file for validation (saved_file is CSV in uploads folder)
            const mappedFileName = saveResult.saved_file || saveResult.output_file;

            this.updateLastMessage(`Validating mappings...`, { progress: { percent: 40, text: 'Analyzing each question...' } });

            let progress = 40;
            const progressInterval = setInterval(() => {
                progress = Math.min(progress + Math.random() * 15, 90);
                this.updateLastMessage(`Validating mappings...`, {
                    progress: { percent: progress, text: `Analyzing... ${Math.round(progress)}%` }
                });
            }, 800);

            const result = await this.api.rateMappings(
                mappedFileName,
                this.uploadedReferenceFile,
                this.selectedDimensions,
                5
            );

            clearInterval(progressInterval);
            this.ratings = result;
            this.recommendations = result.recommendations || [];

            this.setState(AgentState.SHOW_RESULTS);
            const correct = result.summary?.correct || 0;
            const partial = result.summary?.partially_correct || 0;
            const incorrect = result.summary?.incorrect || 0;
            const total = correct + partial + incorrect;
            const accuracy = total > 0 ? Math.round((correct / total) * 100) : 0;

            this.addAgentMessage(`Validation complete! ${accuracy}% accuracy (${correct}/${total} correct)`, {
                results: {
                    type: 'rating',
                    correct: correct,
                    partial: partial,
                    incorrect: incorrect
                },
                quickActions: [
                    { label: 'Save & Generate Charts', action: 'save_and_visualize', primary: true },
                    { label: 'Save Corrections Only', action: 'save' },
                    { label: 'Start Over', action: 'start_over' }
                ]
            });

        } catch (error) {
            this.addAgentMessage(`Error during validation: ${error.message}`, {
                quickActions: [{ label: 'Try Again', action: 'validate_new' }, { label: 'Start Over', action: 'start_over' }]
            });
            this.setState(AgentState.SHOW_RESULTS);
        }
    }

    async startInsightsAfterMapping() {
        // Check if we already have a saved mapped file from a previous save operation
        if (this.savedMappedFile) {
            this.setState(AgentState.PROCESSING);
            this.addAgentMessage(`Generating charts...`, { progress: { percent: 30, text: 'Creating visualizations...' } });

            try {
                const result = await this.api.generateInsights(
                    this.savedMappedFile,
                    this.uploadedReferenceFile,
                    this.selectedDimensions
                );

                this.insights = result;

                this.setState(AgentState.COMPLETE);
                this.addAgentMessage(`Charts generated!`, {
                    charts: result.charts,
                    quickActions: [
                        { label: 'Start Over', action: 'start_over' }
                    ]
                });

                this.onComplete({ type: 'insights', data: result });

            } catch (error) {
                this.addAgentMessage(`Error generating charts: ${error.message}`, {
                    quickActions: [{ label: 'Try Again', action: 'visualize' }, { label: 'Start Over', action: 'start_over' }]
                });
                this.setState(AgentState.SHOW_RESULTS);
            }
        }
        // If we have recommendations from mapping but haven't saved yet, save first
        else if (this.recommendations.length > 0 && !this.ratings) {
            this.setState(AgentState.PROCESSING);
            this.addAgentMessage(`Preparing visualizations...`, { progress: { percent: 10, text: 'Saving mappings first...' } });

            try {
                const name = `Temp_Mapping_${Date.now()}`;
                this.selectedIndices = this.recommendations.map((_, i) => i);

                // Save mappings to create a properly mapped file
                const saveResult = await this.api.saveAndDownloadMappings(
                    this.uploadedQuestionFile,
                    this.recommendations,
                    this.selectedIndices,
                    this.selectedDimensions,
                    name
                );

                // Use the saved mapped file for insights (saved_file is CSV in uploads folder)
                const mappedFileName = saveResult.saved_file || saveResult.output_file;
                this.savedMappedFile = mappedFileName;

                this.updateLastMessage(`Generating charts...`, { progress: { percent: 50, text: 'Creating visualizations...' } });

                const result = await this.api.generateInsights(
                    mappedFileName,
                    this.uploadedReferenceFile,
                    this.selectedDimensions
                );

                console.log('Insights result:', result);
                console.log('Charts:', result.charts);
                this.insights = result;

                this.setState(AgentState.COMPLETE);
                this.addAgentMessage(`Charts generated!`, {
                    charts: result.charts,
                    quickActions: [
                        { label: 'Start Over', action: 'start_over' }
                    ]
                });

                this.onComplete({ type: 'insights', data: result });

            } catch (error) {
                this.addAgentMessage(`Error generating charts: ${error.message}`, {
                    quickActions: [{ label: 'Try Again', action: 'visualize' }, { label: 'Start Over', action: 'start_over' }]
                });
                this.setState(AgentState.SHOW_RESULTS);
            }
        } else {
            // Fall back to regular insights (for already-mapped files)
            this.startInsights();
        }
    }

    async saveAndGenerateCharts() {
        // Combined operation: Save mappings and generate charts in one flow
        this.setState(AgentState.PROCESSING);
        this.addAgentMessage(`Saving mappings and generating charts...`, { progress: { percent: 10, text: 'Saving...' } });

        try {
            const name = `Mapping_${new Date().toISOString().slice(0, 10)}`;
            this.selectedIndices = this.recommendations.map((_, i) => i);

            // Step 1: Save mappings
            const saveResult = await this.api.saveAndDownloadMappings(
                this.uploadedQuestionFile,
                this.recommendations,
                this.selectedIndices,
                this.selectedDimensions,
                name
            );

            const mappedFileName = saveResult.saved_file || saveResult.output_file;
            this.savedMappedFile = mappedFileName;

            // Trigger download
            this.api.downloadFile(saveResult.download_url);

            this.updateLastMessage(`Saved! Now generating charts...`, { progress: { percent: 50, text: 'Creating visualizations...' } });

            // Step 2: Generate insights
            const result = await this.api.generateInsights(
                mappedFileName,
                this.uploadedReferenceFile,
                this.selectedDimensions
            );

            this.insights = result;
            this.setState(AgentState.COMPLETE);

            this.addAgentMessage(`All done! Your Excel file is downloading and here are your insights:`, {
                charts: result.charts,
                quickActions: [
                    { label: 'Validate Mappings', action: 'validate_new' },
                    { label: 'Start Over', action: 'start_over' }
                ]
            });

            this.onComplete({ type: 'save_and_insights', data: { save: saveResult, insights: result } });

        } catch (error) {
            this.addAgentMessage(`Error: ${error.message}`, {
                quickActions: [
                    { label: 'Try Again', action: 'save_and_visualize' },
                    { label: 'Save Only', action: 'save' },
                    { label: 'Start Over', action: 'start_over' }
                ]
            });
            this.setState(AgentState.SHOW_RESULTS);
        }
    }

    // =========================================================================
    // HELPERS
    // =========================================================================

    detectMappedStatus(result) {
        const columns = result.question_metadata?.columns || [];
        const mappingColumns = [
            'mapped_competency', 'mapped_objective', 'mapped_skill',
            'mapped_topic', 'mapped_blooms', 'mapped_complexity', 'mapped_nmc'
        ];
        return columns.some(col => mappingColumns.some(mc => col.toLowerCase().includes(mc)));
    }

    detectDimensions(refMeta) {
        if (!refMeta) return ['competency'];

        const dims = [];
        if (refMeta.competencies?.length) dims.push('competency');
        if (refMeta.objectives?.length) dims.push('objective');
        if (refMeta.skills?.length) dims.push('skill');
        if (refMeta.nmc_competencies?.length) dims.push('nmc_competency');
        if (refMeta.topics?.length) dims.push('area_topics');
        if (refMeta.blooms?.length) dims.push('blooms');
        if (refMeta.complexity?.length) dims.push('complexity');

        return dims.length ? dims : ['competency'];
    }

    countReferenceItems(refMeta) {
        if (!refMeta) return 0;
        return (refMeta.competencies?.length || 0) +
               (refMeta.objectives?.length || 0) +
               (refMeta.skills?.length || 0) +
               (refMeta.nmc_competencies?.length || 0) +
               (refMeta.topics?.length || 0) +
               (refMeta.blooms?.length || 0) +
               (refMeta.complexity?.length || 0);
    }

    resetState() {
        this.state = AgentState.IDLE;
        this.questionFile = null;
        this.questionFileName = null;
        this.referenceFile = null;
        this.referenceFileName = null;
        this.uploadedQuestionFile = null;
        this.uploadedReferenceFile = null;
        this.fileOverview = null;
        this.isMapped = false;
        this.detectedDimensions = [];
        this.selectedDimensions = [];
        this.recommendations = [];
        this.ratings = null;
        this.insights = null;
        this.selectedIndices = [];
        this.savedMappedFile = null;
        this.lastAction = null;
    }
}

// Static init method for easy setup
InpodsAgent.init = function(options) {
    return new InpodsAgent(options);
};

// Export
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { InpodsAgent, AgentState };
}
