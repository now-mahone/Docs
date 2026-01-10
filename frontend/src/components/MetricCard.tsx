// Created: 2025-12-28
import React from 'react';
import { ArrowUpRight, ArrowDownRight } from 'lucide-react';
import { cn } from '@/lib/utils';

interface MetricCardProps {
  label: string;
  value: string | number;
  subValue?: string;
  trend?: 'up' | 'down';
  className?: string;
}

export function MetricCard({ label, value, subValue, trend, className, tooltip }: MetricCardProps & { tooltip?: string }) {
  return (
    <div className={cn(
      "bg-card border border-border p-4 flex flex-col gap-1 group relative rounded-xl shadow-sm",
      className
    )}>
      {tooltip && (
        <div className="absolute -top-8 left-0 bg-white border border-border px-2 py-1 text-[8px] text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10 whitespace-nowrap shadow-sm">
          {tooltip}
        </div>
      )}
      <div className="text-[10px] text-muted-foreground font-sans font-bold tracking-tighter uppercase">
        {label}
      </div>
      <div className="flex items-baseline gap-2">
        <div className="text-2xl font-heading font-bold text-foreground tracking-tight">
          {value}
        </div>
        {trend && (
          <div className={cn(
            "flex items-center text-sm font-sans font-bold",
            trend === 'up' ? "text-primary" : "text-destructive"
          )}>
            {trend === 'up' ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
          </div>
        )}
      </div>
      {subValue && (
        <div className="text-xs text-muted-foreground font-sans font-medium">
          {subValue}
        </div>
      )}
    </div>
  );
}
