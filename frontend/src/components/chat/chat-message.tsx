"use client";

import { Card } from "@/components/ui/card";
import { User, Bot } from "lucide-react";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface ChatMessageProps {
  role: "user" | "assistant";
  content: string;
  isTyping?: boolean;
}

export function ChatMessage({ role, content, isTyping = false }: ChatMessageProps) {
  const isUser = role === "user";

  return (
    <div className={`flex gap-4 ${isUser ? "justify-end" : "justify-start"}`}>
      {!isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-primary flex items-center justify-center">
          <Bot className="h-5 w-5 text-primary-foreground" />
        </div>
      )}
      
      <div className={`flex-1 max-w-3xl ${isUser ? "flex justify-end" : ""}`}>
        <Card className={`inline-block p-4 ${
          isUser 
            ? "bg-primary text-primary-foreground border-primary" 
            : "bg-card border-border"
        }`}>
          {isTyping ? (
            <div className="flex gap-1">
              <div className="w-2 h-2 bg-current rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
              <div className="w-2 h-2 bg-current rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
              <div className="w-2 h-2 bg-current rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
          ) : (
            <div className="prose prose-sm max-w-none">
              <ReactMarkdown 
                remarkPlugins={[remarkGfm]}
                components={{
                  p: ({children}) => <p className="mb-2 last:mb-0">{children}</p>,
                  strong: ({children}) => <strong className="font-semibold">{children}</strong>,
                  em: ({children}) => <em className="italic">{children}</em>,
                  ul: ({children}) => <ul className="list-disc pl-4 mb-2">{children}</ul>,
                  ol: ({children}) => <ol className="list-decimal pl-4 mb-2">{children}</ol>,
                  li: ({children}) => <li>{children}</li>,
                  code: ({children}) => <code className="bg-black/10 dark:bg-white/10 px-1.5 py-0.5 rounded text-xs font-mono">{children}</code>,
                }}
              >
                {content}
              </ReactMarkdown>
            </div>
          )}
        </Card>
      </div>

      {isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-secondary flex items-center justify-center">
          <User className="h-5 w-5 text-foreground" />
        </div>
      )}
    </div>
  );
}
