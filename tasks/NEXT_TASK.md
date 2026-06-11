---
id: TASK-056
status: todo
priority: medium
epic: Frontend Chat Interface
estimated_hours: 4
dependencies: [TASK-045, TASK-053]
---

# Typing Indicators and Streaming UI

## Objective
Implement a smooth streaming UI for assistant responses, including typing indicators and auto-scrolling.

## Business Context
Real-time feedback makes the assistant feel more responsive and "alive," improving the overall user experience.

## Technical Context
We need to handle the Server-Sent Events (SSE) stream from the backend and update the message content incrementally.

## Requirements
- Use `fetch` or a specialized library to consume the SSE stream from TASK-045.
- Update the message state as chunks arrive.
- Show a "typing" or "thinking" indicator while the stream is active.
- Implement auto-scrolling to the bottom of the chat as new content arrives.
- Allow the user to stop the generation (optional).

## Acceptance Criteria
- [ ] Responses appear word-by-word (or chunk-by-chunk) in real-time.
- [ ] Typing indicator is visible only while waiting for the next chunk.
- [ ] The chat window automatically scrolls down as the response grows.

## Files To Create
- /frontend/src/hooks/use-chat-stream.ts
- /frontend/src/components/chat/typing-indicator.tsx

## Implementation Notes
Be careful with React state updates in high-frequency streams. Consider using a `ref` or a more optimized state management approach if performance becomes an issue.

## Testing Requirements
- Test with long responses to ensure auto-scroll works.
- Test network interruptions during streaming.

## Done Definition
- All acceptance criteria met
- Streaming experience is smooth and responsive
