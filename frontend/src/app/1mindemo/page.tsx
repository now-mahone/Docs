// Created: 2026-02-11
import { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Kerne Protocol - 1 Minute Demo',
  description: 'A quick 1-minute demo of Kerne Protocol - delta-neutral yield infrastructure on Base.',
};

export default function OneMinDemoPage() {
  return (
    <main className="min-h-screen bg-[#0a0a0a] text-white flex flex-col items-center justify-center p-4">
      <div className="max-w-4xl w-full">
        <div className="text-center mb-8">
          <h1 className="text-3xl md:text-4xl font-bold mb-4 bg-gradient-to-r from-[#00ff88] to-[#00ccff] bg-clip-text text-transparent">
            Kerne Protocol
          </h1>
          <p className="text-lg text-gray-400">
            Delta-Neutral Yield Infrastructure on Base
          </p>
        </div>
        
        <div className="relative w-full aspect-video rounded-xl overflow-hidden border border-gray-800 shadow-2xl">
          <video 
            className="w-full h-full object-contain bg-black"
            controls
            autoPlay
            playsInline
            poster="/kerne-logo-512.png"
          >
            <source src="/kerne-demo.mp4" type="video/mp4" />
            Your browser does not support the video tag.
          </video>
        </div>
        
        <div className="mt-8 text-center">
          <a 
            href="https://kerne.ai"
            className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-[#00ff88] to-[#00ccff] text-black font-semibold rounded-lg hover:opacity-90 transition-opacity"
          >
            Visit kerne.ai
          </a>
        </div>
        
        <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6 text-center">
          <div className="p-4 rounded-lg bg-gray-900/50 border border-gray-800">
            <div className="text-2xl font-bold text-[#00ff88]">35+</div>
            <div className="text-sm text-gray-400">Smart Contracts</div>
          </div>
          <div className="p-4 rounded-lg bg-gray-900/50 border border-gray-800">
            <div className="text-2xl font-bold text-[#00ff88]">154</div>
            <div className="text-sm text-gray-400">Foundry Tests</div>
          </div>
          <div className="p-4 rounded-lg bg-gray-900/50 border border-gray-800">
            <div className="text-2xl font-bold text-[#00ff88]">24/7</div>
            <div className="text-sm text-gray-400">Live Hedging</div>
          </div>
        </div>
      </div>
    </main>
  );
}