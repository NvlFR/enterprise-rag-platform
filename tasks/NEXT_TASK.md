# Next Task

## Task ID

TASK-020

## Title

Metadata Extraction (Language, Title, Keywords)

## Why This Task

Improve document searchability by extracting rich metadata from the extracted text and file properties.

## Dependencies Check

- [x] TASK-019: Text Extraction Service (Unstructured.io/PyMuPDF)

## Context

We have the raw text extracted from documents. Now we need to parse this text and associated file properties to extract useful metadata (language, title, keywords) to enrich the `document_metadata` JSONB field in our `documents` table, which will be crucial for metadata filtering in hybrid search.

## Implementation Plan

1. **Develop Metadata Extraction**:
    *   Create a service or update `ParserService` in `backend/app/services/parser.py` to extract metadata.
    *   Implement methods for language detection, title extraction (e.g., first heading), and basic keyword extraction (e.g., using frequency or NLP).
2. **Integration**:
    *   Update the Celery worker (`process_document_task`) to call the metadata extraction logic after text parsing.
    *   Update the `DocumentService` to save metadata to the database.
3. **Testing**:
    *   Add comprehensive tests in `backend/tests/test_metadata_extraction.py`.

## Files To Create

- `backend/tests/test_metadata_extraction.py`

## Files To Modify

- `backend/app/services/parser.py` (add metadata extraction logic)
- `backend/app/tasks/document.py` (integrate metadata extraction)

## Acceptance Criteria

- [ ] Language, title, and keywords are extracted for supported file types.
- [ ] Metadata is correctly saved to the database.
- [ ] Extraction logic handles edge cases (e.g., no title found).
- [ ] Code is linted and formatted with Ruff.

## Definition of Done

- [ ] Metadata extraction service implemented and integrated.
- [ ] Unit tests for metadata extraction passing.
- [ ] Code is linted and formatted with Ruff.

## Expected Output

A metadata-enriched document record in the database, enabling better search and filtering.

## Testing Strategy

- **Unit Test**: Create `backend/tests/test_metadata_extraction.py` to test metadata extraction from text samples.
