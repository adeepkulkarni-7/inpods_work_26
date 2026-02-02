// Mode C: Insights & Visualization - Standalone App
// Visualize mapping distribution, confidence scores, and curriculum coverage gaps

let uploadedFiles = { mappedFile: null, referenceFile: null };

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // App is ready
});

async function generateInsights() {
    const mappedFile = document.getElementById('mappedFile').files[0];

    if (!mappedFile) {
        showStatus('Please select a mapped file', 'error');
        return;
    }

    // Get selected dimensions (empty array means auto-detect)
    const selectedDimensions = getSelectedDimensions('dimensions');

    const formData = new FormData();
    formData.append('mapped_file', mappedFile);

    const referenceFile = document.getElementById('referenceFile').files[0];
    if (referenceFile) {
        formData.append('reference_file', referenceFile);
    }

    try {
        // First upload the files
        const uploadResponse = await fetch(`${API_URL}/upload-mapped`, { method: 'POST', body: formData });
        const uploadData = await uploadResponse.json();

        if (!uploadResponse.ok) {
            showStatus(`Error: ${uploadData.error}`, 'error');
            return;
        }

        uploadedFiles.mappedFile = uploadData.mapped_file;
        uploadedFiles.referenceFile = uploadData.reference_file;

        // Create task description
        const dimDesc = selectedDimensions.length > 0
            ? selectedDimensions.map(d => d.replace('_', ' ')).join(', ')
            : 'auto-detect';
        const taskId = taskManager.create('insights', `Generating insights (${dimDesc}) from ${mappedFile.name}`);

        document.getElementById('uploadSection').classList.add('hidden');
        document.getElementById('loading').classList.remove('hidden');

        // Run async with task tracking
        const task = await taskManager.run(taskId, async (updateProgress) => {
            const response = await fetch(`${API_URL}/generate-insights`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    mapped_file: uploadedFiles.mappedFile,
                    reference_file: uploadedFiles.referenceFile,
                    dimensions: selectedDimensions
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Insights generation failed');
            }

            return await response.json();
        });

        document.getElementById('loading').classList.add('hidden');

        if (task.state === TaskState.COMPLETED) {
            displayInsights(task.result);
            document.getElementById('insightsSection').classList.remove('hidden');
        } else {
            document.getElementById('uploadSection').classList.remove('hidden');
        }
    } catch (error) {
        document.getElementById('loading').classList.add('hidden');
        document.getElementById('uploadSection').classList.remove('hidden');
        showStatus(`Error: ${error.message}`, 'error');
    }
}

function displayInsights(data) {
    // Summary stats (kept minimal since executive_summary chart has details)
    const statsDiv = document.getElementById('summaryStats');
    statsDiv.innerHTML = `
        <div class="stat-card">
            <div class="stat-value">${data.summary.total_questions}</div>
            <div class="stat-label">Total Questions</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">${data.summary.topics_covered}</div>
            <div class="stat-label">Items Covered</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">${Math.round(data.summary.average_confidence * 100)}%</div>
            <div class="stat-label">Avg Confidence</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">${(data.detected_dimensions || []).length}</div>
            <div class="stat-label">Dimensions Analyzed</div>
        </div>
    `;

    // Charts - New infographic style with dimension separation
    const chartsDiv = document.getElementById('chartsGrid');
    chartsDiv.innerHTML = '';

    // Display detected dimensions
    const detectedDims = data.detected_dimensions || [];
    if (detectedDims.length > 0) {
        const dimBadges = document.createElement('div');
        dimBadges.className = 'dimension-badges';
        dimBadges.innerHTML = `
            <span style="color: #64748b; font-size: 14px; margin-right: 5px;">Dimensions:</span>
            ${detectedDims.map(d => `<span class="dimension-badge">${formatDimensionName(d)}</span>`).join('')}
        `;
        chartsDiv.appendChild(dimBadges);
    }

    // Executive Summary and Confidence Gauge (global charts)
    const globalCharts = [
        { key: 'executive_summary', fullWidth: true, label: 'Executive Summary' },
        { key: 'confidence_gauge', fullWidth: false, label: 'Overall Confidence' }
    ];

    globalCharts.forEach(chart => {
        if (data.charts[chart.key]) {
            const container = document.createElement('div');
            container.className = chart.fullWidth ? 'chart-container full-width' : 'chart-container';
            container.innerHTML = `<img src="${BASE_URL}${data.charts[chart.key]}" alt="${chart.label}">`;
            chartsDiv.appendChild(container);
        }
    });

    // Per-dimension charts (coverage heatmap and gap analysis)
    detectedDims.forEach(dim => {
        const dimLabel = formatDimensionName(dim);

        // Section header for this dimension
        const sectionHeader = document.createElement('div');
        sectionHeader.className = 'dimension-section-header';
        sectionHeader.textContent = `${dimLabel} Analysis`;
        chartsDiv.appendChild(sectionHeader);

        // Coverage heatmap for this dimension
        const heatmapKey = `coverage_heatmap_${dim}`;
        if (data.charts[heatmapKey]) {
            const container = document.createElement('div');
            container.className = 'chart-container';
            container.innerHTML = `<img src="${BASE_URL}${data.charts[heatmapKey]}" alt="${dimLabel} Coverage">`;
            chartsDiv.appendChild(container);
        }

        // Gap analysis for this dimension
        const gapKey = `gap_analysis_${dim}`;
        if (data.charts[gapKey]) {
            const container = document.createElement('div');
            container.className = 'chart-container';
            container.innerHTML = `<img src="${BASE_URL}${data.charts[gapKey]}" alt="${dimLabel} Gap Analysis">`;
            chartsDiv.appendChild(container);
        }
    });

    // Coverage Tables - one per dimension
    const coverageTables = data.coverage_tables || {};
    const tableSection = document.getElementById('coverageTableSection');
    const tableBody = document.getElementById('coverageTableBody');

    // Clear existing content
    tableBody.innerHTML = '';

    // If we have per-dimension tables, show them with headers
    if (Object.keys(coverageTables).length > 0) {
        Object.entries(coverageTables).forEach(([dim, tableData]) => {
            if (tableData && tableData.length > 0) {
                // Dimension header row
                const headerRow = document.createElement('tr');
                headerRow.className = 'dimension-table-header';
                headerRow.innerHTML = `<td colspan="4" style="background: #1e293b; color: white; font-weight: 600; padding: 12px 16px;">${formatDimensionName(dim)}</td>`;
                tableBody.appendChild(headerRow);

                // Data rows for this dimension
                tableData.forEach(item => {
                    const row = document.createElement('tr');
                    let rowClass = '';
                    if (item.count === 0) rowClass = 'gap-row';
                    else if (item.count <= 2) rowClass = 'low-row';
                    row.className = rowClass;

                    let barClass = 'high';
                    if (item.percentage < 5) barClass = 'low';
                    else if (item.percentage < 15) barClass = 'medium';
                    const barWidth = Math.min(item.percentage * 2, 60);

                    row.innerHTML = `
                        <td class="code-cell">${item.code}</td>
                        <td class="definition-cell">${item.definition || '-'}</td>
                        <td class="count-cell">${item.count}</td>
                        <td class="percentage-cell">
                            ${item.percentage}%
                            <span class="percentage-bar ${barClass}" style="width: ${barWidth}px;"></span>
                        </td>
                    `;
                    tableBody.appendChild(row);
                });
            }
        });
        tableSection.classList.remove('hidden');
    } else if (data.coverage_table && data.coverage_table.length > 0) {
        // Fallback to single coverage table (backward compatibility)
        data.coverage_table.forEach(item => {
            const row = document.createElement('tr');
            let rowClass = '';
            if (item.count === 0) rowClass = 'gap-row';
            else if (item.count <= 2) rowClass = 'low-row';
            row.className = rowClass;

            let barClass = 'high';
            if (item.percentage < 5) barClass = 'low';
            else if (item.percentage < 15) barClass = 'medium';
            const barWidth = Math.min(item.percentage * 2, 60);

            row.innerHTML = `
                <td class="code-cell">${item.code}</td>
                <td class="definition-cell">${item.definition || '-'}</td>
                <td class="count-cell">${item.count}</td>
                <td class="percentage-cell">
                    ${item.percentage}%
                    <span class="percentage-bar ${barClass}" style="width: ${barWidth}px;"></span>
                </td>
            `;
            tableBody.appendChild(row);
        });
        tableSection.classList.remove('hidden');
    } else {
        tableSection.classList.add('hidden');
    }
}

function startOver() {
    // Reset all state
    uploadedFiles = { mappedFile: null, referenceFile: null };
    document.getElementById('mappedFile').value = '';
    document.getElementById('referenceFile').value = '';
    document.getElementById('insightsSection').classList.add('hidden');
    document.getElementById('loading').classList.add('hidden');
    document.getElementById('uploadSection').classList.remove('hidden');
    document.getElementById('summaryStats').innerHTML = '';
    document.getElementById('chartsGrid').innerHTML = '';
    document.getElementById('coverageTableBody').innerHTML = '';
    // Clear dimension checkboxes
    document.querySelectorAll('#dimensions input[type="checkbox"]').forEach(cb => cb.checked = false);
}
