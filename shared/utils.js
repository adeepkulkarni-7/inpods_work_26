// Shared Utilities - Common across all standalone apps

const API_URL = 'http://localhost:5001/api';
const BASE_URL = 'http://localhost:5001';

function showStatus(message, type) {
    const status = document.getElementById('status');
    if (status) {
        status.textContent = message;
        status.className = `status ${type}`;
        setTimeout(() => { status.className = 'status'; }, 5000);
    }
}

function getSelectedDimensions(containerId) {
    const checkboxes = document.querySelectorAll(`#${containerId} input[type="checkbox"]:checked`);
    return Array.from(checkboxes).map(cb => cb.value);
}

// Dimension labels for display
const DIMENSION_LABELS = {
    'competency': 'Competency',
    'objective': 'Objective',
    'skill': 'Skill',
    'nmc_competency': 'NMC Competency',
    'area_topics': 'Topic Areas',
    'blooms': 'Blooms Level',
    'complexity': 'Complexity'
};

function formatDimensionName(dim) {
    return DIMENSION_LABELS[dim] || dim.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase());
}
