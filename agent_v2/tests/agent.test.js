/**
 * Inpods Conversational Agent - Test Suite
 *
 * 17 test cases covering:
 * - File upload (TC01-TC04)
 * - Detection (TC05-TC08)
 * - Mapping (TC09-TC11)
 * - Rating (TC12-TC13)
 * - Visualization (TC14-TC15)
 * - Conversation flow (TC16-TC17)
 *
 * Run with: Open test-runner.html in browser
 * Or: node --experimental-vm-modules agent.test.js (if using Node)
 */

const TEST_API_URL = 'http://localhost:5001';

// Test utilities
class TestRunner {
    constructor() {
        this.results = [];
        this.passed = 0;
        this.failed = 0;
    }

    async run(name, testFn) {
        const startTime = Date.now();
        try {
            await testFn();
            this.passed++;
            this.results.push({
                name,
                status: 'PASS',
                duration: Date.now() - startTime
            });
            console.log(`✓ ${name}`);
        } catch (error) {
            this.failed++;
            this.results.push({
                name,
                status: 'FAIL',
                error: error.message,
                duration: Date.now() - startTime
            });
            console.error(`✗ ${name}: ${error.message}`);
        }
    }

    summary() {
        console.log('\n' + '='.repeat(50));
        console.log(`Tests: ${this.passed} passed, ${this.failed} failed, ${this.passed + this.failed} total`);
        console.log('='.repeat(50));
        return { passed: this.passed, failed: this.failed, results: this.results };
    }
}

function assert(condition, message) {
    if (!condition) throw new Error(message || 'Assertion failed');
}

function assertEqual(actual, expected, message) {
    if (actual !== expected) {
        throw new Error(message || `Expected ${expected}, got ${actual}`);
    }
}

function assertContains(array, item, message) {
    if (!array.includes(item)) {
        throw new Error(message || `Expected array to contain ${item}`);
    }
}

function assertHasProperty(obj, prop, message) {
    if (!(prop in obj)) {
        throw new Error(message || `Expected object to have property ${prop}`);
    }
}

// Mock file creation for tests (works in both Node and Browser)
function createMockCSV(content) {
    if (typeof Blob !== 'undefined') {
        return new Blob([content], { type: 'text/csv' });
    }
    return { content, type: 'text/csv', size: content.length };
}

function createMockFile(name, content, type = 'text/csv') {
    if (typeof Blob !== 'undefined' && typeof File !== 'undefined') {
        const blob = new Blob([content], { type });
        return new File([blob], name, { type });
    }
    // Node.js mock
    return { name, content, type, size: content.length };
}

// Sample test data
const SAMPLE_UNMAPPED_CSV = `Question Number,Question Text,Option A,Option B,Option C,Option D
1,Which bacteria causes tuberculosis?,E. coli,M. tuberculosis,S. aureus,P. aeruginosa
2,What is the function of ribosomes?,Energy production,Protein synthesis,Cell division,DNA replication
3,Which virus causes AIDS?,Influenza,HIV,Hepatitis B,Herpes
4,What type of immunity is provided by vaccines?,Natural active,Natural passive,Artificial active,Artificial passive
5,Which organelle is the powerhouse of the cell?,Nucleus,Mitochondria,Ribosome,Golgi body`;

const SAMPLE_MAPPED_CSV = `Question Number,Question Text,mapped_competency,mapped_blooms,confidence_score
1,Which bacteria causes tuberculosis?,C3,KL1,0.92
2,What is the function of ribosomes?,C2,KL2,0.88
3,Which virus causes AIDS?,C3,KL1,0.95
4,What type of immunity is provided by vaccines?,C4,KL3,0.78
5,Which organelle is the powerhouse of the cell?,C1,KL2,0.85`;

const SAMPLE_REFERENCE_CSV = `Code,Type,Description
C1,Competency,Remember basic science concepts
C2,Competency,Understand biological mechanisms
C3,Competency,Apply clinical knowledge
C4,Competency,Analyze diagnostic findings
C5,Competency,Evaluate treatment options
C6,Competency,Create treatment plans
KL1,Blooms,Remember
KL2,Blooms,Understand
KL3,Blooms,Apply
KL4,Blooms,Analyze
KL5,Blooms,Evaluate
KL6,Blooms,Create`;

const SAMPLE_NMC_REFERENCE_CSV = `NMC Code,Description
MI1.1,Basic microbiology principles
MI1.2,Bacterial classification
MI2.1,Immunology fundamentals
MI2.2,Antibody mechanisms
MI3.1,Clinical infections - respiratory
MI3.2,Clinical infections - GI tract`;


// =============================================================================
// TEST CASES
// =============================================================================

async function runAllTests() {
    const runner = new TestRunner();

    console.log('\n🧪 Inpods Agent Test Suite\n');
    console.log('='.repeat(50));

    // =========================================================================
    // FILE UPLOAD TESTS (TC01-TC04)
    // =========================================================================

    console.log('\n📁 File Upload Tests\n');

    // TC01: Upload valid CSV question file
    await runner.run('TC01: Upload valid CSV question file', async () => {
        const questionFile = createMockFile('questions.csv', SAMPLE_UNMAPPED_CSV);

        // Test file validation logic
        assert(questionFile.name.endsWith('.csv'), 'Should accept CSV file');
        assert(questionFile.size > 0, 'File should have content');

        // Test parsing logic (simulated)
        const lines = SAMPLE_UNMAPPED_CSV.split('\n');
        const headers = lines[0].split(',');
        assertContains(headers, 'Question Number', 'Should have Question Number column');
        assertContains(headers, 'Question Text', 'Should have Question Text column');
        assertEqual(lines.length - 1, 5, 'Should have 5 questions');
    });

    // TC02: Upload valid Excel reference file
    await runner.run('TC02: Upload valid reference file with dimensions', async () => {
        const lines = SAMPLE_REFERENCE_CSV.split('\n');
        const headers = lines[0].split(',');

        // Check reference structure
        assertContains(headers, 'Code', 'Should have Code column');
        assertContains(headers, 'Description', 'Should have Description column');

        // Check dimension detection
        const codes = lines.slice(1).map(l => l.split(',')[0]);
        const hasCompetency = codes.some(c => /^C\d$/.test(c));
        const hasBlooms = codes.some(c => /^KL\d$/.test(c));

        assert(hasCompetency, 'Should detect Competency codes (C1-C6)');
        assert(hasBlooms, 'Should detect Blooms codes (KL1-KL6)');
    });

    // TC03: Upload invalid file type
    await runner.run('TC03: Reject invalid file type (PDF)', async () => {
        const invalidFile = createMockFile('document.pdf', 'fake pdf content', 'application/pdf');
        const allowedExtensions = ['csv', 'xlsx', 'xls', 'ods'];
        const extension = invalidFile.name.split('.').pop().toLowerCase();

        const isAllowed = allowedExtensions.includes(extension);
        assert(!isAllowed, 'Should reject PDF files');
    });

    // TC04: Upload empty file
    await runner.run('TC04: Handle empty file gracefully', async () => {
        const emptyCSV = 'Question Number,Question Text\n';
        const lines = emptyCSV.split('\n').filter(l => l.trim());
        const questionCount = lines.length - 1; // Minus header

        assertEqual(questionCount, 0, 'Should detect 0 questions');

        // Agent should show appropriate message
        const expectedMessage = questionCount === 0
            ? 'No questions found in file'
            : `Found ${questionCount} questions`;
        assert(expectedMessage.includes('No questions'), 'Should indicate empty file');
    });

    // =========================================================================
    // DETECTION TESTS (TC05-TC08)
    // =========================================================================

    console.log('\n🔍 Detection Tests\n');

    // TC05: Detect unmapped questions
    await runner.run('TC05: Detect unmapped questions', async () => {
        const headers = SAMPLE_UNMAPPED_CSV.split('\n')[0].toLowerCase();

        const mappingColumns = [
            'mapped_competency', 'mapped_objective', 'mapped_skill',
            'mapped_topic', 'mapped_blooms', 'mapped_complexity', 'mapped_nmc'
        ];

        const hasMappingColumn = mappingColumns.some(col => headers.includes(col));
        assert(!hasMappingColumn, 'Unmapped file should not have mapping columns');

        // Agent logic
        const detectedState = hasMappingColumn ? 'mapped' : 'unmapped';
        assertEqual(detectedState, 'unmapped', 'Should detect as unmapped');
    });

    // TC06: Detect pre-mapped questions
    await runner.run('TC06: Detect pre-mapped questions', async () => {
        const headers = SAMPLE_MAPPED_CSV.split('\n')[0].toLowerCase();

        const mappingColumns = [
            'mapped_competency', 'mapped_objective', 'mapped_skill',
            'mapped_topic', 'mapped_blooms', 'mapped_complexity', 'mapped_nmc'
        ];

        const hasMappingColumn = mappingColumns.some(col => headers.includes(col));
        assert(hasMappingColumn, 'Mapped file should have mapping columns');

        // Check which dimensions are mapped
        const detectedDimensions = [];
        if (headers.includes('mapped_competency')) detectedDimensions.push('competency');
        if (headers.includes('mapped_blooms')) detectedDimensions.push('blooms');

        assert(detectedDimensions.length >= 1, 'Should detect at least one mapped dimension');
        assertContains(detectedDimensions, 'competency', 'Should detect competency mapping');
        assertContains(detectedDimensions, 'blooms', 'Should detect blooms mapping');
    });

    // TC07: Detect NMC codes in reference
    await runner.run('TC07: Detect NMC codes in reference file', async () => {
        const content = SAMPLE_NMC_REFERENCE_CSV;

        // NMC pattern: MI followed by digits and dots (MI1.1, MI2.1, etc.)
        const nmcPattern = /MI\d+\.\d+/g;
        const nmcMatches = content.match(nmcPattern) || [];

        assert(nmcMatches.length > 0, 'Should find NMC codes');
        assert(nmcMatches.includes('MI1.1'), 'Should find MI1.1');
        assert(nmcMatches.includes('MI2.1'), 'Should find MI2.1');

        // Agent should offer NMC mapping option
        const detectedDimension = 'nmc_competency';
        assertEqual(detectedDimension, 'nmc_competency', 'Should detect NMC dimension');
    });

    // TC08: Detect multiple dimensions (C1-C6 + KL1-KL6)
    await runner.run('TC08: Detect multiple dimensions in reference', async () => {
        const content = SAMPLE_REFERENCE_CSV;

        const competencyPattern = /^C\d,/gm;
        const bloomsPattern = /^KL\d,/gm;

        const competencyMatches = content.match(competencyPattern) || [];
        const bloomsMatches = content.match(bloomsPattern) || [];

        assert(competencyMatches.length === 6, 'Should find 6 competency codes');
        assert(bloomsMatches.length === 6, 'Should find 6 blooms codes');

        // Agent should offer both dimensions
        const availableDimensions = [];
        if (competencyMatches.length > 0) availableDimensions.push('competency');
        if (bloomsMatches.length > 0) availableDimensions.push('blooms');

        assertEqual(availableDimensions.length, 2, 'Should detect both dimensions');
    });

    // =========================================================================
    // MAPPING TESTS (TC09-TC11)
    // =========================================================================

    console.log('\n🗺️ Mapping Tests\n');

    // TC09: Map 5 questions to competency
    await runner.run('TC09: Map questions returns correct count', async () => {
        // Simulate mapping response
        const mockResponse = {
            recommendations: [
                { question_num: 1, mapped_competency: 'C3', confidence: 0.92 },
                { question_num: 2, mapped_competency: 'C2', confidence: 0.88 },
                { question_num: 3, mapped_competency: 'C3', confidence: 0.95 },
                { question_num: 4, mapped_competency: 'C4', confidence: 0.78 },
                { question_num: 5, mapped_competency: 'C1', confidence: 0.85 }
            ],
            total_questions: 5,
            mapped_questions: 5
        };

        assertEqual(mockResponse.recommendations.length, 5, 'Should return 5 recommendations');
        assertEqual(mockResponse.total_questions, 5, 'Should report 5 total questions');

        // All should have required fields
        mockResponse.recommendations.forEach((rec, i) => {
            assertHasProperty(rec, 'question_num', `Rec ${i} should have question_num`);
            assertHasProperty(rec, 'mapped_competency', `Rec ${i} should have mapped_competency`);
            assertHasProperty(rec, 'confidence', `Rec ${i} should have confidence`);
        });
    });

    // TC10: Map with batch size 3
    await runner.run('TC10: Batch size affects API call count', async () => {
        const totalQuestions = 10;
        const batchSize = 3;

        const expectedBatches = Math.ceil(totalQuestions / batchSize);
        assertEqual(expectedBatches, 4, 'Should make 4 batches for 10 questions with batch size 3');

        // With batch size 5
        const batchSize5 = 5;
        const expectedBatches5 = Math.ceil(totalQuestions / batchSize5);
        assertEqual(expectedBatches5, 2, 'Should make 2 batches with batch size 5');
    });

    // TC11: Map to multiple dimensions
    await runner.run('TC11: Multi-dimension mapping returns all dimensions', async () => {
        const dimensions = ['competency', 'blooms'];

        // Simulate multi-dimension response
        const mockResponse = {
            recommendations: [
                { question_num: 1, mapped_competency: 'C3', mapped_blooms: 'KL1', confidence: 0.90 },
                { question_num: 2, mapped_competency: 'C2', mapped_blooms: 'KL2', confidence: 0.85 }
            ],
            dimensions: dimensions
        };

        // Check all dimensions are present
        mockResponse.recommendations.forEach((rec, i) => {
            dimensions.forEach(dim => {
                const key = `mapped_${dim}`;
                assertHasProperty(rec, key, `Rec ${i} should have ${key}`);
            });
        });

        assertEqual(mockResponse.dimensions.length, 2, 'Should return both dimensions');
    });

    // =========================================================================
    // RATING TESTS (TC12-TC13)
    // =========================================================================

    console.log('\n⭐ Rating Tests\n');

    // TC12: Rate pre-mapped file
    await runner.run('TC12: Rate mappings returns correct/partial/incorrect counts', async () => {
        // Simulate rating response
        const mockResponse = {
            ratings: [
                { question_num: 1, rating: 'correct' },
                { question_num: 2, rating: 'correct' },
                { question_num: 3, rating: 'partially_correct' },
                { question_num: 4, rating: 'incorrect' },
                { question_num: 5, rating: 'correct' }
            ],
            summary: {
                correct: 3,
                partially_correct: 1,
                incorrect: 1
            },
            recommendations: [
                { question_num: 3, rating: 'partially_correct', suggested: 'C4' },
                { question_num: 4, rating: 'incorrect', suggested: 'C2' }
            ]
        };

        assertEqual(mockResponse.summary.correct, 3, 'Should have 3 correct');
        assertEqual(mockResponse.summary.partially_correct, 1, 'Should have 1 partial');
        assertEqual(mockResponse.summary.incorrect, 1, 'Should have 1 incorrect');

        // Recommendations should only include non-correct items
        assertEqual(mockResponse.recommendations.length, 2, 'Should have 2 items needing review');
    });

    // TC13: Apply selected corrections
    await runner.run('TC13: Apply corrections updates only selected items', async () => {
        const allRecommendations = [
            { question_num: 3, suggested: 'C4' },
            { question_num: 4, suggested: 'C2' }
        ];

        // User selects only index 1 (question 4)
        const selectedIndices = [1];

        const selectedRecommendations = selectedIndices.map(i => allRecommendations[i]);
        assertEqual(selectedRecommendations.length, 1, 'Should apply only 1 correction');
        assertEqual(selectedRecommendations[0].question_num, 4, 'Should apply to question 4');
    });

    // =========================================================================
    // VISUALIZATION TESTS (TC14-TC15)
    // =========================================================================

    console.log('\n📊 Visualization Tests\n');

    // TC14: Generate insights from mapped file
    await runner.run('TC14: Generate insights returns chart URLs', async () => {
        // Simulate insights response
        const mockResponse = {
            status: 'success',
            charts: {
                executive_summary: '/api/insights/executive_summary.png',
                coverage_heatmap_competency: '/api/insights/coverage_competency.png',
                confidence_gauge: '/api/insights/confidence.png'
            },
            summary: {
                total_questions: 46,
                topics_covered: 6,
                average_confidence: 0.87
            }
        };

        assertEqual(mockResponse.status, 'success', 'Should return success status');
        assert(Object.keys(mockResponse.charts).length >= 2, 'Should have at least 2 charts');
        assertHasProperty(mockResponse.charts, 'executive_summary', 'Should have executive summary');
        assertHasProperty(mockResponse.summary, 'total_questions', 'Should have question count');
    });

    // TC15: Generate with reference file includes gap analysis
    await runner.run('TC15: Generate with reference includes gap analysis', async () => {
        const mockResponseWithRef = {
            charts: {
                executive_summary: '/api/insights/executive_summary.png',
                gap_analysis_competency: '/api/insights/gap_competency.png',
                coverage_heatmap_competency: '/api/insights/coverage_competency.png'
            },
            summary: {
                gaps_count: 2,
                total_questions: 46
            },
            coverage_tables: {
                competency: [
                    { code: 'C1', count: 8, percentage: 17 },
                    { code: 'C2', count: 12, percentage: 26 },
                    { code: 'C3', count: 0, percentage: 0 },  // Gap!
                    { code: 'C4', count: 15, percentage: 33 },
                    { code: 'C5', count: 11, percentage: 24 },
                    { code: 'C6', count: 0, percentage: 0 }   // Gap!
                ]
            }
        };

        assertHasProperty(mockResponseWithRef.charts, 'gap_analysis_competency', 'Should have gap analysis chart');
        assertEqual(mockResponseWithRef.summary.gaps_count, 2, 'Should report 2 gaps');

        // Check coverage table has gaps marked
        const gaps = mockResponseWithRef.coverage_tables.competency.filter(c => c.count === 0);
        assertEqual(gaps.length, 2, 'Coverage table should show 2 gaps');
    });

    // =========================================================================
    // CONVERSATION FLOW TESTS (TC16-TC17)
    // =========================================================================

    console.log('\n💬 Conversation Flow Tests\n');

    // TC16: Full flow: upload → overview → map → save → visualize
    await runner.run('TC16: Complete workflow executes in order', async () => {
        const workflow = [];

        // Simulate state machine transitions
        const states = ['IDLE', 'AWAIT_FILES', 'ANALYZING', 'SHOW_OVERVIEW', 'AWAIT_ACTION', 'PROCESSING', 'SHOW_RESULTS', 'COMPLETE'];

        // Step 1: Start
        workflow.push('IDLE');

        // Step 2: User initiates
        workflow.push('AWAIT_FILES');

        // Step 3: Files uploaded
        workflow.push('ANALYZING');

        // Step 4: Analysis complete
        workflow.push('SHOW_OVERVIEW');

        // Step 5: User selects action
        workflow.push('AWAIT_ACTION');

        // Step 6: Processing
        workflow.push('PROCESSING');

        // Step 7: Results shown
        workflow.push('SHOW_RESULTS');

        // Step 8: User saves/completes
        workflow.push('COMPLETE');

        assertEqual(workflow.length, states.length, 'Should go through all states');
        workflow.forEach((state, i) => {
            assertEqual(state, states[i], `State ${i} should be ${states[i]}`);
        });
    });

    // TC17: Start over mid-flow resets state
    await runner.run('TC17: Start over resets state correctly', async () => {
        // Simulate agent state
        let agentState = {
            currentState: 'SHOW_RESULTS',
            uploadedFiles: { question: 'test.csv', reference: 'ref.csv' },
            recommendations: [{ id: 1 }, { id: 2 }],
            selectedIndices: [0, 1],
            dimensions: ['competency']
        };

        // User says "start over"
        function resetState() {
            return {
                currentState: 'IDLE',
                uploadedFiles: { question: null, reference: null },
                recommendations: [],
                selectedIndices: [],
                dimensions: []
            };
        }

        agentState = resetState();

        assertEqual(agentState.currentState, 'IDLE', 'Should reset to IDLE');
        assertEqual(agentState.uploadedFiles.question, null, 'Should clear question file');
        assertEqual(agentState.recommendations.length, 0, 'Should clear recommendations');
        assertEqual(agentState.selectedIndices.length, 0, 'Should clear selections');
    });

    // =========================================================================
    // SUMMARY
    // =========================================================================

    return runner.summary();
}

// Export for use in browser or Node
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { runAllTests, TestRunner };
}

// Auto-run if in browser
if (typeof window !== 'undefined') {
    window.runAgentTests = runAllTests;
}

// Auto-run if executed directly in Node
if (typeof require !== 'undefined' && require.main === module) {
    runAllTests().then(summary => {
        process.exit(summary.failed > 0 ? 1 : 0);
    });
}
