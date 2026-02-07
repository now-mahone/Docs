// Created: 2026-01-16
// Animated SVG for kUSD Synthetic Dollar card
'use client';

import React from 'react';

export default function KUSDAnimation() {
  return (
    <div className="w-full h-full min-h-[200px] flex items-center justify-center bg-[#edf2fd]">
      <svg
        viewBox="0 0 400 300"
        className="w-full h-full max-w-[300px]"
        xmlns="http://www.w3.org/2000/svg"
      >
        {/* Central coin shape */}
        <g className="animate-coin-rotate">
          <ellipse cx="200" cy="150" rx="70" ry="70" fill="#000000" className="animate-pulse-coin" />
          <ellipse cx="200" cy="150" rx="55" ry="55" fill="#edf2fd" />
          <ellipse cx="200" cy="150" rx="50" ry="50" fill="#000000" opacity="0.1" />
          {/* Dollar sign */}
          <text x="200" y="165" textAnchor="middle" fontSize="50" fontWeight="bold" fill="#000000" className="animate-text-fade">$</text>
        </g>
        
        {/* Floating currency particles */}
        <circle cx="100" cy="80" r="8" fill="#000000" opacity="0.6" className="animate-float-1" />
        <circle cx="320" cy="100" r="6" fill="#000000" opacity="0.5" className="animate-float-2" />
        <circle cx="80" cy="200" r="5" fill="#37b48d" opacity="0.7" className="animate-float-3" />
        <circle cx="330" cy="220" r="7" fill="#000000" opacity="0.4" className="animate-float-4" />
        <circle cx="150" cy="250" r="4" fill="#000000" opacity="0.6" className="animate-float-5" />
        <circle cx="280" cy="60" r="5" fill="#37b48d" opacity="0.5" className="animate-float-6" />
        
        {/* Stability lines */}
        <g className="animate-lines">
          <line x1="120" y1="150" x2="80" y2="150" stroke="#000000" strokeWidth="2" strokeLinecap="round" opacity="0.3" />
          <line x1="280" y1="150" x2="320" y2="150" stroke="#000000" strokeWidth="2" strokeLinecap="round" opacity="0.3" />
          <line x1="200" y1="70" x2="200" y2="40" stroke="#000000" strokeWidth="2" strokeLinecap="round" opacity="0.3" />
          <line x1="200" y1="230" x2="200" y2="260" stroke="#000000" strokeWidth="2" strokeLinecap="round" opacity="0.3" />
        </g>
        
        {/* Peg indicator arrows */}
        <path d="M60 150 L75 140 L75 160 Z" fill="#37b48d" className="animate-arrow-left" />
        <path d="M340 150 L325 140 L325 160 Z" fill="#37b48d" className="animate-arrow-right" />
        
        <style>{`
          @keyframes coin-rotate {
            0%, 100% { transform: perspective(400px) rotateY(0deg); }
            50% { transform: perspective(400px) rotateY(15deg); }
          }
          @keyframes pulse-coin {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.85; }
          }
          @keyframes text-fade {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
          }
          @keyframes float-1 {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-15px); }
          }
          @keyframes float-2 {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-20px); }
          }
          @keyframes float-3 {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-12px); }
          }
          @keyframes float-4 {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-18px); }
          }
          @keyframes float-5 {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-10px); }
          }
          @keyframes float-6 {
            0%, 100% { transform: translateY(0px); }
            50% { transform: translateY(-14px); }
          }
          @keyframes arrow-pulse {
            0%, 100% { transform: translateX(0px); opacity: 0.8; }
            50% { transform: translateX(5px); opacity: 1; }
          }
          @keyframes arrow-pulse-reverse {
            0%, 100% { transform: translateX(0px); opacity: 0.8; }
            50% { transform: translateX(-5px); opacity: 1; }
          }
          @keyframes lines-pulse {
            0%, 100% { opacity: 0.3; }
            50% { opacity: 0.6; }
          }
          .animate-coin-rotate {
            animation: coin-rotate 4s ease-in-out infinite;
            transform-origin: 200px 150px;
          }
          .animate-pulse-coin {
            animation: pulse-coin 3s ease-in-out infinite;
          }
          .animate-text-fade {
            animation: text-fade 3s ease-in-out infinite;
          }
          .animate-float-1 {
            animation: float-1 3s ease-in-out infinite;
          }
          .animate-float-2 {
            animation: float-2 4s ease-in-out infinite 0.5s;
          }
          .animate-float-3 {
            animation: float-3 3.5s ease-in-out infinite 1s;
          }
          .animate-float-4 {
            animation: float-4 4.5s ease-in-out infinite 0.3s;
          }
          .animate-float-5 {
            animation: float-5 3.2s ease-in-out infinite 0.7s;
          }
          .animate-float-6 {
            animation: float-6 3.8s ease-in-out infinite 0.2s;
          }
          .animate-arrow-left {
            animation: arrow-pulse 2s ease-in-out infinite;
          }
          .animate-arrow-right {
            animation: arrow-pulse-reverse 2s ease-in-out infinite;
          }
          .animate-lines {
            animation: lines-pulse 2.5s ease-in-out infinite;
          }
        `}</style>
      </svg>
    </div>
  );
}
