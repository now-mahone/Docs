// Created: 2026-01-09
'use client';

import React, { createContext, useContext, ReactNode } from 'react';

export interface WhiteLabelConfig {
  vaultAddress: `0x${string}`;
  assetSymbol: string;
  brandName: string;
  primaryColor: string;
  logoUrl?: string;
}

const WhiteLabelContext = createContext<WhiteLabelConfig | undefined>(undefined);

export function WhiteLabelProvider({ 
  config, 
  children 
}: { 
  config: WhiteLabelConfig; 
  children: ReactNode;
}) {
  return (
    <WhiteLabelContext.Provider value={config}>
      <div style={{ '--primary-color': config.primaryColor } as React.CSSProperties}>
        {children}
      </div>
    </WhiteLabelContext.Provider>
  );
}

export function useWhiteLabel() {
  const context = useContext(WhiteLabelContext);
  if (!context) {
    throw new Error('useWhiteLabel must be used within a WhiteLabelProvider');
  }
  return context;
}
