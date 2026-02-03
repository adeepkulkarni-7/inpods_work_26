// Mode B: Rating Validation - Standalone App
// Analyze and improve existing question-to-curriculum mappings

let uploadedFiles = { mappedFile: null, referenceFile: null };
let ratings = [];
let recommendations = [];
let referenceDefinitions = {};
let currentDimensions = [];
let selectedIndices = [];
let pendingSaveData = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    // App is ready
});

async function uploadAndRate() {
    const mappedFile = document.getElementById('mappedFile').files[0];
    const referenceFile = document.getElementById('referenceFile').files[0];

    if (!mappedFile || !referenceFile) {
        showStatus('Please select both files', 'error');
        return;
    }

    // Get selected dimensions from checkboxes
    const dimensions = getSelectedDimensions('dimensions');
    if (dimensions.length === 0) {
        document.getElementById('dimensionError').classList.add('show');
        showStatus('Please select at least one dimension to rate', 'error');
        return;
    }
    document.getElementById('dimensionError').classList.remove('show');

    const formData = new FormData();
    formData.append('mapped_file', mappedFile);
    formData.append('reference_file', referenceFile);

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

        // Get dimension names for task description
        const dimNames = dimensions.map(d => d.replace('_', ' ')).join(', ');

        // Create task for the rating operation
        const taskId = taskManager.create('rating', `Rating mappings for ${dimNames}`);

        document.getElementById('uploadSection').classList.add('hidden');
        document.getElementById('loading').classList.remove('hidden');

        // Run async with task tracking
        const task = await taskManager.run(taskId, async (updateProgress) => {
            const response = await fetch(`${API_URL}/rate-mappings`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    mapped_file: uploadedFiles.mappedFile,
                    reference_file: uploadedFiles.referenceFile,
                    dimensions: dimensions,
                    dimension: dimensions[0],
                    batch_size: parseInt(document.getElementById('batchSize').value)
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || 'Rating failed');
            }

            return await response.json();
        });

        document.getElementById('loading').classList.add('hidden');

        if (task.state === TaskState.COMPLETED) {
            const rateData = task.result;
            ratings = rateData.ratings;
            recommendations = rateData.recommendations;
            referenceDefinitions = rateData.reference_definitions || {};
            currentDimensions = dimensions;
            displayRatings(rateData, referenceDefinitions);

            if (rateData.token_usage) {
                displayTokenUsage(rateData.token_usage);
            }

            document.getElementById('ratingsSection').classList.remove('hidden');
        } else {
            document.getElementById('uploadSection').classList.remove('hidden');
        }
    } catch (error) {
        document.getElementById('loading').classList.add('hidden');
        document.getElementById('uploadSection').classList.remove('hidden');
        showStatus(`Error: ${error.message}`, 'error');
    }
}

function displayTokenUsage(tokenUsage) {
    document.getElementById('promptTokens').textContent = tokenUsage.prompt_tokens.toLocaleString();
    document.getElementById('completionTokens').textContent = tokenUsage.completion_tokens.toLocaleString();
    document.getElementById('totalTokens').textContent = tokenUsage.total_tokens.toLocaleString();
    document.getElementById('apiCalls').textContent = tokenUsage.api_calls || 0;
}

function displayRatings(data, definitions = {}) {
    document.getElementById('correctCount').textContent = data.summary.correct;
    document.getElementById('partialCount').textContent = data.summary.partially_correct;
    document.getElementById('incorrectCount').textContent = data.summary.incorrect;
    document.getElementById('needsReviewCount').textContent = recommendations.length;

    referenceDefinitions = definitions;

    const tbody = document.getElementById('ratingsBody');
    const thead = document.getElementById('tableHeader');
    tbody.innerHTML = '';

    // Check if multi-dimension mode (has dimensions array)
    const isMultiDim = data.dimensions && data.dimensions.length > 1;
    const dimensions = data.dimensions || currentDimensions || [];

    const dimensionLabels = {
        'competency': 'Comp',
        'objective': 'Obj',
        'skill': 'Skill',
        'nmc_competency': 'NMC',
        'area_topics': 'Topic',
        'blooms': 'Blooms',
        'complexity': 'Cmplx'
    };

    // Update table headers for multi-dimension mode
    if (isMultiDim) {
        let headerHtml = `
            <th style="width: 40px;"><input type="checkbox" class="checkbox" id="selectAllCheckbox" onchange="toggleSelectAll()"></th>
            <th style="width: 60px;">Q#</th>
            <th style="width: 250px;">Question</th>
        `;
        dimensions.forEach(dim => {
            headerHtml += `<th style="width: 120px;">${dimensionLabels[dim] || dim}<br><small>Curr → Sugg</small></th>`;
        });
        headerHtml += `
            <th style="width: 80px;">Rating</th>
            <th style="width: 70px;">Conf</th>
            <th>Justification</th>
        `;
        thead.innerHTML = headerHtml;
    }

    recommendations.forEach((rec, index) => {
        const row = document.createElement('tr');
        let ratingClass = 'rating-incorrect';
        const overallRating = rec.rating || rec.overall_rating || 'unknown';
        if (overallRating === 'correct') ratingClass = 'rating-correct';
        else if (overallRating === 'partially_correct') ratingClass = 'rating-partial';

        // Multi-dimension display
        if (isMultiDim && rec.dimension_ratings) {
            let rowHtml = `
                <td><input type="checkbox" class="checkbox" data-index="${index}" onchange="updateSelection()"></td>
                <td>${rec.question_num}</td>
                <td class="question-text">
                    <div class="question-text-full">${rec.question_text || ''}</div>
                </td>
            `;

            dimensions.forEach(dim => {
                const dimRating = rec.dimension_ratings[dim] || {};
                const current = dimRating.current || rec.current_mapping?.[`mapped_${dim}`] || '-';
                const suggested = dimRating.suggested || current;
                const dimRatingVal = dimRating.rating || 'unknown';

                let dimClass = '';
                if (dimRatingVal === 'correct') dimClass = 'color: #065f46;';
                else if (dimRatingVal === 'incorrect') dimClass = 'color: #991b1b; font-weight: bold;';
                else if (dimRatingVal === 'partially_correct') dimClass = 'color: #92400e;';

                if (dimRatingVal === 'correct') {
                    rowHtml += `<td style="${dimClass}"><strong>${current}</strong></td>`;
                } else {
                    rowHtml += `<td style="${dimClass}"><span style="text-decoration: line-through;">${current}</span> → <strong>${suggested}</strong></td>`;
                }
            });

            const confidence = rec.confidence || 0;
            let confClass = 'confidence-low';
            if (confidence >= 0.85) confClass = 'confidence-high';
            else if (confidence >= 0.70) confClass = 'confidence-medium';

            rowHtml += `
                <td><span class="rating-badge ${ratingClass}">${overallRating.replace('_', ' ')}</span></td>
                <td><span class="confidence-badge ${confClass}">${Math.round(confidence * 100)}%</span></td>
                <td class="justification">${rec.justification || ''}</td>
            `;
            row.innerHTML = rowHtml;
        } else {
            // Single dimension mode - original display
            let originalCode = 'N/A';
            if (rec.current_mapping) {
                if (rec.current_mapping.id) {
                    originalCode = rec.current_mapping.id;
                } else if (rec.current_mapping.topic) {
                    originalCode = rec.current_mapping.topic;
                    if (rec.current_mapping.subtopic) {
                        originalCode += ' / ' + rec.current_mapping.subtopic;
                    }
                } else {
                    // Try to get any mapped_* value
                    const mappedKeys = Object.keys(rec.current_mapping).filter(k => k.startsWith('mapped_'));
                    if (mappedKeys.length > 0) {
                        originalCode = rec.current_mapping[mappedKeys[0]] || 'N/A';
                    }
                }
            }

            const suggestedCode = rec.mapped_id || rec.mapped_topic || rec.recommended_mapping || '';
            const definition = definitions[suggestedCode] || definitions[rec.mapped_id] || definitions[rec.mapped_topic] || '';

            const confidence = rec.confidence || 0;
            let confClass = 'confidence-low';
            if (confidence >= 0.85) confClass = 'confidence-high';
            else if (confidence >= 0.70) confClass = 'confidence-medium';

            row.innerHTML = `
                <td><input type="checkbox" class="checkbox" data-index="${index}" onchange="updateSelection()"></td>
                <td>${rec.question_num}</td>
                <td class="question-text">
                    <div class="question-text-full">${rec.question_text || ''}</div>
                </td>
                <td><strong>${originalCode}</strong></td>
                <td><span class="rating-badge ${ratingClass}">${overallRating.replace('_', ' ')}</span></td>
                <td><strong>${suggestedCode}</strong></td>
                <td class="definition-text">${definition}</td>
                <td><span class="confidence-badge ${confClass}">${Math.round(confidence * 100)}%</span></td>
                <td class="justification">${rec.justification || rec.suggestion_justification || ''}</td>
            `;
        }
        tbody.appendChild(row);
    });
}

function updateSelection() {
    const checkboxes = document.querySelectorAll('#ratingsBody input[type="checkbox"]');
    selectedIndices = [];
    checkboxes.forEach(cb => { if (cb.checked) selectedIndices.push(parseInt(cb.dataset.index)); });
    document.getElementById('selectionCount').textContent = selectedIndices.length;
}

function toggleSelectAll() {
    const selectAll = document.getElementById('selectAllCheckbox').checked;
    document.querySelectorAll('#ratingsBody input[type="checkbox"]').forEach(cb => cb.checked = selectAll);
    updateSelection();
}

function selectAllIncorrect() {
    document.querySelectorAll('#ratingsBody input[type="checkbox"]').forEach((cb, i) => {
        cb.checked = recommendations[i].rating === 'incorrect';
    });
    updateSelection();
}

function selectAllPartial() {
    document.querySelectorAll('#ratingsBody input[type="checkbox"]').forEach((cb, i) => {
        cb.checked = recommendations[i].rating === 'partially_correct';
    });
    updateSelection();
}

function selectNone() {
    document.querySelectorAll('#ratingsBody input[type="checkbox"]').forEach(cb => cb.checked = false);
    document.getElementById('selectAllCheckbox').checked = false;
    updateSelection();
}

function saveAndDownload() {
    if (selectedIndices.length === 0) {
        showStatus('Please select at least one correction', 'error');
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
    document.getElementById('saveName').value = `Corrections_${new Date().toISOString().slice(0, 10)}`;
    document.getElementById('saveModal').classList.remove('hidden');
}

function closeSaveModal() {
    document.getElementById('saveModal').classList.add('hidden');
    pendingSaveData = null;
}

async function confirmSaveAndDownload() {
    if (!pendingSaveData) return;

    const name = document.getElementById('saveName').value.trim() || 'Unnamed Corrections';

    try {
        const response = await fetch(`${API_URL}/apply-corrections-and-save`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                mapped_file: uploadedFiles.mappedFile,
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
    ratings = [];
    recommendations = [];
    selectedIndices = [];
    uploadedFiles = { mappedFile: null, referenceFile: null };
    document.getElementById('mappedFile').value = '';
    document.getElementById('referenceFile').value = '';
    document.getElementById('ratingsSection').classList.add('hidden');
    document.getElementById('loading').classList.add('hidden');
    document.getElementById('uploadSection').classList.remove('hidden');
    document.getElementById('selectionCount').textContent = '0';
    document.getElementById('ratingsBody').innerHTML = '';
    document.getElementById('selectAllCheckbox').checked = false;
    document.getElementById('dimensionError').classList.remove('show');
    // Reset table header to default
    const thead = document.getElementById('tableHeader');
    thead.innerHTML = `
        <th style="width: 40px;"><input type="checkbox" class="checkbox" id="selectAllCheckbox" onchange="toggleSelectAll()"></th>
        <th style="width: 70px;">Q#</th>
        <th style="width: 250px;">Question</th>
        <th style="width: 100px;">Original Code</th>
        <th style="width: 90px;">Rating</th>
        <th style="width: 100px;">Suggested Code</th>
        <th style="width: 200px;">Definition</th>
        <th style="width: 80px;">Confidence</th>
        <th style="width: 200px;">Justification</th>
    `;
}
