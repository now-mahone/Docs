// Created: 2026-01-30
// Updated: 2026-02-04 - Added dropdown for connected wallet state with disconnect and history options
'use client';

import React, { useState, useRef, useEffect } from 'react';
import { useAccount, useDisconnect } from 'wagmi';
import { ChevronDown, LogOut, SquareUser, Copy, Check } from 'lucide-react';
import { WalletDropdown } from './WalletDropdown';

export function WalletConnectButton() {
  const { address, isConnected } = useAccount();
  const { disconnect } = useDisconnect();
  const [isOpen, setIsOpen] = useState(false);
  const [copied, setCopied] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => document.removeEventListener('mousedown', handleClickOutside);
    }
  }, [isOpen]);

  const handleDisconnect = () => {
    disconnect();
    setIsOpen(false);
  };

  const handleCopy = async () => {
    if (address) {
      await navigator.clipboard.writeText(address);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  if (isConnected && address) {
    return (
      <div className="relative" ref={dropdownRef}>
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="relative px-6 bg-[linear-gradient(110deg,#19b097,#37d097,#19b097)] animate-mesh text-[#000000] text-s font-bold rounded-sm border-none outline-none h-12 flex items-center justify-center gap-2 transition-all cursor-pointer"
        >
          {address.slice(0, 6)}...{address.slice(-4)}
          <ChevronDown className={`w-4 h-4 text-[#000000] transition-transform ${isOpen ? 'rotate-180' : ''}`} />
        </button>

        {isOpen && (
          <div className="absolute top-full right-0 mt-2 w-80 bg-[#000000] border border-[#444a4f] rounded-sm shadow-2xl z-50 overflow-hidden p-4">
            <div className="mb-4 flex items-center gap-2">
              <SquareUser className="w-4 h-4 text-[#aab9be] flex-shrink-0" />
              <p className="text-xs text-[#aab9be] break-all flex-1">
                {address}
              </p>
              <button
                onClick={handleCopy}
                className="flex-shrink-0 p-1 hover:bg-[#22252a] rounded transition-colors"
              >
                {copied ? (
                  <Check className="w-4 h-4 text-[#37d097]" />
                ) : (
                  <Copy className="w-4 h-4 text-[#aab9be]" />
                )}
              </button>
            </div>
            <div className="pt-3 border-t border-[#444a4f]">
              <button
                onClick={handleDisconnect}
                className="w-full flex items-center gap-3 px-4 py-3 bg-[#22252a] border border-[#444a4f] rounded-sm text-left cursor-pointer hover:bg-[#22252a]/80 transition-colors"
              >
                <LogOut className="w-5 h-5 text-[#aab9be]" />
                <span className="text-s font-medium text-[#ffffff]">Disconnect</span>
              </button>
            </div>
          </div>
        )}
      </div>
    );
  }

  return <WalletDropdown />;
}