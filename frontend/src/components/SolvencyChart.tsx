// Created: 2025-12-30
import React from 'react';

interface SolvencyChartProps {
  breakdown: Array<{
    name: string;
    value: string;
    type: string;
  }>;
}

export const SolvencyChart: React.FC<SolvencyChartProps> = ({ breakdown }) => {
  const total = breakdown.reduce((acc, item) => acc + parseFloat(item.value), 0);

  return (
    <div className="space-y-4">
      <div className="flex h-8 w-full bg-zinc-900 overflow-hidden border border-zinc-800">
        {breakdown.map((item, index) => {
          const percentage = (parseFloat(item.value) / total) * 100;
          return (
            <div
              key={item.name}
              style={{ width: `${percentage}%` }}
              className={`h-full transition-all duration-500 ${
                item.type === 'on-chain' ? 'bg-emerald-500' : 
                index % 2 === 0 ? 'bg-zinc-500' : 'bg-zinc-700'
              }`}
              title={`${item.name}: ${percentage.toFixed(2)}%`}
            />
          );
        })}
      </div>
      
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {breakdown.map((item, index) => (
          <div key={item.name} className="flex items-center space-x-2">
            <div className={`w-3 h-3 ${
              item.type === 'on-chain' ? 'bg-emerald-500' : 
              index % 2 === 0 ? 'bg-zinc-500' : 'bg-zinc-700'
            }`} />
            <div className="flex flex-col">
              <span className="text-[10px] text-zinc-500 uppercase tracking-widest">{item.name}</span>
              <span className="text-sm font-bold text-zinc-200">{item.value} ETH</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
