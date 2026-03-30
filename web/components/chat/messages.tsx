"use client";

import { useEffect, useRef } from "react";
import type { Message } from "@langchain/langgraph-sdk";
import { Message as MessageComponent } from "./message";
import { Bot, Loader2 } from "lucide-react";

interface MessagesProps {
  messages: Message[];
  isLoading?: boolean;
}

export function Messages({ messages, isLoading }: MessagesProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isLoading]);

  const getMessageContent = (content: Message["content"]): string => {
    if (typeof content === "string") {
      return content;
    }
    return content
      .filter(
        (part): part is { type: "text"; text: string } => part.type === "text"
      )
      .map((part) => part.text)
      .join("");
  };

  const getMessageRole = (message: Message): "human" | "ai" => {
    if (message.type === "human") {
      return "human";
    }
    return "ai";
  };

  if (messages.length === 0 && !isLoading) {
    return (
      <div className="flex flex-1 flex-col items-center justify-center gap-4 p-8">
        <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary/10">
          <Bot className="h-8 w-8 text-primary" />
        </div>
        <div className="text-center">
          <h2 className="text-xl font-semibold text-foreground">
            Hi! I&apos;m StudyBuddy
          </h2>
          <p className="mt-2 text-sm text-muted-foreground">
            Ask me about your study notes or any topic you&apos;re learning.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-1 flex-col overflow-y-auto">
      <div
        className="flex flex-col gap-1 py-4"
        style={{ paddingBottom: "120px" }}
      >
        {messages.map((message, index): React.ReactNode => {
          // Hide tool result messages — these are raw tool output the LLM
          // reads internally, not content intended for the user.
          if (message.type === "tool") return null;

          // Hide intermediate AI messages that contain only tool call
          // requests (no prose response yet). These are the agent's
          // "thinking" steps between receiving user input and producing
          // the final answer.
          if (
            message.type === "ai" &&
            Array.isArray((message as { tool_calls?: unknown[] }).tool_calls) &&
            ((message as { tool_calls: unknown[] }).tool_calls).length > 0 &&
            !getMessageContent(message.content).trim()
          ) {
            return null;
          }

          const content = getMessageContent(message.content);
          const role = getMessageRole(message);

          if (!content.trim()) return null;

          return (
            <MessageComponent
              key={message.id ?? `msg-${index}`}
              role={role}
              content={content}
            />
          );
        })}

        {isLoading && messages.at(-1)?.type !== "ai" && (
          <div
            className="flex flex-col gap-2 py-3"
            style={{ paddingInline: "var(--spacing-chat-margin)" }}
          >
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-secondary">
              <Bot className="h-4 w-4 text-primary" />
            </div>
            <div className="flex items-center gap-2 text-sm text-muted-foreground">
              <Loader2 className="h-4 w-4 animate-spin" />
              <span>Thinking...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>
    </div>
  );
}
