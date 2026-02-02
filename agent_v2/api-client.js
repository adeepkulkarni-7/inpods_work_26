/**
 * Inpods API Client
 * Wrapper for backend API calls with error handling
 */

class InpodsAPIClient {
    constructor(baseUrl = 'http://localhost:5001') {
        this.baseUrl = baseUrl;
        this.apiUrl = `${baseUrl}/api`;
    }

    // =========================================================================
    // HEALTH CHECK
    // =========================================================================

    async checkHealth() {
        try {
            const response = await fetch(`${this.apiUrl}/health`);
            return await response.json();
        } catch (error) {
            return { status: 'error', error: error.message };
        }
    }

    // =========================================================================
    // FILE UPLOAD
    // =========================================================================

    /**
     * Upload question file + reference file (Mode A)
     */
    async uploadFiles(questionFile, referenceFile) {
        const formData = new FormData();
        formData.append('question_file', questionFile);
        formData.append('reference_file', referenceFile);

        const response = await fetch(`${this.apiUrl}/upload`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Upload failed');
        }

        return await response.json();
    }

    /**
     * Upload mapped file + optional reference (Mode B/C)
     */
    async uploadMappedFile(mappedFile, referenceFile = null) {
        const formData = new FormData();
        formData.append('mapped_file', mappedFile);
        if (referenceFile) {
            formData.append('reference_file', referenceFile);
        }

        const response = await fetch(`${this.apiUrl}/upload-mapped`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Upload failed');
        }

        return await response.json();
    }

    // =========================================================================
    // MAPPING (Mode A)
    // =========================================================================

    /**
     * Map questions to curriculum dimensions
     */
    async mapQuestions(questionFile, referenceFile, dimensions, batchSize = 5) {
        const response = await fetch(`${this.apiUrl}/run-audit-efficient`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                question_file: questionFile,
                reference_file: referenceFile,
                dimensions: dimensions,
                dimension: dimensions[0],
                batch_size: batchSize
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Mapping failed');
        }

        return await response.json();
    }

    // =========================================================================
    // RATING (Mode B)
    // =========================================================================

    /**
     * Rate existing mappings
     */
    async rateMappings(mappedFile, referenceFile, dimensions, batchSize = 5) {
        const response = await fetch(`${this.apiUrl}/rate-mappings`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                mapped_file: mappedFile,
                reference_file: referenceFile,
                dimensions: dimensions,
                dimension: dimensions[0],
                batch_size: batchSize
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Rating failed');
        }

        return await response.json();
    }

    // =========================================================================
    // INSIGHTS (Mode C)
    // =========================================================================

    /**
     * Generate visualization insights
     */
    async generateInsights(mappedFile, referenceFile = null, dimensions = []) {
        const response = await fetch(`${this.apiUrl}/generate-insights`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                mapped_file: mappedFile,
                reference_file: referenceFile,
                dimensions: dimensions
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Insights generation failed');
        }

        return await response.json();
    }

    // =========================================================================
    // SAVE & EXPORT
    // =========================================================================

    /**
     * Save mappings and download Excel (Mode A)
     */
    async saveAndDownloadMappings(questionFile, recommendations, selectedIndices, dimensions, name) {
        const response = await fetch(`${this.apiUrl}/apply-and-save`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                question_file: questionFile,
                recommendations: recommendations,
                selected_indices: selectedIndices,
                dimensions: dimensions,
                dimension: dimensions[0],
                name: name
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Save failed');
        }

        return await response.json();
    }

    /**
     * Save corrections and download Excel (Mode B)
     */
    async saveAndDownloadCorrections(mappedFile, recommendations, selectedIndices, dimensions, name) {
        const response = await fetch(`${this.apiUrl}/apply-corrections-and-save`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                mapped_file: mappedFile,
                recommendations: recommendations,
                selected_indices: selectedIndices,
                dimensions: dimensions,
                dimension: dimensions[0],
                name: name
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Save failed');
        }

        return await response.json();
    }

    /**
     * Trigger file download
     */
    downloadFile(downloadUrl) {
        window.location.href = `${this.baseUrl}${downloadUrl}`;
    }

    /**
     * Get chart image URL
     */
    getChartUrl(chartPath) {
        return `${this.baseUrl}${chartPath}`;
    }

    // =========================================================================
    // LIBRARY
    // =========================================================================

    async listLibrary() {
        const response = await fetch(`${this.apiUrl}/library`);
        return await response.json();
    }

    async getLibraryItem(id) {
        const response = await fetch(`${this.apiUrl}/library/${id}`);
        return await response.json();
    }

    async deleteLibraryItem(id) {
        const response = await fetch(`${this.apiUrl}/library/${id}`, {
            method: 'DELETE'
        });
        return await response.json();
    }
}

// Export for use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { InpodsAPIClient };
}
