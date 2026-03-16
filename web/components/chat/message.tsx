"use client";

import { memo } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { User, Bot } from "lucide-react";

interface MessageProps {
  role: "human" | "ai" | "user" | "assistant";
  content: string;
}

function MessageComponent({ role, content }: MessageProps) {
  const isUser = role === "human" || role === "user";

  return (
    <div
      className="flex flex-col gap-2 py-3"
      style={{ paddingInline: "var(--spacing-chat-margin)" }}
    >
      {/* Avatar */}
      <div className="flex h-8 w-8 items-center justify-center rounded-full bg-secondary">
        {isUser ? (
          <User className="h-4 w-4 text-secondary-foreground" />
        ) : (
          <Bot className="h-4 w-4 text-primary" />
        )}
      </div>

      {/* Message content */}
      <div className="flex flex-col gap-1 text-sm">
        {isUser ? (
          <p className="text-foreground whitespace-pre-wrap">{content}</p>
        ) : (
          <div className="prose dark:prose-invert max-w-none text-sm">
            <ReactMarkdown
              remarkPlugins={[remarkGfm]}
              components={{
                code({ className, children, ...props }) {
                  const match = /language-(\w+)/.exec(className || "");
                  const isInline = !match;

                  if (isInline) {
                    return (
                      <code
                        className="bg-secondary px-1.5 py-0.5 rounded text-sm"
                        {...props}
                      >
                        {children}
                      </code>
                    );
                  }

                  return (
                    <code className={className} {...props}>
                      {children}
                    </code>
                  );
                },
                a({ children, ...props }) {
                  return (
                    <a
                      className="text-primary underline hover:no-underline"
                      target="_blank"
                      rel="noopener noreferrer"
                      {...props}
                    >
                      {children}
                    </a>
                  );
                },
              }}
            >
              {content}
            </ReactMarkdown>
          </div>
        )}
      </div>
    </div>
  );
}

export const Message = memo(MessageComponent);
