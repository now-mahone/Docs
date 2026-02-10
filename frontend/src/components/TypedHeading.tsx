// Created: 2026-02-10
'use client';

import React, { useRef } from 'react';
import { motion, useInView } from 'framer-motion';

interface TypedHeadingProps {
  children: string;
  className?: string;
  delay?: number;
}

export default function TypedHeading({ children, className = "", delay = 0 }: TypedHeadingProps) {
  const ref = useRef(null);
  const isInView = useInView(ref, { once: true, amount: 0.5 });

  const characters = Array.from(children);

  const containerVariants = {
    hidden: { opacity: 1 },
    visible: {
      opacity: 1,
      transition: { 
        staggerChildren: 0.03, 
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
        duration: 0.05,
      },
    },
  };

  return (
    <motion.h2
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
    </motion.h2>
  );
}