---
id: TASK-055
status: completed
priority: medium
epic: Frontend Chat Interface
estimated_hours: 6
dependencies: [TASK-053, TASK-046]
---

# Document Source Viewer (PDF Sidebar)

## Objective
Implement a sidebar or overlay that allows users to view the original document context for a citation, ideally with PDF highlighting.

## Business Context
Seeing the citation in the context of the original document is the ultimate form of verification for users.

## Technical Context
We need to fetch the document (or a specific page) from the backend and display it. For PDFs, we can use a library like `react-pdf-viewer`.

## Requirements
- Create a `SourceViewer` component.
- Display the text content of the cited chunk.
- If it's a PDF, attempt to render the page and highlight the relevant section (if coordinates are available).
- Provide a full-screen view option.

## Acceptance Criteria
- [ ] Users can open the source viewer from a citation.
- [ ] The viewer displays the correct content from the API (TASK-046).
- [ ] Basic PDF rendering is functional.

## Files To Create
- /frontend/src/components/chat/source-viewer.tsx
- /frontend/src/hooks/use-source-preview.ts

## Implementation Notes
Focus on text-based preview first, then add PDF rendering if time permits or as a follow-up.

## Testing Requirements
- Test with various document types.

## Done Definition
- All acceptance criteria met
- Users can view sources in context
