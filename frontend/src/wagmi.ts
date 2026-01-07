// Created: 2025-12-28
import { getDefaultConfig } from '@rainbow-me/rainbowkit';
import { base, foundry, arbitrum, optimism } from 'wagmi/chains';

export const config = getDefaultConfig({
  appName: 'Kerne Terminal',
  projectId: '647910767760c9828a53e139dec924aa',
  chains: process.env.NODE_ENV === 'production' ? [base, arbitrum, optimism] : [foundry, base, arbitrum, optimism],
  ssr: true,
});
