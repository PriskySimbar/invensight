"use client";

import { Card, CardContent } from "@/components/ui/card";
import { Code, Database } from "lucide-react";

interface SqlResultProps {
  sqlQuery: string;
  data: Record<string, any>[];
}

export function SqlResult({ sqlQuery, data }: SqlResultProps) {
  const columns = data.length > 0 ? Object.keys(data[0]) : [];

  return (
    <div className="space-y-4 mt-4">
      {/* SQL Query */}
      <Card className="border-border bg-secondary/30">
        <CardContent className="p-4">
          <div className="flex items-center gap-2 mb-2">
            <Database className="h-4 w-4 text-primary" />
            <span className="text-xs font-semibold text-foreground uppercase tracking-wider">
              Executed SQL
            </span>
          </div>
          <pre className="text-xs text-foreground font-mono overflow-x-auto whitespace-pre-wrap">
            {sqlQuery}
          </pre>
        </CardContent>
      </Card>

      {/* Data Table */}
      {data.length > 0 && (
        <Card className="border-border">
          <CardContent className="p-0">
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
                  {data.slice(0, 10).map((row, index) => (
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
            {data.length > 10 && (
              <div className="bg-secondary/30 px-4 py-2 text-center">
                <p className="text-xs text-muted-foreground">
                  Showing first 10 of {data.length} rows
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
