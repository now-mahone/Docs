// Created: 2026-01-30
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
  Area,
  AreaChart,
  ComposedChart,
} from 'recharts';

interface ETHComparisonChartProps {
  data: Array<{
    time: string;
    eth: number;
    simulated: number;
    isBiWeekly?: boolean;
  }>;
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-gradient-to-b from-[#22252a] to-[#000000] rounded-sm p-4 shadow-lg border border-[#444a4f]">
        <p className="text-xs font-bold text-[#ffffff] mb-2">{label}</p>
        {payload.filter((entry: any) => entry.name !== 'Kerne Realized').map((entry: any, index: number) => (
          <p key={index} className="text-xs font-medium" style={{ color: entry.color }}>
            {entry.name}: ${entry.value.toLocaleString()}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

export const ETHComparisonChart: React.FC<ETHComparisonChartProps> = ({ data }) => {
  return (
    <div className="w-full h-full min-h-[300px] lg:min-h-[450px]">
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart
          data={data}
          margin={{
            top: 10,
            right: 10,
            left: 0,
            bottom: 20,
          }}
        >
          <defs>
            <linearGradient id="kerneGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#4c7be7" stopOpacity={0.3}/>
              <stop offset="95%" stopColor="#4c7be7" stopOpacity={0}/>
            </linearGradient>
          </defs>
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
            tickFormatter={(value: number) => `$${value.toLocaleString()}`}
            domain={['auto', 'auto']}
            tick={(props: any) => {
              const { x, y, payload } = props;
              return (
                <g transform={`translate(${x},${y})`}>
                  <text 
                    x={15}
                    y={0} 
                    dy={4} 
                    textAnchor="start"
                    fill="#aab9be" 
                    fontSize="11px" 
                    fontWeight={500}
                  >
                    ${payload.value.toLocaleString()}
                  </text>
                </g>
              );
            }}
          />
          <Tooltip content={<CustomTooltip />} />
          <Area
            name="Kerne Simulated"
            type="linear"
            dataKey="simulated"
            stroke="#4c7be7"
            strokeWidth={2}
            fill="url(#kerneGradient)"
            dot={false}
          />
          <Line
            name="ETH Index"
            type="linear"
            dataKey="eth"
            stroke="#babefb"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4, stroke: '#16191c', strokeWidth: 2 }}
          />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
};