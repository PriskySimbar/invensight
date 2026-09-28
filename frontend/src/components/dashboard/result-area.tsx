"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { Code, Database, BarChart3, FileText } from "lucide-react";
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface ResultAreaProps {
  summary: string;
  sqlQuery: string;
  data: Record<string, any>[];
  isPlaceholder?: boolean;
}

// Detect if data is suitable for bar chart
function canRenderBarChart(data: Record<string, any>[]): boolean {
  if (!data || data.length === 0) return false;
  
  const keys = Object.keys(data[0]);
  // Need at least 2 columns: one for labels, one for numeric values
  if (keys.length < 2) return false;
  
  // Check if there's at least one numeric column
  const hasNumeric = keys.some(key => {
    const value = data[0][key];
    return typeof value === 'number' || !isNaN(Number(value));
  });
  
  return hasNumeric;
}

// Transform data for bar chart
function transformToChartData(data: Record<string, any>[]) {
  if (!data || data.length === 0) return [];
  
  const keys = Object.keys(data[0]);
  // Find first non-numeric column for labels
  const labelKey = keys.find(key => typeof data[0][key] === 'string') || keys[0];
  // Find first numeric column for values
  const valueKey = keys.find(key => typeof data[0][key] === 'number' || !isNaN(Number(data[0][key]))) || keys[1];
  
  return data.slice(0, 10).map(row => ({
    name: String(row[labelKey] || 'Unknown'),
    value: Number(row[valueKey] || 0),
  }));
}

export function ResultArea({ summary, sqlQuery, data, isPlaceholder = false }: ResultAreaProps) {
  const showChart = !isPlaceholder && canRenderBarChart(data);
  const chartData = showChart ? transformToChartData(data) : [];
  const tableData = isPlaceholder ? [] : data;
  const columns = tableData.length > 0 ? Object.keys(tableData[0]) : [];

  return (
    <div className="space-y-6">
      {/* Summary Card */}
      <Card className="border-border shadow-sm">
        <CardHeader className="pb-4">
          <CardTitle className="text-lg font-semibold text-foreground flex items-center gap-2">
            <FileText className="h-5 w-5 text-primary" />
            Analysis Summary
          </CardTitle>
        </CardHeader>
        <CardContent>
          {isPlaceholder ? (
            <div className="flex items-center justify-center py-8">
              <p className="text-sm text-muted-foreground text-center">
                Results will appear here after analysis. Ask a question above to get started.
              </p>
            </div>
          ) : (
            <div className="prose prose-sm max-w-none text-foreground">
              <ReactMarkdown 
                remarkPlugins={[remarkGfm]}
                components={{
                  p: ({children}) => <p className="mb-3 text-foreground leading-relaxed">{children}</p>,
                  strong: ({children}) => <strong className="font-semibold text-foreground">{children}</strong>,
                  em: ({children}) => <em className="italic text-foreground">{children}</em>,
                  ul: ({children}) => <ul className="list-disc pl-6 mb-3 space-y-1">{children}</ul>,
                  ol: ({children}) => <ol className="list-decimal pl-6 mb-3 space-y-1">{children}</ol>,
                  li: ({children}) => <li className="text-foreground">{children}</li>,
                  code: ({children}) => <code className="bg-secondary px-1.5 py-0.5 rounded text-xs font-mono text-foreground">{children}</code>,
                }}
              >
                {summary}
              </ReactMarkdown>
            </div>
          )}
        </CardContent>
      </Card>

      {/* SQL Query Card */}
      {!isPlaceholder && sqlQuery && (
        <Card className="border-border shadow-sm">
          <CardHeader className="pb-4">
            <CardTitle className="text-lg font-semibold text-foreground flex items-center gap-2">
              <Database className="h-5 w-5 text-primary" />
              Executed SQL Query
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="bg-secondary/30 border border-border rounded-lg p-4">
              <pre className="text-xs text-foreground font-mono overflow-x-auto whitespace-pre-wrap">
                {sqlQuery}
              </pre>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Data Table */}
      {tableData.length > 0 && (
        <Card className="border-border shadow-sm">
          <CardHeader className="pb-4">
            <CardTitle className="text-lg font-semibold text-foreground flex items-center gap-2">
              <Database className="h-5 w-5 text-primary" />
              Data Results 
              <Badge variant="secondary" className="ml-2">
                {tableData.length} rows
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="rounded-lg border border-border overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="bg-secondary/30 border-b border-border">
                      {columns.map((col) => (
                        <th key={col} className="px-4 py-3 text-left font-semibold text-foreground text-xs uppercase tracking-wider">
                          {col.replace(/_/g, ' ')}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {tableData.slice(0, 20).map((row, index) => (
                      <tr key={index} className="border-b border-border hover:bg-accent/30 transition-colors">
                        {columns.map((col) => (
                          <td key={col} className="px-4 py-3 text-foreground text-sm">
                            {String(row[col] ?? '-')}
                          </td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
              {tableData.length > 20 && (
                <div className="bg-secondary/30 px-4 py-2 text-center">
                  <p className="text-xs text-muted-foreground">
                    Showing first 20 of {tableData.length} rows
                  </p>
                </div>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Chart */}
      {showChart && chartData.length > 0 && (
        <Card className="border-border shadow-sm">
          <CardHeader className="pb-4">
            <CardTitle className="text-lg font-semibold text-foreground flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-primary" />
              Visual Analytics
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={chartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" vertical={false} />
                  <XAxis 
                    dataKey="name" 
                    stroke="var(--muted-foreground)"
                    fontSize={12}
                    tick={{ fill: 'var(--muted-foreground)' }}
                    axisLine={{ stroke: 'var(--border)' }}
                    tickLine={{ stroke: 'var(--border)' }}
                  />
                  <YAxis 
                    stroke="var(--muted-foreground)"
                    fontSize={12}
                    tick={{ fill: 'var(--muted-foreground)' }}
                    axisLine={{ stroke: 'var(--border)' }}
                    tickLine={{ stroke: 'var(--border)' }}
                  />
                  <Tooltip 
                    contentStyle={{
                      backgroundColor: "var(--card)",
                      border: "1px solid var(--border)",
                      borderRadius: "var(--radius)",
                      color: "var(--foreground)",
                    }}
                    itemStyle={{ color: "var(--foreground)" }}
                  />
                  <Bar 
                    dataKey="value" 
                    fill="var(--primary)" 
                    radius={[4, 4, 0, 0]}
                    className="hover:opacity-80 transition-opacity"
                  />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
