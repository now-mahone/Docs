// Created: 2026-02-10
'use client';

import React, { useRef } from 'react';
import { motion, useInView } from 'framer-motion';

interface TypedTextProps {
  children: string;
  className?: string;
  delay?: number;
  staggerSpeed?: number;
  charDuration?: number;
}

export default function TypedText({ children, className = "", delay = 0, staggerSpeed = 0.02, charDuration = 0.03 }: TypedTextProps) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, amount: 0.5 });

  const characters = Array.from(children);

  const containerVariants = {
    hidden: { opacity: 1 },
    visible: {
      opacity: 1,
      transition: { 
        staggerChildren: staggerSpeed, 
        delayChildren: delay
      },
    },
  };

  const childVariants = {
    hidden: {
      opacity: 0,
    },
    visible: {
      opacity: 1,
      transition: {
        duration: charDuration,
      },
    },
  };

  return (
    <motion.span
      ref={ref}
      className={className}
      variants={containerVariants}
      initial="hidden"
      animate={isInView ? "visible" : "hidden"}
    >
      {characters.map((char, index) => (
        <motion.span key={index} variants={childVariants}>
          {char}
        </motion.span>
      ))}
    </motion.span>
  );
}