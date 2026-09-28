"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Sparkles } from "lucide-react";

interface AnalyzeInputProps {
  onAnalyze?: (question: string) => void;
}

export function AnalyzeInput({ onAnalyze }: AnalyzeInputProps) {
  const [question, setQuestion] = useState("");

  const handleAnalyze = () => {
    if (question.trim() && onAnalyze) {
      onAnalyze(question.trim());
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleAnalyze();
    }
  };

  return (
    <Card className="border-border">
      <CardHeader>
        <CardTitle className="text-xl font-semibold text-foreground">
          Ask InvenSight AI
        </CardTitle>
        <CardDescription className="text-muted-foreground">
          Ask questions about your warehouse inventory, transactions, and analytics
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="flex gap-3">
          <Input
            placeholder="e.g., 'Show me the top 5 products by stock level in Jakarta warehouse'"
            className="flex-1 border-border bg-background text-foreground placeholder:text-muted-foreground"
            value={question}
            onChange={(e) => setQuestion(e.target.value)}
            onKeyPress={handleKeyPress}
          />
          <Button 
            className="bg-primary text-primary-foreground hover:bg-primary/90"
            onClick={handleAnalyze}
            disabled={!question.trim()}
          >
            <Sparkles className="mr-2 h-4 w-4" />
            Analyze
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
