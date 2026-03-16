"use client";

import {
  useState,
  useRef,
  useCallback,
  forwardRef,
  useImperativeHandle,
  type KeyboardEvent,
} from "react";
import { cn } from "@/lib/utils";
import { Send, Loader2 } from "lucide-react";

interface ChatInputProps {
  onSubmit: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export interface ChatInputHandle {
  focus: () => void;
}

export const ChatInput = forwardRef<ChatInputHandle, ChatInputProps>(
  function ChatInput(
    { onSubmit, disabled = false, placeholder = "Type a message..." },
    ref
  ) {
    const [value, setValue] = useState("");
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    useImperativeHandle(ref, () => ({
      focus: () => {
        textareaRef.current?.focus();
      },
    }));

    const handleSubmit = useCallback(() => {
      const trimmedValue = value.trim();
      if (!trimmedValue || disabled) return;

      onSubmit(trimmedValue);
      setValue("");

      if (textareaRef.current) {
        textareaRef.current.style.height = "auto";
      }
    }, [value, disabled, onSubmit]);

    const handleKeyDown = useCallback(
      (e: KeyboardEvent<HTMLTextAreaElement>) => {
        if (e.key === "Enter" && !e.shiftKey) {
          e.preventDefault();
          handleSubmit();
        }
      },
      [handleSubmit]
    );

    const handleInput = useCallback(() => {
      const textarea = textareaRef.current;
      if (textarea) {
        textarea.style.height = "auto";
        textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
      }
    }, []);

    return (
      <div className="border-t border-border bg-background">
        <div
          className="py-4"
          style={{ paddingInline: "var(--spacing-chat-margin)" }}
        >
          <div className="mx-auto" style={{ maxWidth: "min(768px, 70vw)" }}>
            <div className="relative flex items-end gap-2 rounded-xl border border-border bg-card p-2">
              <textarea
                ref={textareaRef}
                value={value}
                onChange={(e) => setValue(e.target.value)}
                onKeyDown={handleKeyDown}
                onInput={handleInput}
                placeholder={placeholder}
                disabled={disabled}
                rows={1}
                className={cn(
                  "flex-1 resize-none bg-transparent px-2 py-1.5 text-sm outline-none placeholder:text-muted-foreground",
                  "max-h-[200px] min-h-[36px]",
                  disabled && "cursor-not-allowed opacity-50"
                )}
              />
              <button
                type="button"
                onClick={handleSubmit}
                disabled={disabled || !value.trim()}
                className={cn(
                  "flex h-9 w-9 shrink-0 items-center justify-center rounded-lg transition-colors",
                  value.trim() && !disabled
                    ? "bg-primary text-primary-foreground hover:bg-primary/90"
                    : "bg-muted text-muted-foreground cursor-not-allowed"
                )}
              >
                {disabled ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <Send className="h-4 w-4" />
                )}
              </button>
            </div>
            <p className="mt-2 text-center text-xs text-muted-foreground">
              Press Enter to send, Shift+Enter for new line
            </p>
          </div>
        </div>
      </div>
    );
  }
);
