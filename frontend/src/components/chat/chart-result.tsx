"use client";

import { Card, CardContent } from "@/components/ui/card";
import { BarChart3 } from "lucide-react";
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";

interface ChartResultProps {
  data: Record<string, any>[];
}

function canRenderBarChart(data: Record<string, any>[]): boolean {
  if (!data || data.length === 0) return false;
  
  const keys = Object.keys(data[0]);
  if (keys.length < 2) return false;
  
  const hasNumeric = keys.some(key => {
    const value = data[0][key];
    return typeof value === 'number' || !isNaN(Number(value));
  });
  
  return hasNumeric;
}

function transformToChartData(data: Record<string, any>[]) {
  if (!data || data.length === 0) return [];
  
  const keys = Object.keys(data[0]);
  const labelKey = keys.find(key => typeof data[0][key] === 'string') || keys[0];
  const valueKey = keys.find(key => typeof data[0][key] === 'number' || !isNaN(Number(data[0][key]))) || keys[1];
  
  return data.slice(0, 10).map(row => ({
    name: String(row[labelKey] || 'Unknown'),
    value: Number(row[valueKey] || 0),
  }));
}

export function ChartResult({ data }: ChartResultProps) {
  const showChart = canRenderBarChart(data);
  const chartData = showChart ? transformToChartData(data) : [];

  if (!showChart || chartData.length === 0) return null;

  return (
    <Card className="border-border mt-4">
      <CardContent className="p-4">
        <div className="flex items-center gap-2 mb-4">
          <BarChart3 className="h-4 w-4 text-primary" />
          <span className="text-xs font-semibold text-foreground uppercase tracking-wider">
            Visual Analytics
          </span>
        </div>
        <div className="h-64">
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
  );
}
