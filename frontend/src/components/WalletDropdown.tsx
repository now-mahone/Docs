// Created: 2026-01-31
// Dropdown-based Wallet Selector
'use client';

import React, { useState, useRef, useEffect } from 'react';
import { useConnect } from 'wagmi';
import { SquareArrowDown } from 'lucide-react';

export function WalletDropdown() {
  const { connect, connectors } = useConnect();
  const [isOpen, setIsOpen] = useState(false);
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

  const walletOptions = [
    { 
      name: 'Base Wallet', 
      connector: 'coinbaseWallet',
      icon: <img src="/Base-DD.svg" alt="Base Wallet" className="w-5 h-5" />
    },
    { 
      name: 'MetaMask', 
      connector: 'injected',
      icon: <img src="/MetaMask-DD.svg" alt="MetaMask" className="w-5 h-5" />
    },
    { 
      name: 'Trust Wallet', 
      connector: 'walletConnect',
      icon: <img src="/Trust-DD.svg" alt="Trust Wallet" className="w-5 h-5" />
    },
    { 
      name: 'Binance Wallet', 
      connector: 'walletConnect',
      icon: <img src="/Binance-DD.svg" alt="Binance Wallet" className="w-5 h-5" />
    },
    { 
      name: 'Search All (WalletConnect)', 
      connector: 'walletConnect',
      icon: <img src="/WalletConnect-DD.svg" alt="Search All" className="w-5 h-5" />,
      isSearchAll: true
    }
  ];

  const handleConnect = async (connectorId: string) => {
    const connector = connectors.find(c => c.id === connectorId || c.id.includes(connectorId));
    if (connector) {
      try {
        await connect({ connector });
        setIsOpen(false);
      } catch (err) {
        console.error('Connection error:', err);
      }
    }
  };

  return (
    <div className="relative" ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="relative px-6 bg-[linear-gradient(110deg,#19b097,#37d097,#19b097)] animate-mesh text-[#000000] text-s font-bold rounded-sm border-none outline-none h-12 flex items-center justify-center gap-2 transition-all cursor-pointer"
      >
        Connect Wallet
        <SquareArrowDown className={`w-4 h-4 text-[#000000] transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </button>

      {isOpen && (
        <div className="absolute top-full right-0 mt-2 w-80 bg-[#000000] border border-[#444a4f] rounded-sm shadow-2xl z-50 overflow-hidden p-4">
          <div className="space-y-1 mb-4">
            {walletOptions.map((wallet) => (
              <button
                key={wallet.name}
                onClick={() => handleConnect(wallet.connector)}
                className="w-full flex items-center gap-3 px-4 py-3 bg-[#22252a] border border-[#444a4f] rounded-sm text-left cursor-pointer"
              >
                {wallet.icon}
                {wallet.isSearchAll ? (
                  <span className="text-s font-medium">
                    <span className="text-[#aab9be]">Search All </span>
                    <span className="text-[#ffffff]">(WalletConnect)</span>
                  </span>
                ) : (
                  <span className="text-s font-medium text-[#ffffff]">{wallet.name}</span>
                )}
              </button>
            ))}
          </div>
          <div className="pt-3 border-t border-[#444a4f]">
            <p className="text-xs text-[#aab9be] leading-relaxed">
              By connecting a wallet, you agree to our{' '}
              <a href="/terms" target="_blank" rel="noopener noreferrer" className="text-[#ffffff] hover:underline">
                Terms of Service
              </a>
              {' '}and acknowledge that you have read and understand our{' '}
              <a href="/privacy" target="_blank" rel="noopener noreferrer" className="text-[#ffffff] hover:underline">
                Privacy Policy
              </a>
              .
            </p>
          </div>
        </div>
      )}
    </div>
  );
}