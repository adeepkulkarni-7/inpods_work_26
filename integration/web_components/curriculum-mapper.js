/**
 * Curriculum Mapper Web Component
 *
 * A framework-agnostic web component that can be embedded in any HTML page
 * to provide curriculum mapping functionality.
 *
 * Usage:
 *   <script src="curriculum-mapper.js"></script>
 *   <curriculum-mapper api-base="https://api.example.com"></curriculum-mapper>
 *
 * Attributes:
 *   - api-base: Base URL of the curriculum mapping API (required)
 *   - dimension: Default dimension (optional, default: 'nmc_competency')
 *   - auth-token: Bearer token for authenticated requests (optional)
 *   - theme: 'light' or 'dark' (optional, default: 'light')
 */

class CurriculumMapper extends HTMLElement {
    constructor() {
        super();
        this.attachShadow({ mode: 'open' });

        // State
        this.state = {
            mode: 'map', // 'map', 'rate', 'insights'
            questionFile: null,
            referenceFile: null,
            mappedFile: null,
            recommendations: [],
            selectedIndices: [],
            loading: false,
            error: null,
            result: null
        };

        // Config
        this.apiBase = '';
        this.dimension = 'nmc_competency';
        this.authToken = '';
        this.theme = 'light';
    }

    static get observedAttributes() {
        return ['api-base', 'dimension', 'auth-token', 'theme'];
    }

    attributeChangedCallback(name, oldValue, newValue) {
        switch (name) {
            case 'api-base':
                this.apiBase = newValue;
                break;
            case 'dimension':
                this.dimension = newValue || 'nmc_competency';
                break;
            case 'auth-token':
                this.authToken = newValue || '';
                break;
            case 'theme':
                this.theme = newValue || 'light';
                this.updateTheme();
                break;
        }
    }

    connectedCallback() {
        this.apiBase = this.getAttribute('api-base') || '';
        this.dimension = this.getAttribute('dimension') || 'nmc_competency';
        this.authToken = this.getAttribute('auth-token') || '';
        this.theme = this.getAttribute('theme') || 'light';

        this.render();
        this.attachEventListeners();
    }

    // ==========================================
    // RENDERING
    // ==========================================

    render() {
        this.shadowRoot.innerHTML = `
            <style>${this.getStyles()}</style>
            <div class="curriculum-mapper ${this.theme}">
                <header class="header">
                    <h2>Curriculum Mapping</h2>
                    <div class="mode-tabs">
                        <button class="tab ${this.state.mode === 'map' ? 'active' : ''}" data-mode="map">
                            Map Questions
                        </button>
                        <button class="tab ${this.state.mode === 'rate' ? 'active' : ''}" data-mode="rate">
                            Rate Mappings
                        </button>
                        <button class="tab ${this.state.mode === 'insights' ? 'active' : ''}" data-mode="insights">
                            Generate Insights
                        </button>
                    </div>
                </header>

                <main class="content">
                    ${this.renderContent()}
                </main>

                ${this.state.error ? `<div class="error">${this.state.error}</div>` : ''}
                ${this.state.loading ? '<div class="loading"><div class="spinner"></div>Processing...</div>' : ''}
            </div>
        `;

        this.attachEventListeners();
    }

    renderContent() {
        switch (this.state.mode) {
            case 'map':
                return this.renderMapMode();
            case 'rate':
                return this.renderRateMode();
            case 'insights':
                return this.renderInsightsMode();
            default:
                return '';
        }
    }

    renderMapMode() {
        if (this.state.result && this.state.result.recommendations) {
            return this.renderRecommendations();
        }

        return `
            <div class="upload-section">
                <h3>Upload Files</h3>

                <div class="file-input">
                    <label>Question Bank (CSV/Excel)</label>
                    <input type="file" id="questionFile" accept=".csv,.xlsx,.xls,.ods">
                    <span class="file-name">${this.state.questionFile?.name || 'No file selected'}</span>
                </div>

                <div class="file-input">
                    <label>Reference Curriculum (CSV/Excel)</label>
                    <input type="file" id="referenceFile" accept=".csv,.xlsx,.xls,.ods">
                    <span class="file-name">${this.state.referenceFile?.name || 'No file selected'}</span>
                </div>

                <div class="form-group">
                    <label>Mapping Dimension</label>
                    <select id="dimension">
                        <option value="nmc_competency" ${this.dimension === 'nmc_competency' ? 'selected' : ''}>NMC Competency</option>
                        <option value="area_topics" ${this.dimension === 'area_topics' ? 'selected' : ''}>Area Topics</option>
                        <option value="competency" ${this.dimension === 'competency' ? 'selected' : ''}>Competency (C1-C9)</option>
                        <option value="objective" ${this.dimension === 'objective' ? 'selected' : ''}>Objective (O1-O9)</option>
                        <option value="skill" ${this.dimension === 'skill' ? 'selected' : ''}>Skill (S1-S5)</option>
                    </select>
                </div>

                <button class="btn primary" id="runMapping" ${!this.state.questionFile || !this.state.referenceFile ? 'disabled' : ''}>
                    Run Mapping
                </button>
            </div>
        `;
    }

    renderRateMode() {
        if (this.state.result && this.state.result.ratings) {
            return this.renderRatings();
        }

        return `
            <div class="upload-section">
                <h3>Upload Pre-Mapped File</h3>

                <div class="file-input">
                    <label>Mapped Questions (CSV/Excel with existing mappings)</label>
                    <input type="file" id="mappedFile" accept=".csv,.xlsx,.xls,.ods">
                    <span class="file-name">${this.state.mappedFile?.name || 'No file selected'}</span>
                </div>

                <div class="file-input">
                    <label>Reference Curriculum (CSV/Excel)</label>
                    <input type="file" id="referenceFile" accept=".csv,.xlsx,.xls,.ods">
                    <span class="file-name">${this.state.referenceFile?.name || 'No file selected'}</span>
                </div>

                <div class="form-group">
                    <label>Mapping Dimension</label>
                    <select id="dimension">
                        <option value="nmc_competency" ${this.dimension === 'nmc_competency' ? 'selected' : ''}>NMC Competency</option>
                        <option value="area_topics" ${this.dimension === 'area_topics' ? 'selected' : ''}>Area Topics</option>
                        <option value="competency" ${this.dimension === 'competency' ? 'selected' : ''}>Competency</option>
                        <option value="objective" ${this.dimension === 'objective' ? 'selected' : ''}>Objective</option>
                        <option value="skill" ${this.dimension === 'skill' ? 'selected' : ''}>Skill</option>
                    </select>
                </div>

                <button class="btn primary" id="runRating" ${!this.state.mappedFile || !this.state.referenceFile ? 'disabled' : ''}>
                    Rate Mappings
                </button>
            </div>
        `;
    }

    renderInsightsMode() {
        if (this.state.result && this.state.result.charts) {
            return this.renderCharts();
        }

        return `
            <div class="upload-section">
                <h3>Upload Mapped File for Insights</h3>

                <div class="file-input">
                    <label>Mapped Questions (CSV/Excel with mappings)</label>
                    <input type="file" id="mappedFile" accept=".csv,.xlsx,.xls,.ods">
                    <span class="file-name">${this.state.mappedFile?.name || 'No file selected'}</span>
                </div>

                <button class="btn primary" id="runInsights" ${!this.state.mappedFile ? 'disabled' : ''}>
                    Generate Insights
                </button>
            </div>
        `;
    }

    renderRecommendations() {
        const recs = this.state.result.recommendations || [];

        return `
            <div class="results-section">
                <div class="results-header">
                    <h3>Mapping Results</h3>
                    <div class="stats">
                        <span>Total: ${recs.length}</span>
                        <span>Selected: ${this.state.selectedIndices.length}</span>
                    </div>
                </div>

                <div class="select-actions">
                    <button class="btn small" id="selectAll">Select All</button>
                    <button class="btn small" id="selectNone">Select None</button>
                    <button class="btn small" id="selectHighConf">Select High Confidence (≥85%)</button>
                </div>

                <div class="recommendations-list">
                    ${recs.map((rec, idx) => `
                        <div class="recommendation ${this.state.selectedIndices.includes(idx) ? 'selected' : ''}">
                            <input type="checkbox" data-index="${idx}" ${this.state.selectedIndices.includes(idx) ? 'checked' : ''}>
                            <div class="rec-content">
                                <div class="question-num">${rec.question_num}</div>
                                <div class="question-text">${this.truncate(rec.question_text, 150)}</div>
                                <div class="mapping">
                                    <span class="label">Mapped to:</span>
                                    <span class="value">${rec.recommended_mapping}</span>
                                </div>
                                <div class="confidence ${this.getConfidenceClass(rec.confidence)}">
                                    ${Math.round(rec.confidence * 100)}%
                                </div>
                            </div>
                        </div>
                    `).join('')}
                </div>

                <div class="actions">
                    <button class="btn secondary" id="resetResults">Start Over</button>
                    <button class="btn primary" id="applyChanges" ${this.state.selectedIndices.length === 0 ? 'disabled' : ''}>
                        Apply & Download
                    </button>
                </div>
            </div>
        `;
    }

    renderRatings() {
        const ratings = this.state.result.ratings || [];
        const summary = this.state.result.summary || {};

        return `
            <div class="results-section">
                <div class="results-header">
                    <h3>Rating Results</h3>
                </div>

                <div class="summary-stats">
                    <div class="stat correct">
                        <span class="num">${summary.correct || 0}</span>
                        <span class="label">Correct</span>
                    </div>
                    <div class="stat partial">
                        <span class="num">${summary.partially_correct || 0}</span>
                        <span class="label">Partial</span>
                    </div>
                    <div class="stat incorrect">
                        <span class="num">${summary.incorrect || 0}</span>
                        <span class="label">Incorrect</span>
                    </div>
                </div>

                <div class="ratings-list">
                    ${ratings.map((r, idx) => `
                        <div class="rating-item ${r.rating}">
                            <div class="rating-badge">${r.rating.replace('_', ' ')}</div>
                            <div class="question-num">${r.question_num}</div>
                            <div class="question-text">${this.truncate(r.question_text, 100)}</div>
                            <div class="current-mapping">Current: ${JSON.stringify(r.existing_mapping)}</div>
                            ${r.suggested_mapping ? `<div class="suggested">Suggested: ${r.suggested_mapping}</div>` : ''}
                        </div>
                    `).join('')}
                </div>

                <div class="actions">
                    <button class="btn secondary" id="resetResults">Start Over</button>
                </div>
            </div>
        `;
    }

    renderCharts() {
        const charts = this.state.result.charts || {};

        return `
            <div class="charts-section">
                <h3>Insight Charts</h3>

                <div class="charts-grid">
                    ${Object.entries(charts).map(([name, url]) => `
                        <div class="chart-item">
                            <img src="${this.apiBase}${url}" alt="${name}" loading="lazy">
                            <span class="chart-name">${name.replace(/_/g, ' ')}</span>
                        </div>
                    `).join('')}
                </div>

                <div class="actions">
                    <button class="btn secondary" id="resetResults">Start Over</button>
                </div>
            </div>
        `;
    }

    // ==========================================
    // STYLES
    // ==========================================

    getStyles() {
        return `
            :host {
                display: block;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            }

            .curriculum-mapper {
                background: #fff;
                border-radius: 8px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                overflow: hidden;
            }

            .curriculum-mapper.dark {
                background: #1a1a2e;
                color: #eee;
            }

            .header {
                background: linear-gradient(135deg, #00a8cc, #00d4aa);
                color: white;
                padding: 20px;
            }

            .header h2 {
                margin: 0 0 15px 0;
                font-size: 1.5rem;
            }

            .mode-tabs {
                display: flex;
                gap: 10px;
            }

            .tab {
                background: rgba(255,255,255,0.2);
                border: none;
                color: white;
                padding: 8px 16px;
                border-radius: 4px;
                cursor: pointer;
                font-size: 0.9rem;
                transition: all 0.2s;
            }

            .tab:hover {
                background: rgba(255,255,255,0.3);
            }

            .tab.active {
                background: white;
                color: #00a8cc;
            }

            .content {
                padding: 20px;
            }

            .upload-section h3 {
                margin: 0 0 20px 0;
                color: #333;
            }

            .dark .upload-section h3 {
                color: #eee;
            }

            .file-input {
                margin-bottom: 15px;
            }

            .file-input label {
                display: block;
                margin-bottom: 5px;
                font-weight: 500;
                color: #555;
            }

            .dark .file-input label {
                color: #ccc;
            }

            .file-input input[type="file"] {
                width: 100%;
                padding: 10px;
                border: 2px dashed #ddd;
                border-radius: 4px;
                cursor: pointer;
            }

            .file-name {
                display: block;
                margin-top: 5px;
                font-size: 0.85rem;
                color: #888;
            }

            .form-group {
                margin-bottom: 15px;
            }

            .form-group label {
                display: block;
                margin-bottom: 5px;
                font-weight: 500;
            }

            .form-group select {
                width: 100%;
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 1rem;
            }

            .btn {
                padding: 12px 24px;
                border: none;
                border-radius: 4px;
                font-size: 1rem;
                cursor: pointer;
                transition: all 0.2s;
            }

            .btn.primary {
                background: #00a8cc;
                color: white;
            }

            .btn.primary:hover:not(:disabled) {
                background: #0090b0;
            }

            .btn.secondary {
                background: #eee;
                color: #333;
            }

            .btn.small {
                padding: 6px 12px;
                font-size: 0.85rem;
            }

            .btn:disabled {
                opacity: 0.5;
                cursor: not-allowed;
            }

            .loading {
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background: rgba(0,0,0,0.7);
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                color: white;
                z-index: 1000;
            }

            .spinner {
                width: 40px;
                height: 40px;
                border: 4px solid rgba(255,255,255,0.3);
                border-top-color: white;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin-bottom: 10px;
            }

            @keyframes spin {
                to { transform: rotate(360deg); }
            }

            .error {
                background: #ff6b6b;
                color: white;
                padding: 10px 20px;
                margin: 10px 20px;
                border-radius: 4px;
            }

            .results-section {
                padding: 10px;
            }

            .results-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-bottom: 15px;
            }

            .select-actions {
                display: flex;
                gap: 10px;
                margin-bottom: 15px;
            }

            .recommendations-list {
                max-height: 400px;
                overflow-y: auto;
            }

            .recommendation {
                display: flex;
                gap: 10px;
                padding: 10px;
                border: 1px solid #eee;
                border-radius: 4px;
                margin-bottom: 10px;
                transition: all 0.2s;
            }

            .recommendation.selected {
                background: #e8f8f5;
                border-color: #00d4aa;
            }

            .rec-content {
                flex: 1;
            }

            .question-num {
                font-weight: bold;
                color: #00a8cc;
            }

            .question-text {
                font-size: 0.9rem;
                color: #555;
                margin: 5px 0;
            }

            .mapping {
                font-size: 0.85rem;
            }

            .mapping .label {
                color: #888;
            }

            .mapping .value {
                font-weight: 500;
                color: #333;
            }

            .confidence {
                display: inline-block;
                padding: 2px 8px;
                border-radius: 4px;
                font-size: 0.8rem;
                font-weight: bold;
            }

            .confidence.high {
                background: #d4edda;
                color: #155724;
            }

            .confidence.medium {
                background: #fff3cd;
                color: #856404;
            }

            .confidence.low {
                background: #f8d7da;
                color: #721c24;
            }

            .summary-stats {
                display: flex;
                gap: 20px;
                margin-bottom: 20px;
            }

            .stat {
                text-align: center;
                padding: 15px 25px;
                border-radius: 8px;
            }

            .stat .num {
                display: block;
                font-size: 2rem;
                font-weight: bold;
            }

            .stat.correct {
                background: #d4edda;
                color: #155724;
            }

            .stat.partial {
                background: #fff3cd;
                color: #856404;
            }

            .stat.incorrect {
                background: #f8d7da;
                color: #721c24;
            }

            .rating-item {
                padding: 10px;
                border-radius: 4px;
                margin-bottom: 10px;
            }

            .rating-item.correct {
                background: #d4edda;
            }

            .rating-item.partially_correct {
                background: #fff3cd;
            }

            .rating-item.incorrect {
                background: #f8d7da;
            }

            .rating-badge {
                display: inline-block;
                padding: 2px 8px;
                border-radius: 4px;
                font-size: 0.75rem;
                text-transform: uppercase;
                font-weight: bold;
                background: rgba(0,0,0,0.1);
                margin-bottom: 5px;
            }

            .charts-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
            }

            .chart-item {
                text-align: center;
            }

            .chart-item img {
                max-width: 100%;
                border-radius: 4px;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }

            .chart-name {
                display: block;
                margin-top: 10px;
                font-size: 0.9rem;
                color: #666;
                text-transform: capitalize;
            }

            .actions {
                display: flex;
                gap: 10px;
                justify-content: flex-end;
                margin-top: 20px;
                padding-top: 20px;
                border-top: 1px solid #eee;
            }
        `;
    }

    // ==========================================
    // EVENT HANDLING
    // ==========================================

    attachEventListeners() {
        const shadow = this.shadowRoot;

        // Mode tabs
        shadow.querySelectorAll('.tab').forEach(tab => {
            tab.addEventListener('click', (e) => {
                this.state.mode = e.target.dataset.mode;
                this.state.result = null;
                this.state.selectedIndices = [];
                this.render();
            });
        });

        // File inputs
        const questionFile = shadow.getElementById('questionFile');
        if (questionFile) {
            questionFile.addEventListener('change', (e) => {
                this.state.questionFile = e.target.files[0];
                this.render();
            });
        }

        const referenceFile = shadow.getElementById('referenceFile');
        if (referenceFile) {
            referenceFile.addEventListener('change', (e) => {
                this.state.referenceFile = e.target.files[0];
                this.render();
            });
        }

        const mappedFile = shadow.getElementById('mappedFile');
        if (mappedFile) {
            mappedFile.addEventListener('change', (e) => {
                this.state.mappedFile = e.target.files[0];
                this.render();
            });
        }

        // Dimension select
        const dimension = shadow.getElementById('dimension');
        if (dimension) {
            dimension.addEventListener('change', (e) => {
                this.dimension = e.target.value;
            });
        }

        // Action buttons
        const runMapping = shadow.getElementById('runMapping');
        if (runMapping) {
            runMapping.addEventListener('click', () => this.runMapping());
        }

        const runRating = shadow.getElementById('runRating');
        if (runRating) {
            runRating.addEventListener('click', () => this.runRating());
        }

        const runInsights = shadow.getElementById('runInsights');
        if (runInsights) {
            runInsights.addEventListener('click', () => this.runInsights());
        }

        const applyChanges = shadow.getElementById('applyChanges');
        if (applyChanges) {
            applyChanges.addEventListener('click', () => this.applyChanges());
        }

        const resetResults = shadow.getElementById('resetResults');
        if (resetResults) {
            resetResults.addEventListener('click', () => {
                this.state.result = null;
                this.state.selectedIndices = [];
                this.render();
            });
        }

        // Selection buttons
        const selectAll = shadow.getElementById('selectAll');
        if (selectAll) {
            selectAll.addEventListener('click', () => {
                this.state.selectedIndices = this.state.result.recommendations.map((_, i) => i);
                this.render();
            });
        }

        const selectNone = shadow.getElementById('selectNone');
        if (selectNone) {
            selectNone.addEventListener('click', () => {
                this.state.selectedIndices = [];
                this.render();
            });
        }

        const selectHighConf = shadow.getElementById('selectHighConf');
        if (selectHighConf) {
            selectHighConf.addEventListener('click', () => {
                this.state.selectedIndices = this.state.result.recommendations
                    .map((r, i) => r.confidence >= 0.85 ? i : -1)
                    .filter(i => i >= 0);
                this.render();
            });
        }

        // Checkboxes
        shadow.querySelectorAll('.recommendation input[type="checkbox"]').forEach(cb => {
            cb.addEventListener('change', (e) => {
                const idx = parseInt(e.target.dataset.index);
                if (e.target.checked) {
                    if (!this.state.selectedIndices.includes(idx)) {
                        this.state.selectedIndices.push(idx);
                    }
                } else {
                    this.state.selectedIndices = this.state.selectedIndices.filter(i => i !== idx);
                }
                this.render();
            });
        });
    }

    // ==========================================
    // API CALLS
    // ==========================================

    async apiCall(endpoint, options = {}) {
        const headers = {
            ...options.headers
        };

        if (this.authToken) {
            headers['Authorization'] = `Bearer ${this.authToken}`;
        }

        const response = await fetch(`${this.apiBase}${endpoint}`, {
            ...options,
            headers
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'API request failed');
        }

        return response.json();
    }

    async runMapping() {
        this.state.loading = true;
        this.state.error = null;
        this.render();

        try {
            // Upload files
            const formData = new FormData();
            formData.append('question_file', this.state.questionFile);
            formData.append('reference_file', this.state.referenceFile);

            const uploadResult = await this.apiCall('/api/upload', {
                method: 'POST',
                body: formData
            });

            // Run mapping
            const result = await this.apiCall('/api/run-audit-efficient', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    question_file: uploadResult.question_file,
                    reference_file: uploadResult.reference_file,
                    dimension: this.dimension,
                    batch_size: 5
                })
            });

            this.state.result = result;
            this.state.selectedIndices = result.recommendations
                .map((r, i) => r.confidence >= 0.85 ? i : -1)
                .filter(i => i >= 0);

        } catch (error) {
            this.state.error = error.message;
        } finally {
            this.state.loading = false;
            this.render();
        }
    }

    async runRating() {
        this.state.loading = true;
        this.state.error = null;
        this.render();

        try {
            // Upload files
            const formData = new FormData();
            formData.append('mapped_file', this.state.mappedFile);
            formData.append('reference_file', this.state.referenceFile);

            const uploadResult = await this.apiCall('/api/upload-mapped', {
                method: 'POST',
                body: formData
            });

            // Run rating
            const result = await this.apiCall('/api/rate-mappings', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    mapped_file: uploadResult.mapped_file,
                    reference_file: uploadResult.reference_file,
                    dimension: this.dimension,
                    batch_size: 5
                })
            });

            this.state.result = result;

        } catch (error) {
            this.state.error = error.message;
        } finally {
            this.state.loading = false;
            this.render();
        }
    }

    async runInsights() {
        this.state.loading = true;
        this.state.error = null;
        this.render();

        try {
            // Upload file
            const formData = new FormData();
            formData.append('mapped_file', this.state.mappedFile);

            const uploadResult = await this.apiCall('/api/upload-mapped', {
                method: 'POST',
                body: formData
            });

            // Generate insights
            const result = await this.apiCall('/api/generate-insights', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    mapped_file: uploadResult.mapped_file
                })
            });

            this.state.result = result;

        } catch (error) {
            this.state.error = error.message;
        } finally {
            this.state.loading = false;
            this.render();
        }
    }

    async applyChanges() {
        this.state.loading = true;
        this.state.error = null;
        this.render();

        try {
            const result = await this.apiCall('/api/apply-changes', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    question_file: this.state.questionFile.name,
                    recommendations: this.state.result.recommendations,
                    selected_indices: this.state.selectedIndices,
                    dimension: this.dimension
                })
            });

            // Download file
            window.open(`${this.apiBase}${result.download_url}`, '_blank');

        } catch (error) {
            this.state.error = error.message;
        } finally {
            this.state.loading = false;
            this.render();
        }
    }

    // ==========================================
    // UTILITIES
    // ==========================================

    truncate(text, maxLength) {
        if (!text) return '';
        return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
    }

    getConfidenceClass(confidence) {
        if (confidence >= 0.85) return 'high';
        if (confidence >= 0.7) return 'medium';
        return 'low';
    }

    updateTheme() {
        const container = this.shadowRoot.querySelector('.curriculum-mapper');
        if (container) {
            container.classList.remove('light', 'dark');
            container.classList.add(this.theme);
        }
    }
}

// Register the custom element
customElements.define('curriculum-mapper', CurriculumMapper);
