// Created: 2026-02-16
'use client';

import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

interface RandomNumberRevealProps {
  value: number | null;
  decimals?: number;
  className?: string;
  duration?: number;
}

export default function RandomNumberReveal({ 
  value, 
  decimals = 1, 
  className = "", 
  duration = 2500 
}: RandomNumberRevealProps) {
  const targetString = value !== null ? value.toFixed(decimals) : "00.00";
  const [chars, setChars] = useState<string[]>([]);
  const [isReady, setIsReady] = useState(false);

  useEffect(() => {
    if (value === null) return;

    // Initialize with random digits but correct structure
    const initial = targetString.split('').map(char => 
      (char === '.' || char === '%') ? char : Math.floor(Math.random() * 10).toString()
    );
    setChars(initial);
    setIsReady(true);

    let startTime = Date.now();
    let frame: number;

    let lastFlickerTime = 0;
    const flickerInterval = 50; 

    const update = () => {
      const now = Date.now();
      const progress = Math.min((now - startTime) / duration, 1);
      
      // Reveal from left to right
      const revealIndex = Math.floor(progress * (targetString.length + 1));
      
      if (now - lastFlickerTime > flickerInterval || progress === 1) {
        const nextChars = targetString.split('').map((targetChar, i) => {
          if (i < revealIndex) return targetChar;
          if (targetChar === '.' || targetChar === '%') return targetChar;
          return Math.floor(Math.random() * 10).toString();
        });
        setChars(nextChars);
        lastFlickerTime = now;
      }

      if (progress < 1) {
        frame = requestAnimationFrame(update);
      }
    };

    frame = requestAnimationFrame(update);
    return () => cancelAnimationFrame(frame);
  }, [value, duration, targetString]);

  return (
    <span className={`${className} inline-flex items-baseline min-w-[5ch] transition-opacity duration-300 ${isReady && value !== null ? 'opacity-100' : 'opacity-0'}`}>
      {chars.map((char, index) => (
        <span key={index} className="relative inline-block overflow-hidden h-[1.1em] leading-none">
          <AnimatePresence mode="popLayout" initial={false}>
            <motion.span
              key={`${index}-${char}`}
              initial={{ y: "100%", opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              exit={{ y: "-100%", opacity: 0 }}
              transition={{ duration: 0.15, ease: "easeOut" }}
              className="inline-block"
            >
              {char}
            </motion.span>
          </AnimatePresence>
        </span>
      ))}
      <span className="ml-[0.1em]">%</span>
    </span>
  );
}
