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
  duration = 1000, 
  revealSpeed = 50 
}: RandomNumberRevealProps) {
  const [displayValue, setDisplayValue] = useState("");
  const targetString = value.toFixed(decimals) + "%";

  useEffect(() => {
    let startTime = Date.now();
    let frame: number;

    const update = () => {
      const now = Date.now();
      const progress = Math.min((now - startTime) / duration, 1);
      
      // Calculate how many characters should be "revealed" (correct) vs "random"
      const revealCount = Math.floor(progress * targetString.length);
      
      let currentStr = "";
      for (let i = 0; i < targetString.length; i++) {
        if (i < revealCount) {
          currentStr += targetString[i];
        } else {
          // Generate random digit or character
          const chars = "0123456789%.";
          currentStr += chars[Math.floor(Math.random() * chars.length)];
        }
      }

      setDisplayValue(currentStr);

      if (progress < 1) {
        frame = requestAnimationFrame(update);
      } else {
        setDisplayValue(targetString);
      }
    };

    frame = requestAnimationFrame(update);
    return () => cancelAnimationFrame(frame);
  }, [value, decimals, duration, targetString]);

  return <span className={className}>{displayValue}</span>;
}