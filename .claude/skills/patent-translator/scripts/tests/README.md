# Tests for Patent Translator Scripts

This directory contains pytest tests for patent translation scripts.

## Running Tests

```bash
# Run all tests
pytest -v

# Run specific test file
pytest test_validate_translation.py -v
pytest test_merge_sections.py -v

# Run specific test class
pytest test_validate_translation.py::TestReferenceFormat -v

# Run specific test
pytest test_validate_translation.py::TestReferenceFormat::test_valid_reference_format -v
pytest test_merge_sections.py::test_merge_sections_success -v

# Run with coverage
pytest test_validate_translation.py --cov=../validate-translation --cov-report=html
pytest test_merge_sections.py --cov=../merge-sections --cov-report=html
```

## Test Files

### test_validate_translation.py

Tests for the `validate-translation.py` script.

#### Test Classes

1. **TestReferenceFormat** - Tests for reference number format checking (e.g., "명사(10)" not "명사 (10)")
2. **TestClaimStructure** - Tests for claim numbering and structure validation
3. **TestOrdinalFormat** - Tests for ordinal number format checking ("제1" vs "첫째")
4. **TestTransitionalPhrases** - Tests for transitional phrase consistency checking
5. **TestReferenceCompleteness** - Tests for reference number completeness between source and target
6. **TestSanggiBasic** - Tests for 상기 (antecedent) usage checking
7. **TestAbbreviationFormat** - Tests for abbreviation definition format checking
8. **TestNumberUnitSpacing** - Tests for spacing between numbers and units
9. **TestGenerateReport** - Tests for report generation with errors and warnings
10. **TestValidateAll** - Integration tests for comprehensive validation
11. **TestContextDataLoading** - Tests for loading context data from project files
12. **TestProjectDirFinding** - Tests for finding project directory structure

### Key Features

- **Temporary test files**: Uses pytest fixtures to create temporary project structures
- **Context data**: Tests context loading from `chunk-context.md` and `project-tb.md`
- **Error vs Warning distinction**: Tests both error conditions (must fix) and warnings (should review)
- **Edge cases**: Tests various edge cases like missing claims, letter suffixes in references, etc.

## Known Limitations

### Abbreviation Regex Bug

The abbreviation check uses `\b([A-Z]{2,5})\b` which doesn't work correctly with Korean text because word boundaries (`\b`) don't recognize Korean characters. This is documented in:
- `test_abbreviation_korean_text_limitation` - Documents the bug with Korean context
- `test_abbreviation_without_definition` - Uses English context to test working behavior
- `test_multiple_abbreviations` - Uses mixed English context for reliable detection

## Test Coverage

The test suite covers:
- ✅ All 8 check methods in TranslationValidator
- ✅ Report generation with errors, warnings, and clean states
- ✅ Context data loading from project files
- ✅ Project directory detection
- ✅ Integration testing via validate_all()
- ✅ Edge cases and error conditions

Total: 39 tests covering all major functionality

---

### test_merge_sections.py

Tests for the `merge-sections.py` script.

#### Functions Tested

1. **extract_translation_content()** - Extracts translation content from markdown
   - Content with `## 번역문` header
   - Legacy format without header
   - Empty content handling

2. **parse_by_markers()** - Parses content by 【】 markers
   - Single section parsing
   - Multiple sections in one file
   - Priority content before markers
   - Title with separator edge cases
   - Abstract marker variants (【요약서】, 【요약】)
   - Trailing separator removal
   - All section types (7 standard sections)

3. **merge_priority_into_tech_field()** - Merges priority into tech_field
   - Both priority and tech_field present
   - Priority-only content
   - No priority content
   - Duplicate header removal

4. **get_section_type()** - Determines section type from filename
   - TAC (section-01-tac.md)
   - Background (section-02-background.md)
   - Drawings (section-03-drawings.md)
   - Detailed (section-04-detailed.md, section-04a-detailed.md)
   - Claims (section-05-claims.md)
   - Abstract (section-06-abstract.md)
   - Summary (section-02-summary.md)
   - Unknown files

5. **merge_sections()** - Main merge function
   - Successful section merging
   - Korean patent standard ordering
   - Priority application content handling
   - Missing sections folder error
   - Empty sections folder error
   - Custom output filename
   - Duplicate header removal
   - Content integrity preservation
   - Metadata accuracy (lines, bytes, hash)

#### Integration Tests

- Full workflow with all section types
- Multiple detailed sections merging

#### Test Coverage

- **Total Tests**: 33 (all passing ✓)
- **Korean Patent Standard Order**: Tests verify correct ordering (발명의 명칭 → 기술분야 → 배경기술 → 도면 → 상세설명 → 청구범위 → 요약서)
- **Temporary Directories**: Uses pytest fixtures for isolated testing
- **Mock Section Files**: Creates realistic test data

## Overall Test Statistics

- **test_validate_translation.py**: 39 tests
- **test_merge_sections.py**: 33 tests
- **Total**: 72 tests
