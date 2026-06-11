"use client"

import { useState, useCallback, useRef } from "react"
import { Message } from "@/types/chat"
import { useAuth } from "@/hooks/use-auth"

interface ChatStreamOptions {
  onChunk?: (chunk: string) => void
  onComplete?: (fullMessage: string) => void
  onError?: (error: Error) => void
}

export function useChatStream() {
  const [messages, setMessages] = useState<Message[]>([])
  const [isStreaming, setIsStreaming] = useState(false)
  const abortControllerRef = useRef<AbortController | null>(null)
  const { token } = useAuth()

  const stopStreaming = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort()
      setIsStreaming(false)
    }
  }, [])

  const sendMessage = useCallback(async (
    content: string,
    conversationId?: string,
    options?: ChatStreamOptions
  ) => {
    if (!content.trim()) return

    const userMessage: Message = {
      id: crypto.randomUUID(),
      conversation_id: conversationId || "new",
      role: "user",
      content,
      timestamp: new Date().toISOString(),
    }

    const assistantMessageId = crypto.randomUUID()
    const assistantMessage: Message = {
      id: assistantMessageId,
      conversation_id: conversationId || "new",
      role: "assistant",
      content: "",
      timestamp: new Date().toISOString(),
    }

    setMessages((prev) => [...prev, userMessage, assistantMessage])
    setIsStreaming(true)

    abortControllerRef.current = new AbortController()

    try {
      const response = await fetch("/api/v1/chat/message", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
        },
        body: JSON.stringify({
          message: content,
          conversation_id: conversationId,
          stream: true,
        }),
        signal: abortControllerRef.current.signal,
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const reader = response.body?.getReader()
      if (!reader) throw new Error("No reader available")

      const decoder = new TextDecoder()
      let accumulatedAnswer = ""
      let buffer = ""

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split("\n")
        buffer = lines.pop() || ""

        for (const line of lines) {
          if (!line.trim()) continue
          try {
            const data = JSON.parse(line)

            switch (data.type) {
              case "answer_chunk":
                accumulatedAnswer += data.content
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === assistantMessageId
                      ? { ...msg, content: accumulatedAnswer }
                      : msg
                  )
                )
                options?.onChunk?.(data.content)
                break

              case "sources":
                // Optional: Store sources if we want to show them during streaming
                break

              case "final_verification":
                setMessages((prev) =>
                  prev.map((msg) =>
                    msg.id === assistantMessageId
                      ? {
                          ...msg,
                          content: data.verified_answer,
                          citations: data.verified_citations,
                        }
                      : msg
                  )
                )
                break

              case "error":
                throw new Error(data.message)

              case "done":
                setIsStreaming(false)
                options?.onComplete?.(accumulatedAnswer)
                break
            }
          } catch (e) {
            console.error("Error parsing JSON chunk:", e, line)
          }
        }
      }
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') {
        console.log("Streaming aborted by user")
      } else {
        const err = error instanceof Error ? error : new Error("Unknown error")
        setIsStreaming(false)
        options?.onError?.(err)

        // Update assistant message with error if failed
        setMessages((prev) =>
          prev.map((msg) =>
            msg.id === assistantMessageId
              ? { ...msg, content: `Error: ${err.message}` }
              : msg
          )
        )
      }
    } finally {
      setIsStreaming(false)
    }
  }, [token])

  return {
    messages,
    setMessages,
    isStreaming,
    sendMessage,
    stopStreaming,
  }
}
