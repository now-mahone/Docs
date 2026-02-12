// Created: 2026-02-12
import React from 'react';

interface PieChartProps {
  data: Array<{
    name: string;
    value: number;
    color: string;
  }>;
  size?: number;
  strokeWidth?: number;
}

export const PieChart: React.FC<PieChartProps> = ({ data, size = 96, strokeWidth = 12 }) => {
  const total = data.reduce((acc, item) => acc + item.value, 0);
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  
  let currentOffset = 0;

  return (
    <div className="relative" style={{ width: size, height: size }}>
      <svg width={size} height={size} className="transform -rotate-90">
        {total === 0 ? (
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="transparent"
            stroke="#22252a"
            strokeWidth={strokeWidth}
          />
        ) : (
          data.map((item, index) => {
            const percentage = (item.value / total) * 100;
            const strokeDasharray = (percentage * circumference) / 100;
            const strokeDashoffset = -currentOffset;
            currentOffset += strokeDasharray;

            return (
              <circle
                key={index}
                cx={size / 2}
                cy={size / 2}
                r={radius}
                fill="transparent"
                stroke={item.color}
                strokeWidth={strokeWidth}
                strokeDasharray={`${strokeDasharray} ${circumference - strokeDasharray}`}
                strokeDashoffset={strokeDashoffset}
                className="transition-all duration-500 ease-in-out"
              />
            );
          })
        )}
      </svg>
    </div>
  );
};