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
      "bg-obsidian border border-zinc-800 p-4 flex flex-col gap-1 group relative",
      className
    )}>
      {tooltip && (
        <div className="absolute -top-8 left-0 bg-zinc-900 border border-zinc-800 px-2 py-1 text-[8px] text-zinc-400 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10 whitespace-nowrap">
          {tooltip}
        </div>
      )}
      <div className="text-[10px] text-zinc-500 font-mono tracking-tighter uppercase">
        {label}
      </div>
      <div className="flex items-baseline gap-2">
        <div className="text-2xl font-mono text-zinc-100 tracking-tight">
          {value}
        </div>
        {trend && (
          <div className={cn(
            "flex items-center text-xs font-mono",
            trend === 'up' ? "text-emerald-500" : "text-rose-500"
          )}>
            {trend === 'up' ? <ArrowUpRight size={14} /> : <ArrowDownRight size={14} />}
          </div>
        )}
      </div>
      {subValue && (
        <div className="text-xs text-zinc-500 font-mono">
          {subValue}
        </div>
      )}
    </div>
  );
}
