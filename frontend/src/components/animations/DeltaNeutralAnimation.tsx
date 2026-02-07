// Created: 2026-01-16
// Animated SVG for Delta-Neutral Vaults card
'use client';

import React from 'react';

export default function DeltaNeutralAnimation() {
  return (
    <div className="w-full h-full min-h-[200px] flex items-center justify-center bg-[#ebf9f4]">
      <svg
        viewBox="0 0 400 300"
        className="w-full h-full max-w-[300px]"
        xmlns="http://www.w3.org/2000/svg"
      >
        {/* Central balance beam */}
        <g className="origin-center">
          <line
            x1="100"
            y1="150"
            x2="300"
            y2="150"
            stroke="#000000"
            strokeWidth="4"
            strokeLinecap="round"
            className="animate-balance-beam"
          />
          {/* Pivot point */}
          <circle cx="200" cy="150" r="8" fill="#000000" />
          
          {/* Left weight */}
          <g className="animate-weight-left">
            <line x1="120" y1="150" x2="120" y2="180" stroke="#000000" strokeWidth="2" />
            <rect x="100" y="180" width="40" height="40" rx="4" fill="#000000" className="animate-pulse-slow" />
          </g>
          
          {/* Right weight */}
          <g className="animate-weight-right">
            <line x1="280" y1="150" x2="280" y2="180" stroke="#000000" strokeWidth="2" />
            <rect x="260" y="180" width="40" height="40" rx="4" fill="#000000" className="animate-pulse-slow" />
          </g>
        </g>
        
        {/* Orbiting circles representing hedging */}
        <circle cx="200" cy="100" r="6" fill="#000000" className="animate-orbit-1" />
        <circle cx="200" cy="100" r="4" fill="#000000" className="animate-orbit-2" />
        <circle cx="200" cy="100" r="5" fill="#000000" className="animate-orbit-3" />
        
        {/* Base stand */}
        <polygon points="180,260 220,260 200,150" fill="none" stroke="#000000" strokeWidth="2" />
        <line x1="160" y1="260" x2="240" y2="260" stroke="#000000" strokeWidth="4" strokeLinecap="round" />
        
        <style>{`
          @keyframes balance {
            0%, 100% { transform: rotate(-2deg); }
            50% { transform: rotate(2deg); }
          }
          @keyframes pulse-slow {
            0%, 100% { opacity: 0.8; }
            50% { opacity: 1; }
          }
          @keyframes orbit-1 {
            0% { transform: translate(0, 0) rotate(0deg) translate(60px) rotate(0deg); }
            100% { transform: translate(0, 50px) rotate(360deg) translate(60px) rotate(-360deg); }
          }
          @keyframes orbit-2 {
            0% { transform: translate(0, 50px) rotate(0deg) translate(45px) rotate(0deg); }
            100% { transform: translate(0, 50px) rotate(-360deg) translate(45px) rotate(360deg); }
          }
          @keyframes orbit-3 {
            0% { transform: translate(0, 50px) rotate(120deg) translate(55px) rotate(-120deg); }
            100% { transform: translate(0, 50px) rotate(480deg) translate(55px) rotate(-480deg); }
          }
          .animate-balance-beam {
            animation: balance 4s ease-in-out infinite;
            transform-origin: 200px 150px;
          }
          .animate-pulse-slow {
            animation: pulse-slow 2s ease-in-out infinite;
          }
          .animate-orbit-1 {
            animation: orbit-1 6s linear infinite;
            transform-origin: 200px 150px;
          }
          .animate-orbit-2 {
            animation: orbit-2 8s linear infinite;
            transform-origin: 200px 150px;
          }
          .animate-orbit-3 {
            animation: orbit-3 5s linear infinite;
            transform-origin: 200px 150px;
          }
          .animate-weight-left {
            animation: balance 4s ease-in-out infinite;
            transform-origin: 200px 150px;
          }
          .animate-weight-right {
            animation: balance 4s ease-in-out infinite reverse;
            transform-origin: 200px 150px;
          }
        `}</style>
      </svg>
    </div>
  );
}
