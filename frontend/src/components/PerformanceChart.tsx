// Created: 2025-12-30
'use client';

import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceLine,
  Area,
  AreaChart,
  ComposedChart,
} from 'recharts';

interface PerformanceChartProps {
  data: Array<{
    time: string;
    apy: number;
    avg: number;
    isBiWeekly?: boolean;
  }>;
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-gradient-to-b from-[#22252a] to-[#000000] rounded-sm p-4 shadow-lg border border-[#444a4f]">
        <p className="text-xs font-bold text-[#ffffff] mb-2">{label}</p>
        <p className="text-xs font-medium text-[#37d097]">
          Kerne APY: {payload[0].value.toFixed(2)}%
        </p>
      </div>
    );
  }
  return null;
};

export const PerformanceChart: React.FC<PerformanceChartProps> = ({ data }) => {
  const average = data.length > 0 ? data[0].avg : 0;

  return (
    <div className="w-full h-full min-h-[300px] lg:min-h-[450px]">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart
          data={data}
          margin={{
            top: 10,
            right: 10,
            left: -20,
            bottom: 20,
          }}
        >
          <ReferenceLine 
            y={average} 
            stroke="#444a4f" 
            strokeWidth={2}
            label={{ 
              value: `Avg ${average}%`, 
              position: 'insideBottomRight', 
              fill: '#444a4f', 
              fontSize: 10, 
              fontWeight: 700, 
              offset: 10 
            }} 
          />
          <CartesianGrid stroke="#22252a" vertical={false} horizontal={true} strokeDasharray="none" />
          <XAxis 
            dataKey="time" 
            stroke="#aab9be" 
            style={{ fontSize: '11px', fontWeight: 500 }}
            tickLine={false}
            axisLine={false}
            tick={(props: any) => {
              const { x, y, payload } = props;
              const entry = data[payload.index];
              if (entry && entry.isBiWeekly) {
                const isLast = payload.index === data.length - 1;
                return (
                  <g transform={`translate(${x},${y})`}>
                    <text 
                      x={0} 
                      y={0} 
                      dy={16} 
                      textAnchor={isLast ? "end" : "middle"} 
                      fill="#aab9be" 
                      fontSize="11px" 
                      fontWeight={500}
                    >
                      {payload.value}
                    </text>
                  </g>
                );
              }
              return null;
            }}
            interval={0}
          />
          <YAxis 
            stroke="#aab9be" 
            style={{ fontSize: '11px', fontWeight: 500 }}
            tickLine={false}
            axisLine={false}
            tickFormatter={(value: number) => `${value}%`}
            domain={[10, 30]}
            tick={{ fill: '#aab9be' }}
            label={{ value: 'APY (%)', angle: -90, position: 'insideLeft', style: { fontSize: '11px', fontWeight: 600, fill: '#aab9be', textAnchor: 'middle' }, dx: -10 }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Line
            name="Kerne APY"
            type="linear"
            dataKey="apy"
            stroke="#37d097"
            strokeWidth={3}
            dot={false}
            activeDot={{ r: 6, stroke: '#16191c', strokeWidth: 2 }}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
};
