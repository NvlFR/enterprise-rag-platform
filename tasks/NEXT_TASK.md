---
id: TASK-057
status: todo
priority: high
epic: Frontend Doc Management
estimated_hours: 5
dependencies: [TASK-051, TASK-017]
---

# Document Upload Interface (Drag & Drop)

## Objective
Implement a user-friendly interface for uploading documents, featuring drag-and-drop functionality and progress tracking.

## Business Context
Document ingestion is the first step in the RAG pipeline. A simple and reliable upload process is essential for users to add their own knowledge.

## Technical Context
The interface needs to interact with the multipart file upload endpoint (TASK-017).

## Requirements
- Create a drag-and-drop zone using `react-dropzone`.
- Support multiple file uploads.
- Display upload progress for each file.
- Handle validation (file types, size limits).
- Show success/error notifications using Toasts.

## Acceptance Criteria
- [ ] Users can drag and drop files to upload.
- [ ] Multiple files are uploaded concurrently or sequentially.
- [ ] Progress bars accurately reflect upload status.
- [ ] Invalid files are rejected with a clear error message.

## Files To Create
- /frontend/src/components/docs/upload-zone.tsx
- /frontend/src/components/docs/upload-progress.tsx

## Implementation Notes
Use the API client with `onUploadProgress` if using Axios.

## Testing Requirements
- Test with various file sizes and types.
- Test network failures during upload.

## Done Definition
- All acceptance criteria met
- Upload interface is intuitive and reliable
