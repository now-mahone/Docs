// Created: 2026-02-16
'use client';

import React, { useState, useEffect } from 'react';

interface RandomNumberRevealProps {
  value: number;
  decimals?: number;
  className?: string;
  duration?: number;
  revealSpeed?: number;
}

export default function RandomNumberReveal({ 
  value, 
  decimals = 1, 
  className = "", 
  duration = 1500 
}: RandomNumberRevealProps) {
  const targetString = value.toFixed(decimals); // e.g. "18.4"
  const [chars, setChars] = useState<string[]>([]);
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    // Initialize with random digits but correct structure
    const initial = targetString.split('').map(char => 
      (char === '.' || char === '%') ? char : Math.floor(Math.random() * 10).toString()
    );
    setChars(initial);
    setIsReady(true);

    let startTime = Date.now();
    let frame: number;

    const update = () => {
      const now = Date.now();
      const progress = Math.min((now - startTime) / duration, 1);
      
      // Reveal from left to right
      const revealIndex = Math.floor(progress * (targetString.length + 1));
      
      const nextChars = targetString.split('').map((targetChar, i) => {
        if (i < revealIndex) return targetChar;
        if (targetChar === '.' || targetChar === '%') return targetChar;
        return Math.floor(Math.random() * 10).toString();
      });

      setChars(nextChars);

      if (progress < 1) {
        frame = requestAnimationFrame(update);
      }
    };

    frame = requestAnimationFrame(update);
    return () => cancelAnimationFrame(frame);
  }, [value, duration, targetString]);

  return (
    <span className={`${className} inline-block min-w-[4ch] transition-opacity duration-300 ${isReady ? 'opacity-100' : 'opacity-0'}`}>
      {chars.join('')}%
    </span>
  );
}
