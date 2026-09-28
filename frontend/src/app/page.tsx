"use client";

import { useState, useRef, useEffect } from "react";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { ChatMessage } from "@/components/chat/chat-message";
import { ChatInput } from "@/components/chat/chat-input";
import { SqlResult } from "@/components/chat/sql-result";
import { ChartResult } from "@/components/chat/chart-result";
import { analyzeQuestion, AnalyzeResponse, API_BASE_URL } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import Image from "next/image";
import { Button } from "@/components/ui/button";
import { Upload, FileText, Image as ImageIcon, Database } from "lucide-react";

type Mode = "sql" | "rag" | "vision";

interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  sqlQuery?: string;
  data?: Record<string, any>[];
  isTyping?: boolean;
  mode?: Mode;
}

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [mode, setMode] = useState<Mode>("sql");
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { error: showError, success: showSuccess } = useToast();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setUploadedFile(file);
      showSuccess("File Uploaded", `${file.name} ready for ${mode} analysis`);
    }
  };

  const handleSend = async (question: string) => {
    const userMessage: Message = {
      id: Date.now().toString(),
      role: "user",
      content: question,
      mode,
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    // Add typing indicator
    const typingMessage: Message = {
      id: (Date.now() + 1).toString(),
      role: "assistant",
      content: "",
      isTyping: true,
      mode,
    };
    setMessages((prev) => [...prev, typingMessage]);

    try {
      let response: any;

      if (mode === "sql") {
        response = await analyzeQuestion(question);
      } else if (mode === "rag") {
        // Query RAG directly (document already auto-loaded)
        const queryRes = await fetch(`${API_BASE_URL}/api/v1/rag/query`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ question }),
        });
        
        if (!queryRes.ok) throw new Error("Failed to query documents");
        response = await queryRes.json();
      } else if (mode === "vision" && uploadedFile) {
        const formData = new FormData();
        formData.append("file", uploadedFile);
        formData.append("question", question);
        
        const visionRes = await fetch(`${API_BASE_URL}/api/v1/vision/analyze`, {
          method: "POST",
          body: formData,
        });
        
        if (!visionRes.ok) throw new Error("Failed to analyze image");
        response = await visionRes.json();
      } else if (mode === "vision") {
        throw new Error("Please upload an image for Vision mode");
      } else {
        throw new Error("Invalid mode");
      }
      
      // Remove typing indicator and add actual response
      setMessages((prev) => {
        const filtered = prev.filter((msg) => msg.id !== typingMessage.id);
        return [
          ...filtered,
          {
            id: (Date.now() + 2).toString(),
            role: "assistant",
            content: response.summary || response.answer || response.analysis || "Analysis complete",
            sqlQuery: response.sql_query,
            data: response.data,
            mode,
          },
        ];
      });

      if (response.is_error) {
        showError(
          "Analysis Error",
          response.summary || "Failed to analyze your question. Please try again."
        );
      }
    } catch (err) {
      console.error("API Error in handleSend:", err);
      setMessages((prev) => {
        const filtered = prev.filter((msg) => msg.id !== typingMessage.id);
        return [
          ...filtered,
          {
            id: (Date.now() + 2).toString(),
            role: "assistant",
            content: "Sorry, I encountered an error processing your request. Please try again.",
            mode,
          },
        ];
      });
      showError(
        "Connection Error",
        err instanceof Error ? err.message : "Failed to connect to the server."
      );
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <DashboardLayout>
      <div className="flex flex-col h-[calc(100vh-4rem)]">
        {/* Mode Selector */}
        <div className="border-b border-border px-4 py-3 bg-background">
          <div className="max-w-4xl mx-auto flex items-center gap-4">
            <div className="flex gap-2">
              <Button
                variant={mode === "sql" ? "default" : "outline"}
                size="sm"
                onClick={() => setMode("sql")}
                className="flex items-center gap-2"
              >
                <Database className="w-4 h-4" />
                SQL Analysis
              </Button>
              <Button
                variant={mode === "rag" ? "default" : "outline"}
                size="sm"
                onClick={() => setMode("rag")}
                className="flex items-center gap-2"
              >
                <FileText className="w-4 h-4" />
                Document Q&A
              </Button>
              <Button
                variant={mode === "vision" ? "default" : "outline"}
                size="sm"
                onClick={() => setMode("vision")}
                className="flex items-center gap-2"
              >
                <ImageIcon className="w-4 h-4" />
                Vision/OCR
              </Button>
            </div>
            
            {(mode === "rag" || mode === "vision") && (
              <div className="flex items-center gap-2 ml-auto">
                <span className="text-sm text-muted-foreground">
                  {mode === "rag" ? "📄 Sample SOP loaded - Ready to query" : "📷 Upload image to analyze"}
                </span>
                {mode === "vision" && (
                  <label className="flex items-center gap-2 px-3 py-1.5 text-sm border border-border rounded-md hover:bg-accent cursor-pointer">
                    <Upload className="w-4 h-4" />
                    {uploadedFile ? uploadedFile.name : "Upload Image"}
                    <input
                      type="file"
                      accept="image/*"
                      onChange={handleFileUpload}
                      className="hidden"
                    />
                  </label>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Chat Container */}
        <div className="flex-1 overflow-y-auto px-4 py-6">
          <div className="max-w-4xl mx-auto space-y-6">
            {messages.length === 0 ? (
              <div className="flex flex-col items-center justify-center h-full py-12">
                <div className="text-center space-y-6">
                  <div className="flex justify-center">
                    <Image 
                      src="/logo.png" 
                      alt="InvenSight Logo" 
                      width={80} 
                      height={80}
                      className="object-contain"
                    />
                  </div>
                  <h1 className="text-3xl font-semibold text-foreground">
                    InvenSight AI
                  </h1>
                  <p className="text-muted-foreground max-w-md">
                    {mode === "sql" && "Ask anything about your warehouse inventory, transactions, and analytics."}
                    {mode === "rag" && "Upload a PDF document (SOPs, manuals, reports) and ask questions about it."}
                    {mode === "vision" && "Upload warehouse images to analyze inventory, count boxes, or detect damages."}
                  </p>
                  <div className="flex gap-2 flex-wrap justify-start">
                    {mode === "sql" && [
                      "Show top 5 products by stock",
                      "Warehouse inventory summary",
                      "Recent transactions",
                    ].map((suggestion) => (
                      <button
                        key={suggestion}
                        onClick={() => handleSend(suggestion)}
                        className="px-4 py-2 text-sm border border-border rounded-lg hover:bg-accent transition-colors text-foreground"
                      >
                        {suggestion}
                      </button>
                    ))}
                    {mode === "rag" && [
                      "What is the return procedure?",
                      "How to handle damaged goods?",
                      "What are the warehouse safety rules?",
                    ].map((suggestion) => (
                      <button
                        key={suggestion}
                        onClick={() => handleSend(suggestion)}
                        className="px-4 py-2 text-sm border border-border rounded-lg hover:bg-accent transition-colors text-foreground"
                      >
                        {suggestion}
                      </button>
                    ))}
                    {mode === "vision" && [
                      "Count the boxes in this image",
                      "Are there any damaged items?",
                      "What products are visible?",
                    ].map((suggestion) => (
                      <button
                        key={suggestion}
                        onClick={() => handleSend(suggestion)}
                        className="px-4 py-2 text-sm border border-border rounded-lg hover:bg-accent transition-colors text-foreground"
                      >
                        {suggestion}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            ) : (
              <>
                {messages.map((message) => (
                  <div key={message.id}>
                    <ChatMessage
                      role={message.role}
                      content={message.content}
                      isTyping={message.isTyping}
                    />
                    {message.role === "assistant" && !message.isTyping && message.sqlQuery && (
                      <>
                        <SqlResult
                          sqlQuery={message.sqlQuery}
                          data={message.data || []}
                        />
                        {message.data && message.data.length > 0 && (
                          <ChartResult data={message.data} />
                        )}
                      </>
                    )}
                  </div>
                ))}
                <div ref={messagesEndRef} />
              </>
            )}
          </div>
        </div>

        {/* Input Area */}
        <ChatInput onSend={handleSend} disabled={isLoading} placeholder={
          mode === "sql" ? "Ask about warehouse data..." :
          mode === "rag" ? "Ask about your document..." :
          "Ask about this image..."
        } />
      </div>
    </DashboardLayout>
  );
}
