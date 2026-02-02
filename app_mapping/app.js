// Mode A: Question Mapping - Standalone App
// Map unmapped questions to curriculum dimensions

let uploadedFiles = { questionFile: null, referenceFile: null };
let recommendations = [];
let referenceDefinitions = {};
let currentDimensions = [];
let selectedIndices = [];
let uploadMetadata = null;
let pendingSaveData = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // App is ready
});

async function uploadAndPreview() {
    const questionFile = document.getElementById('questionFile').files[0];
    const referenceFile = document.getElementById('referenceFile').files[0];

    if (!questionFile || !referenceFile) {
        showStatus('Please select both files', 'error');
        return;
    }

    const formData = new FormData();
    formData.append('question_file', questionFile);
    formData.append('reference_file', referenceFile);

    try {
        const uploadResponse = await fetch(`${API_URL}/upload`, { method: 'POST', body: formData });
        const uploadData = await uploadResponse.json();

        if (!uploadResponse.ok) {
            showStatus(`Error: ${uploadData.error}`, 'error');
            return;
        }

        uploadedFiles.questionFile = uploadData.question_file;
        uploadedFiles.referenceFile = uploadData.reference_file;
        uploadMetadata = {
            question: uploadData.question_metadata,
            reference: uploadData.reference_metadata
        };

        // Display file overview
        displayFileOverview(uploadData);

        document.getElementById('uploadSection').classList.add('hidden');
        document.getElementById('fileOverview').classList.remove('hidden');

        showStatus(`Files uploaded successfully`, 'success');

    } catch (error) {
        showStatus(`Error: ${error.message}`, 'error');
    }
}

function displayFileOverview(data) {
    // Question Overview
    const qMeta = data.question_metadata || {};
    let qHtml = `
        <div class="overview-stats">
            <div class="overview-stat">
                <div class="overview-stat-value">${qMeta.total_questions || data.question_count || 0}</div>
                <div class="overview-stat-label">Questions</div>
            </div>
            <div class="overview-stat">
                <div class="overview-stat-value">${(qMeta.columns || []).length}</div>
                <div class="overview-stat-label">Columns</div>
            </div>
        </div>
    `;

    if (qMeta.sample_questions && qMeta.sample_questions.length > 0) {
        qHtml += `<div class="sample-questions"><strong>Sample Questions:</strong>`;
        qMeta.sample_questions.forEach(q => {
            qHtml += `
                <div class="sample-question">
                    <div class="sample-question-num">Q${q.number}</div>
                    <div class="sample-question-text">${q.text}</div>
                </div>
            `;
        });
        qHtml += `</div>`;
    }

    document.getElementById('questionOverview').innerHTML = qHtml;

    // Reference Overview
    const rMeta = data.reference_metadata || {};
    let rHtml = `<div class="overview-stats">`;

    const totalItems =
        (rMeta.competencies || []).length +
        (rMeta.objectives || []).length +
        (rMeta.skills || []).length +
        (rMeta.topics || []).length +
        (rMeta.nmc_competencies || []).length +
        (rMeta.blooms || []).length +
        (rMeta.complexity || []).length;

    rHtml += `
        <div class="overview-stat">
            <div class="overview-stat-value">${totalItems}</div>
            <div class="overview-stat-label">Total Items</div>
        </div>
    `;

    if (rMeta.detected_type) {
        rHtml += `
            <div class="overview-stat">
                <div class="overview-stat-value" style="font-size: 16px;">${rMeta.detected_type.replace('_', ' ').toUpperCase()}</div>
                <div class="overview-stat-label">Detected Type</div>
            </div>
        `;
    }
    rHtml += `</div>`;

    rHtml += `<ul class="curriculum-list">`;

    // NMC Competencies
    if (rMeta.nmc_competencies && rMeta.nmc_competencies.length > 0) {
        rHtml += `<div class="curriculum-type-header">NMC Competencies <span class="curriculum-count">${rMeta.nmc_competencies.length}</span></div>`;
        rMeta.nmc_competencies.forEach(item => {
            rHtml += `
                <li class="curriculum-item nmc">
                    <span class="curriculum-id">${item.id}</span>
                    <span class="curriculum-desc">${item.description}</span>
                </li>
            `;
        });
    }

    // Competencies
    if (rMeta.competencies && rMeta.competencies.length > 0) {
        rHtml += `<div class="curriculum-type-header">Competencies <span class="curriculum-count">${rMeta.competencies.length}</span></div>`;
        rMeta.competencies.forEach(item => {
            rHtml += `
                <li class="curriculum-item competency">
                    <span class="curriculum-id">${item.id}</span>
                    <span class="curriculum-desc">${item.description}</span>
                </li>
            `;
        });
    }

    // Objectives
    if (rMeta.objectives && rMeta.objectives.length > 0) {
        rHtml += `<div class="curriculum-type-header">Objectives <span class="curriculum-count">${rMeta.objectives.length}</span></div>`;
        rMeta.objectives.forEach(item => {
            rHtml += `
                <li class="curriculum-item objective">
                    <span class="curriculum-id">${item.id}</span>
                    <span class="curriculum-desc">${item.description}</span>
                </li>
            `;
        });
    }

    // Skills
    if (rMeta.skills && rMeta.skills.length > 0) {
        rHtml += `<div class="curriculum-type-header">Skills <span class="curriculum-count">${rMeta.skills.length}</span></div>`;
        rMeta.skills.forEach(item => {
            rHtml += `
                <li class="curriculum-item skill">
                    <span class="curriculum-id">${item.id}</span>
                    <span class="curriculum-desc">${item.description}</span>
                </li>
            `;
        });
    }

    // Topics
    if (rMeta.topics && rMeta.topics.length > 0) {
        rHtml += `<div class="curriculum-type-header">Topic Areas <span class="curriculum-count">${rMeta.topics.length}</span></div>`;
        rMeta.topics.forEach(item => {
            rHtml += `
                <li class="curriculum-item topic">
                    <span class="curriculum-id">${item.topic}</span>
                    ${item.subtopics ? `<span class="curriculum-desc">${item.subtopics}</span>` : ''}
                </li>
            `;
        });
    }

    // Blooms Levels
    if (rMeta.blooms && rMeta.blooms.length > 0) {
        rHtml += `<div class="curriculum-type-header">Blooms Levels <span class="curriculum-count">${rMeta.blooms.length}</span></div>`;
        rMeta.blooms.forEach(item => {
            rHtml += `
                <li class="curriculum-item blooms">
                    <span class="curriculum-id">${item.id}</span>
                    <span class="curriculum-desc">${item.description}</span>
                </li>
            `;
        });
    }

    // Complexity Levels
    if (rMeta.complexity && rMeta.complexity.length > 0) {
        rHtml += `<div class="curriculum-type-header">Complexity Levels <span class="curriculum-count">${rMeta.complexity.length}</span></div>`;
        rMeta.complexity.forEach(item => {
            rHtml += `
                <li class="curriculum-item complexity">
                    <span class="curriculum-id">${item.id}</span>
                    <span class="curriculum-desc">${item.description}</span>
                </li>
            `;
        });
    }

    rHtml += `</ul>`;

    if (totalItems === 0) {
        rHtml = `<p style="color: #64748b; text-align: center; padding: 20px;">No curriculum items detected in reference file. Please ensure the file contains competencies (C1-C6), objectives (O1-O6), skills (S1-S5), NMC codes (MI1.1, etc.), Blooms levels (KL1-KL6), or complexity levels (Easy/Medium/Hard).</p>`;
    }

    document.getElementById('referenceOverview').innerHTML = rHtml;
}

function backToUpload() {
    document.getElementById('fileOverview').classList.add('hidden');
    document.getElementById('uploadSection').classList.remove('hidden');
}

async function runAudit() {
    // Get selected dimensions from checkboxes
    const dimensions = getSelectedDimensions('dimensions');

    // Validate at least one dimension selected
    if (dimensions.length === 0) {
        document.getElementById('dimensionError').classList.add('show');
        showStatus('Please select at least one dimension to map', 'error');
        return;
    }
    document.getElementById('dimensionError').classList.remove('show');

    // Get question count and dimension names for task description
    const qCount = uploadMetadata?.question?.total_questions || '?';
    const dimNames = dimensions.map(d => d.replace('_', ' ')).join(', ');

    // Create task (non-blocking)
    const taskId = taskManager.create('mapping', `Mapping ${qCount} questions to ${dimNames}`);

    // Show loading but allow interaction
    document.getElementById('fileOverview').classList.add('hidden');
    document.getElementById('loading').classList.remove('hidden');

    // Run async with task tracking
    const task = await taskManager.run(taskId, async (updateProgress) => {
        const useEfficient = document.getElementById('efficientMode').checked;
        const batchSize = parseInt(document.getElementById('batchSize').value);
        const endpoint = useEfficient ? '/run-audit-efficient' : '/run-audit';

        const response = await fetch(`${API_URL}${endpoint}`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                question_file: uploadedFiles.questionFile,
                reference_file: uploadedFiles.referenceFile,
                dimensions: dimensions,
                dimension: dimensions[0],
                batch_size: batchSize
            })
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || 'Audit failed');
        }

        return await response.json();
    });

    document.getElementById('loading').classList.add('hidden');

    if (task.state === TaskState.COMPLETED) {
        const data = task.result;
        recommendations = data.recommendations;
        referenceDefinitions = data.reference_definitions || {};
        currentDimensions = dimensions;
        displayRecommendations(recommendations, referenceDefinitions, dimensions);

        if (data.token_usage) {
            displayTokenUsage(data.token_usage);
        }

        document.getElementById('recommendationsSection').classList.remove('hidden');
    } else {
        document.getElementById('fileOverview').classList.remove('hidden');
    }
}

function displayRecommendations(recs, definitions = {}, dimensions = []) {
    const tbody = document.getElementById('recommendationsBody');
    const thead = document.getElementById('tableHeader');
    tbody.innerHTML = '';
    document.getElementById('totalCount').textContent = recs.length;

    // Build dynamic column headers based on dimensions
    const dimensionLabels = {
        'competency': 'Competency',
        'objective': 'Objective',
        'skill': 'Skill',
        'nmc_competency': 'NMC',
        'area_topics': 'Topic',
        'blooms': 'Blooms',
        'complexity': 'Complexity'
    };

    // Update table headers for multi-dimension mode
    if (dimensions.length > 1) {
        let headerHtml = `
            <th style="width: 40px;"><input type="checkbox" class="checkbox" id="selectAllCheckbox" onchange="toggleSelectAll()"></th>
            <th style="width: 80px;">Q#</th>
            <th style="width: 300px;">Question</th>
        `;
        dimensions.forEach(dim => {
            headerHtml += `<th style="width: 100px;">${dimensionLabels[dim] || dim}</th>`;
        });
        headerHtml += `
            <th style="width: 80px;">Conf</th>
            <th>Justification</th>
        `;
        thead.innerHTML = headerHtml;
    }

    recs.forEach((rec, index) => {
        const row = document.createElement('tr');
        const confidence = rec.confidence || 0;
        let confidenceClass = 'confidence-low';
        if (confidence >= 0.85) confidenceClass = 'confidence-high';
        else if (confidence >= 0.70) confidenceClass = 'confidence-medium';

        // Build row content based on dimensions
        if (dimensions.length > 1) {
            // Multi-dimension mode - show each dimension in separate column
            let rowHtml = `
                <td><input type="checkbox" class="checkbox" data-index="${index}" onchange="updateSelection()"></td>
                <td>${rec.question_num}</td>
                <td class="question-text">
                    <div class="question-text-full">${rec.question_text || ''}</div>
                </td>
            `;

            dimensions.forEach(dim => {
                let code = '';
                if (dim === 'area_topics') {
                    code = rec.mapped_topic || rec[`mapped_${dim}_topic`] || '';
                } else {
                    code = rec[`mapped_${dim}`] || '';
                }
                const def = definitions[code] || '';
                rowHtml += `<td><strong title="${def}">${code}</strong></td>`;
            });

            rowHtml += `
                <td><span class="confidence-badge ${confidenceClass}">${Math.round(confidence * 100)}%</span></td>
                <td class="justification">${rec.justification || ''}</td>
            `;
            row.innerHTML = rowHtml;
        } else {
            // Single dimension mode - original display
            const mappingCode = rec.recommended_mapping || rec.mapped_id || rec.mapped_competency || rec.mapped_objective || '';
            const definition = definitions[mappingCode] || definitions[rec.mapped_id] || '';

            row.innerHTML = `
                <td><input type="checkbox" class="checkbox" data-index="${index}" onchange="updateSelection()"></td>
                <td>${rec.question_num}</td>
                <td class="question-text">
                    <div class="question-text-full">${rec.question_text || ''}</div>
                </td>
                <td><strong>${mappingCode}</strong></td>
                <td class="definition-text">${definition}</td>
                <td><span class="confidence-badge ${confidenceClass}">${Math.round(confidence * 100)}%</span></td>
                <td class="justification">${rec.justification || ''}</td>
            `;
        }
        tbody.appendChild(row);
    });
}

function displayTokenUsage(tokenUsage) {
    document.getElementById('promptTokens').textContent = tokenUsage.prompt_tokens.toLocaleString();
    document.getElementById('completionTokens').textContent = tokenUsage.completion_tokens.toLocaleString();
    document.getElementById('totalTokens').textContent = tokenUsage.total_tokens.toLocaleString();
    document.getElementById('apiCalls').textContent = tokenUsage.api_calls || 0;
}

function updateSelection() {
    const checkboxes = document.querySelectorAll('#recommendationsBody input[type="checkbox"]');
    selectedIndices = [];
    checkboxes.forEach(cb => { if (cb.checked) selectedIndices.push(parseInt(cb.dataset.index)); });
    document.getElementById('selectionCount').textContent = selectedIndices.length;
}

function toggleSelectAll() {
    const selectAll = document.getElementById('selectAllCheckbox').checked;
    document.querySelectorAll('#recommendationsBody input[type="checkbox"]').forEach(cb => cb.checked = selectAll);
    updateSelection();
}

function selectAll() { document.getElementById('selectAllCheckbox').checked = true; toggleSelectAll(); }
function selectNone() { document.getElementById('selectAllCheckbox').checked = false; toggleSelectAll(); }
function selectHighConfidence() {
    document.querySelectorAll('#recommendationsBody input[type="checkbox"]').forEach((cb, i) => {
        cb.checked = recommendations[i].confidence >= 0.85;
    });
    updateSelection();
}

function saveAndDownload() {
    if (selectedIndices.length === 0) {
        showStatus('Please select at least one recommendation', 'error');
        return;
    }
    openSaveModal();
}

function openSaveModal() {
    const dimensions = getSelectedDimensions('dimensions');
    pendingSaveData = {
        recommendations: recommendations,
        dimensions: dimensions,
        dimension: dimensions[0] || 'competency'
    };
    document.getElementById('saveName').value = `Mapping_${new Date().toISOString().slice(0, 10)}`;
    document.getElementById('saveModal').classList.remove('hidden');
}

function closeSaveModal() {
    document.getElementById('saveModal').classList.add('hidden');
    pendingSaveData = null;
}

async function confirmSaveAndDownload() {
    if (!pendingSaveData) return;

    const name = document.getElementById('saveName').value.trim() || 'Unnamed Mapping';

    try {
        const response = await fetch(`${API_URL}/apply-and-save`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                question_file: uploadedFiles.questionFile,
                recommendations: pendingSaveData.recommendations,
                selected_indices: selectedIndices,
                dimensions: pendingSaveData.dimensions,
                dimension: pendingSaveData.dimension,
                name: name
            })
        });

        const data = await response.json();

        if (data.status === 'success') {
            showStatus(`Saved "${name}" to library and downloading...`, 'success');
            closeSaveModal();
            // Trigger download
            window.location.href = `${BASE_URL}${data.download_url}`;
        } else {
            showStatus(`Error: ${data.error}`, 'error');
        }
    } catch (error) {
        showStatus(`Error: ${error.message}`, 'error');
    }
}

function startOver() {
    // Reset all state
    recommendations = [];
    selectedIndices = [];
    currentDimensions = [];
    uploadedFiles = { questionFile: null, referenceFile: null };
    uploadMetadata = null;
    document.getElementById('questionFile').value = '';
    document.getElementById('referenceFile').value = '';
    document.getElementById('recommendationsSection').classList.add('hidden');
    document.getElementById('loading').classList.add('hidden');
    document.getElementById('fileOverview').classList.add('hidden');
    document.getElementById('uploadSection').classList.remove('hidden');
    document.getElementById('selectionCount').textContent = '0';
    document.getElementById('totalCount').textContent = '0';
    document.getElementById('recommendationsBody').innerHTML = '';
    document.getElementById('selectAllCheckbox').checked = false;
    document.getElementById('dimensionError').classList.remove('show');
    // Reset table header to default
    const thead = document.getElementById('tableHeader');
    thead.innerHTML = `
        <th style="width: 40px;"><input type="checkbox" class="checkbox" id="selectAllCheckbox" onchange="toggleSelectAll()"></th>
        <th style="width: 80px;">Q#</th>
        <th style="width: 350px;">Question (Full Text)</th>
        <th style="width: 120px;">Mapping Code</th>
        <th style="width: 280px;">Definition</th>
        <th style="width: 100px;">Confidence</th>
        <th>Justification</th>
    `;
}
