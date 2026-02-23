// Created: 2026-01-16
// Animated SVG for Quanta Points card
'use client';

import React from 'react';

export default function QuantaAnimation() {
  return (
    <div className="w-full h-full min-h-[200px] flex items-center justify-center bg-[#f2d3e5]">
      <svg
        viewBox="0 0 400 300"
        className="w-full h-full max-w-[300px]"
        xmlns="http://www.w3.org/2000/svg"
      >
        {/* Central hexagon representing points collection */}
        <g className="animate-hex-pulse">
          <polygon 
            points="200,80 250,110 250,170 200,200 150,170 150,110" 
            fill="none" 
            stroke="#000000" 
            strokeWidth="3"
          />
          <polygon 
            points="200,95 235,115 235,160 200,180 165,160 165,115" 
            fill="#000000" 
            opacity="0.15"
          />
        </g>
        
        {/* Inner Q symbol */}
        <text x="200" y="155" textAnchor="middle" fontSize="40" fontWeight="bold" fill="#000000" className="animate-q-glow">Q</text>
        
        {/* Orbiting points particles */}
        <circle cx="200" cy="50" r="6" fill="#000000" className="animate-point-orbit-1" />
        <circle cx="200" cy="50" r="5" fill="#000000" className="animate-point-orbit-2" />
        <circle cx="200" cy="50" r="4" fill="#37b48d" className="animate-point-orbit-3" />
        <circle cx="200" cy="50" r="5" fill="#000000" className="animate-point-orbit-4" />
        <circle cx="200" cy="50" r="3" fill="#0d33ec" className="animate-point-orbit-5" />
        <circle cx="200" cy="50" r="4" fill="#000000" className="animate-point-orbit-6" />
        
        {/* Scattered reward points */}
        <circle cx="80" cy="60" r="4" fill="#000000" opacity="0.7" className="animate-scatter-1" />
        <circle cx="320" cy="80" r="5" fill="#000000" opacity="0.6" className="animate-scatter-2" />
        <circle cx="60" cy="180" r="3" fill="#000000" opacity="0.8" className="animate-scatter-3" />
        <circle cx="340" cy="200" r="4" fill="#000000" opacity="0.5" className="animate-scatter-4" />
        <circle cx="100" cy="250" r="5" fill="#37b48d" opacity="0.6" className="animate-scatter-5" />
        <circle cx="300" cy="260" r="3" fill="#000000" opacity="0.7" className="animate-scatter-6" />
        
        {/* Connection lines */}
        <line x1="200" y1="80" x2="80" y2="60" stroke="#000000" strokeWidth="1" opacity="0.2" className="animate-line-1" />
        <line x1="200" y1="80" x2="320" y2="80" stroke="#000000" strokeWidth="1" opacity="0.2" className="animate-line-2" />
        <line x1="150" y1="170" x2="60" y2="180" stroke="#000000" strokeWidth="1" opacity="0.2" className="animate-line-3" />
        <line x1="250" y1="170" x2="340" y2="200" stroke="#000000" strokeWidth="1" opacity="0.2" className="animate-line-4" />
        
        {/* Rising score indicators */}
        <g className="animate-rise-1">
          <text x="120" y="100" fontSize="12" fill="#000000" opacity="0.8">+10</text>
        </g>
        <g className="animate-rise-2">
          <text x="270" y="120" fontSize="12" fill="#000000" opacity="0.8">+25</text>
        </g>
        <g className="animate-rise-3">
          <text x="180" y="240" fontSize="12" fill="#37b48d" opacity="0.8">+50</text>
        </g>
        
        <style>{`
          @keyframes hex-pulse {
            0%, 100% { transform: scale(1); opacity: 1; }
            50% { transform: scale(1.05); opacity: 0.9; }
          }
          @keyframes q-glow {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
          }
          @keyframes point-orbit-1 {
            0% { transform: rotate(0deg) translate(90px) rotate(0deg); }
            100% { transform: rotate(360deg) translate(90px) rotate(-360deg); }
          }
          @keyframes point-orbit-2 {
            0% { transform: rotate(60deg) translate(80px) rotate(-60deg); }
            100% { transform: rotate(420deg) translate(80px) rotate(-420deg); }
          }
          @keyframes point-orbit-3 {
            0% { transform: rotate(120deg) translate(100px) rotate(-120deg); }
            100% { transform: rotate(480deg) translate(100px) rotate(-480deg); }
          }
          @keyframes point-orbit-4 {
            0% { transform: rotate(180deg) translate(85px) rotate(-180deg); }
            100% { transform: rotate(540deg) translate(85px) rotate(-540deg); }
          }
          @keyframes point-orbit-5 {
            0% { transform: rotate(240deg) translate(95px) rotate(-240deg); }
            100% { transform: rotate(600deg) translate(95px) rotate(-600deg); }
          }
          @keyframes point-orbit-6 {
            0% { transform: rotate(300deg) translate(75px) rotate(-300deg); }
            100% { transform: rotate(660deg) translate(75px) rotate(-660deg); }
          }
          @keyframes scatter {
            0%, 100% { transform: scale(1); opacity: 0.5; }
            50% { transform: scale(1.3); opacity: 1; }
          }
          @keyframes rise {
            0% { transform: translateY(0); opacity: 0; }
            20% { opacity: 1; }
            80% { opacity: 1; }
            100% { transform: translateY(-30px); opacity: 0; }
          }
          @keyframes line-fade {
            0%, 100% { opacity: 0.1; }
            50% { opacity: 0.4; }
          }
          .animate-hex-pulse {
            animation: hex-pulse 3s ease-in-out infinite;
            transform-origin: 200px 140px;
          }
          .animate-q-glow {
            animation: q-glow 2s ease-in-out infinite;
          }
          .animate-point-orbit-1 {
            animation: point-orbit-1 8s linear infinite;
            transform-origin: 200px 140px;
          }
          .animate-point-orbit-2 {
            animation: point-orbit-2 10s linear infinite;
            transform-origin: 200px 140px;
          }
          .animate-point-orbit-3 {
            animation: point-orbit-3 7s linear infinite;
            transform-origin: 200px 140px;
          }
          .animate-point-orbit-4 {
            animation: point-orbit-4 9s linear infinite;
            transform-origin: 200px 140px;
          }
          .animate-point-orbit-5 {
            animation: point-orbit-5 11s linear infinite;
            transform-origin: 200px 140px;
          }
          .animate-point-orbit-6 {
            animation: point-orbit-6 6s linear infinite;
            transform-origin: 200px 140px;
          }
          .animate-scatter-1 {
            animation: scatter 3s ease-in-out infinite;
          }
          .animate-scatter-2 {
            animation: scatter 3.5s ease-in-out infinite 0.5s;
          }
          .animate-scatter-3 {
            animation: scatter 2.8s ease-in-out infinite 1s;
          }
          .animate-scatter-4 {
            animation: scatter 4s ease-in-out infinite 0.3s;
          }
          .animate-scatter-5 {
            animation: scatter 3.2s ease-in-out infinite 0.7s;
          }
          .animate-scatter-6 {
            animation: scatter 3.8s ease-in-out infinite 0.2s;
          }
          .animate-line-1, .animate-line-2, .animate-line-3, .animate-line-4 {
            animation: line-fade 2s ease-in-out infinite;
          }
          .animate-rise-1 {
            animation: rise 3s ease-out infinite;
          }
          .animate-rise-2 {
            animation: rise 3s ease-out infinite 1s;
          }
          .animate-rise-3 {
            animation: rise 3s ease-out infinite 2s;
          }
        `}</style>
      </svg>
    </div>
  );
}
