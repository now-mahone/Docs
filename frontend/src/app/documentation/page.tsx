// Temporary documentation redirect page
// Created: 2026-02-09
'use client';

import { useEffect } from 'react';

export default function DocumentationPage() {
  useEffect(() => {
    // Redirect to GitHub Pages URL once DNS is configured
    // For now, show a message
    const timer = setTimeout(() => {
      window.location.href = 'https://kerne-protocol.github.io/docs';
    }, 3000);
    
    return () => clearTimeout(timer);
  }, []);

  return (
    <div className="min-h-screen bg-gradient-to-b from-[#f8f9fa] to-[#ffffff] flex items-center justify-center p-6">
      <div className="max-w-2xl w-full bg-white border border-[#aab9be] rounded-sm p-12 text-center">
        <h1 className="text-4xl font-bold text-[#000000] mb-6">
          Documentation Loading...
        </h1>
        <p className="text-lg text-[#737581] mb-8">
          Redirecting you to the Kerne Protocol documentation.
        </p>
        <div className="flex items-center justify-center gap-2">
          <div className="w-2 h-2 bg-[#000000] rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
          <div className="w-2 h-2 bg-[#000000] rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
          <div className="w-2 h-2 bg-[#000000] rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
        </div>
        <p className="text-sm text-[#737581] mt-8">
          If you are not redirected automatically, please{' '}
          <a 
            href="https://kerne-protocol.github.io/docs" 
            className="text-[#000000] font-semibold underline"
          >
            click here
          </a>.
        </p>
      </div>
    </div>
  );
}