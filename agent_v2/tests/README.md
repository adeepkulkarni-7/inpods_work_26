# Inpods Agent Test Suite

17 test cases validating the conversational agent functionality.

## Running Tests

### Browser (Recommended)
```bash
# From project root
python -m http.server 8002

# Open in browser
http://localhost:8002/agent_v2/tests/test-runner.html
```

Click "Run All Tests" to execute.

### Node.js
```bash
cd agent_v2/tests
node agent.test.js
```

---

## Test Cases

### File Upload Tests (TC01-TC04)

| ID | Test | Expected |
|----|------|----------|
| TC01 | Upload valid CSV question file | Accept, parse headers & count questions |
| TC02 | Upload valid reference file | Detect dimensions (C1-C6, KL1-KL6) |
| TC03 | Upload invalid file type (PDF) | Reject with error message |
| TC04 | Upload empty file | Show "No questions found" |

### Detection Tests (TC05-TC08)

| ID | Test | Expected |
|----|------|----------|
| TC05 | Detect unmapped questions | No `mapped_*` columns → state = "unmapped" |
| TC06 | Detect pre-mapped questions | Has `mapped_*` columns → state = "mapped" |
| TC07 | Detect NMC codes in reference | Find MI1.1, MI2.1 patterns → offer NMC dimension |
| TC08 | Detect multiple dimensions | Find both C1-C6 and KL1-KL6 → offer both |

### Mapping Tests (TC09-TC11)

| ID | Test | Expected |
|----|------|----------|
| TC09 | Map 5 questions to competency | Return 5 recommendations with confidence |
| TC10 | Batch size affects API calls | 10 questions / batch 3 = 4 API calls |
| TC11 | Multi-dimension mapping | Return `mapped_competency` AND `mapped_blooms` |

### Rating Tests (TC12-TC13)

| ID | Test | Expected |
|----|------|----------|
| TC12 | Rate pre-mapped file | Return counts: correct, partial, incorrect |
| TC13 | Apply selected corrections | Only update selected indices |

### Visualization Tests (TC14-TC15)

| ID | Test | Expected |
|----|------|----------|
| TC14 | Generate insights | Return chart URLs + summary stats |
| TC15 | Generate with reference | Include gap analysis chart |

### Conversation Flow Tests (TC16-TC17)

| ID | Test | Expected |
|----|------|----------|
| TC16 | Full workflow | IDLE → AWAIT_FILES → ANALYZING → ... → COMPLETE |
| TC17 | Start over mid-flow | Reset all state to IDLE |

---

## Test Data

The tests use mock CSV data defined in `agent.test.js`:

- `SAMPLE_UNMAPPED_CSV` - 5 questions without mappings
- `SAMPLE_MAPPED_CSV` - 5 questions with competency + blooms mappings
- `SAMPLE_REFERENCE_CSV` - C1-C6 + KL1-KL6 reference
- `SAMPLE_NMC_REFERENCE_CSV` - MI1.x-MI3.x NMC codes

---

## Adding New Tests

```javascript
await runner.run('TC18: New test description', async () => {
    // Arrange
    const input = { ... };

    // Act
    const result = someFunction(input);

    // Assert
    assertEqual(result.value, expected, 'Should match expected');
    assert(result.valid, 'Should be valid');
});
```

---

## Test Utilities

```javascript
assert(condition, message)           // Throws if false
assertEqual(actual, expected, msg)   // Throws if not equal
assertContains(array, item, msg)     // Throws if not in array
assertHasProperty(obj, prop, msg)    // Throws if property missing
```
