// Created: 2026-01-30
'use client';

import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';
import { PieChart as PieChartIcon, Activity } from 'lucide-react';

const data = [
  { name: 'On Chain ETH', value: 40, color: '#37d097' },
  { name: 'Mirror Assets', value: 30, color: '#f82b6c' },
  { name: 'LST Reserves', value: 30, color: '#4c7be7' },
];

const CustomTooltip = ({ active, payload }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-gradient-to-b from-[#22252a] to-[#000000] rounded-sm p-4 shadow-lg border border-[#444a4f]">
        <p className="text-xs font-bold text-[#ffffff] mb-1">{payload[0].name}</p>
        <p className="text-xs font-medium" style={{ color: payload[0].payload.color }}>
          {payload[0].value}% Allocation
        </p>
      </div>
    );
  }
  return null;
};

export const AssetComposition = () => {
  return (
    <div className="w-full h-full flex flex-col p-6 lg:p-8 bg-gradient-to-b from-[#22252a] via-[#16191c] to-[#000000]">
      <div className="flex items-start justify-between mb-8">
        <div>
          <span className="text-xs font-bold text-[#aab9be] uppercase tracking-wide block mb-1">Portfolio Breakdown</span>
          <p className="text-xl font-heading font-medium text-[#ffffff]">Asset Composition</p>
        </div>
        <PieChartIcon size={16} className="text-[#aab9be] mt-1" />
      </div>

      <div className="flex-1 w-full min-h-0 relative flex flex-col justify-between">
        <div className="h-[250px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Pie
                data={data}
                cx="50%"
                cy="50%"
                innerRadius={60}
                outerRadius={80}
                paddingAngle={0}
                dataKey="value"
                stroke="none"
              >
                {data.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip content={<CustomTooltip />} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Legend */}
        <div className="mt-8 p-6 bg-transparent border border-[#444a4f] rounded-sm w-full space-y-4">
          {data.map((item, idx) => (
            <div key={idx} className="flex items-center justify-between gap-4">
              <div className="flex items-center gap-2">
                <div className="w-1.5 h-1.5 rounded-full shrink-0" style={{ backgroundColor: item.color }} />
                <span className="text-xs font-medium text-[#aab9be]">{item.name}</span>
              </div>
              <span className="text-xs font-bold text-[#ffffff] uppercase font-heading">{item.value}%</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};