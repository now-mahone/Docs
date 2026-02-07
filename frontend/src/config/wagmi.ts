// Created: 2026-01-31
// Clean Wagmi Configuration for Kerne (No Reown/AppKit dependencies)

import { http, createConfig } from 'wagmi'
import { base, arbitrum, optimism } from 'wagmi/chains'
import { injected, walletConnect, coinbaseWallet } from 'wagmi/connectors'

// WalletConnect Project ID
const projectId = process.env.NEXT_PUBLIC_WALLETCONNECT_PROJECT_ID || '647910767760c9828a53e139dec924aa'

export const config = createConfig({
  chains: [base, arbitrum, optimism],
  connectors: [
    injected(),
    coinbaseWallet({
      appName: 'Kerne',
      appLogoUrl: 'https://kerne.ai/logo.png',
    }),
    walletConnect({
      projectId,
      metadata: {
        name: 'Kerne',
        description: 'Institutional Liquidity Layer',
        url: 'https://kerne.ai',
        icons: ['https://kerne.ai/logo.png']
      },
      showQrModal: true,
    }),
  ],
  transports: {
    [base.id]: http(),
    [arbitrum.id]: http(),
    [optimism.id]: http(),
  },
})
