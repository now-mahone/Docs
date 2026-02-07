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
      "bg-white border border-[#f1f1ed] p-6 flex flex-col gap-1 group relative rounded-sm",
      className
    )}>
      {tooltip && (
        <div className="absolute -top-10 left-0 bg-[#000000] text-white px-3 py-1.5 rounded-sm text-xs font-bold opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none z-10 whitespace-nowrap">
          {tooltip}
        </div>
      )}
      <div className="text-xs text-zinc-400 font-sans font-bold tracking-tight">
        {label}
      </div>
      <div className="flex items-baseline gap-2 mt-1">
        <div className="text-xl font-heading font-medium text-[#000000] tracking-tight">
          {value}
        </div>
        {trend && (
          <div className={cn(
            "flex items-center text-s font-sans font-bold",
            trend === 'up' ? "text-primary" : "text-red-500"
          )}>
            {trend === 'up' ? <ArrowUpRight size={16} /> : <ArrowDownRight size={16} />}
          </div>
        )}
      </div>
      {subValue && (
        <div className="text-xs text-zinc-500 font-sans font-medium mt-1">
          {subValue}
        </div>
      )}
    </div>
  );
}
