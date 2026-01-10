// Created: 2025-12-30
'use client';

import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown } from 'lucide-react';

const faqs = [
  {
    question: "What is Kerne?",
    answer: "Kerne is an institutional-grade delta-neutral protocol built on Base. It allows users to earn stable yield by capturing funding rates through a non-custodial vault architecture, eliminating exposure to underlying asset price volatility."
  },
  {
    question: "How is the yield generated?",
    answer: "Yield is generated through a combination of ETH staking rewards and delta-neutral hedging. Our engine automatically offsets spot ETH exposure with perpetual futures on top-tier exchanges, capturing the funding rate spread while maintaining a price-neutral position."
  },
  {
    question: "Is my capital safe?",
    answer: "Security is our priority. Kerne uses audited smart contracts (OpenZeppelin & Trail of Bits) and never takes custody of your principal. All hedging operations are transparently logged, and the protocol maintains strict collateralization ratios."
  },
  {
    question: "What is the 'Genesis Phase'?",
    answer: "The Genesis Phase is our initial launch period. The first 50 depositors (or up to 50 ETH TVL) benefit from 0% performance fees, maximizing their yield as early adopters of the protocol."
  },
  {
    question: "How do I withdraw my funds?",
    answer: "Users can request withdrawals through the Terminal at any time. Depending on the current hedging cycle and liquidity, withdrawals are typically processed within 24-48 hours to ensure minimal impact on the delta-neutral strategy."
  }
];

export function FAQ() {
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  return (
    <section className="px-8 py-32 max-w-4xl mx-auto z-10 relative">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true }}
        transition={{ duration: 0.6 }}
        className="text-center mb-16"
      >
        <h2 className="text-[10px] uppercase tracking-[0.3em] text-primary font-bold mb-4">Common Questions</h2>
        <h3 className="text-4xl font-heading font-bold tracking-tighter uppercase">Frequently Asked Questions</h3>
      </motion.div>

      <div className="space-y-4">
        {faqs.map((faq, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, y: 10 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.4, delay: index * 0.1 }}
            className="border border-border rounded-xl overflow-hidden bg-card backdrop-blur-sm shadow-sm"
          >
            <button
              onClick={() => setOpenIndex(openIndex === index ? null : index)}
              className="w-full px-6 py-5 flex items-center justify-between text-left hover:bg-muted transition-colors font-heading"
            >
              <span className="font-bold uppercase tracking-tight text-sm text-foreground">{faq.question}</span>
              <ChevronDown
                size={18}
                className={`text-primary transition-transform duration-300 ${openIndex === index ? 'rotate-180' : ''}`}
              />
            </button>
            <AnimatePresence>
              {openIndex === index && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  transition={{ duration: 0.3, ease: "easeInOut" }}
                >
                  <div className="px-6 pt-2 pb-6 text-muted-foreground text-sm leading-relaxed">
                    {faq.answer}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        ))}
      </div>
    </section>
  );
}
