// Created: 2025-12-28
import Link from 'next/link';

export default function DocsPage() {
  return (
    <main className="min-h-screen bg-black text-zinc-300 font-mono p-8 md:p-24 selection:bg-emerald-500 selection:text-black">
      <div className="max-w-3xl mx-auto space-y-12">
        {/* Header */}
        <header className="border-b border-zinc-800 pb-8">
          <Link href="/" className="text-zinc-500 hover:text-white transition-colors mb-4 inline-block">
            {"<"} RETURN_TO_DASHBOARD
          </Link>
          <h1 className="text-4xl font-bold text-white tracking-tighter">KERNE_LITEPAPER_V1.0</h1>
          <p className="text-zinc-500 mt-2">Institutional-Grade Delta-Neutral Synthetic Assets</p>
        </header>

        {/* Strategy Section */}
        <section className="space-y-4">
          <h2 className="text-xl text-emerald-500 border-l-2 border-emerald-500 pl-4">01_THE_STRATEGY</h2>
          <div className="space-y-4 leading-relaxed">
            <p>
              Kerne utilizes a Delta-Neutral Shorting strategy to generate sustainable, high-yield returns on Ethereum collateral. 
              By combining Liquid Staking Tokens (LSTs) with 1x Short Perpetual positions on Tier-1 Centralized Exchanges, 
              the protocol eliminates price exposure while capturing two distinct yield streams.
            </p>
            <ul className="list-disc list-inside space-y-2 text-zinc-400 ml-4">
              <li>Staking Yield: Native rewards from wstETH/cbETH.</li>
              <li>Funding Arbitrage: Payments from long traders to short holders during bullish/neutral markets.</li>
            </ul>
          </div>
        </section>

        {/* kUSD Section */}
        <section className="space-y-4">
          <h2 className="text-xl text-emerald-400 border-l-2 border-emerald-400 pl-4">02_kUSD_SYNTHETIC_DOLLAR</h2>
          <div className="space-y-4 leading-relaxed">
            <p>
              kUSD is the native synthetic dollar of the Kerne ecosystem. It is minted against KerneVault shares (kLP) as collateral, 
              allowing users to unlock liquidity from their yield-bearing positions without selling their principal.
            </p>
            <div className="p-4 bg-zinc-900/50 border border-zinc-800 space-y-2">
              <div className="flex justify-between text-xs">
                <span className="text-zinc-500">MINT_COLLATERAL_RATIO</span>
                <span className="text-white">150%</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-zinc-500">LIQUIDATION_THRESHOLD</span>
                <span className="text-red-400">120%</span>
              </div>
              <div className="flex justify-between text-xs">
                <span className="text-zinc-500">LIQUIDATION_BONUS</span>
                <span className="text-emerald-400">5%</span>
              </div>
            </div>
          </div>
        </section>

        {/* Risk Section */}
        <section className="space-y-4">
          <h2 className="text-xl text-red-500 border-l-2 border-red-500 pl-4">03_RISK_VECTORS</h2>
          <div className="space-y-4 leading-relaxed">
            <p>
              Transparency is our core principle. Investors must understand the following risks:
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="p-4 bg-zinc-900/50 border border-zinc-800">
                <h3 className="text-white mb-2">Counterparty_Risk</h3>
                <p className="text-sm text-zinc-500">
                  Collateral is held on Tier-1 exchanges (Binance/Bybit). Exchange insolvency or API failure could impact withdrawals.
                </p>
              </div>
              <div className="p-4 bg-zinc-900/50 border border-zinc-800">
                <h3 className="text-white mb-2">Smart_Contract_Risk</h3>
                <p className="text-sm text-zinc-500">
                  While audited, all on-chain protocols carry inherent risks of bugs or exploits in the vault logic.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Fees Section */}
        <section className="space-y-4">
          <h2 className="text-xl text-zinc-100 border-l-2 border-zinc-100 pl-4">04_FEE_STRUCTURE</h2>
          <div className="p-6 bg-zinc-950 border border-dashed border-zinc-800">
            <div className="flex justify-between items-center">
              <span className="text-zinc-500">PERFORMANCE_FEE</span>
              <span className="text-2xl text-white">10%</span>
            </div>
            <p className="text-xs text-zinc-400 mt-4 uppercase leading-relaxed">
              The performance fee is a <span className="text-white font-bold">commission on profits only</span>. 
              It is automatically deducted from the generated yield before it is distributed to depositors. 
              Kerne charges <span className="text-emerald-500 font-bold">0% management fees</span> and 0% entry/exit fees.
            </p>
          </div>
          <div className="p-6 bg-emerald-950/30 border border-emerald-800/50">
            <div className="flex justify-between items-center">
              <span className="text-emerald-400">GENESIS_PHASE_FEE</span>
              <span className="text-2xl text-emerald-400">0%</span>
            </div>
            <p className="text-xs text-zinc-400 mt-4 uppercase leading-relaxed">
              During the Genesis Phase, early depositors enjoy <span className="text-emerald-400 font-bold">0% performance fees</span> until 
              the protocol reaches <span className="text-white font-bold">$100,000 TVL</span>. This incentivizes early adoption and 
              helps bootstrap protocol liquidity. Once TVL exceeds the threshold, standard performance fees apply.
            </p>
          </div>
        </section>

        {/* Footer */}
        <footer className="pt-12 border-t border-zinc-800 text-center text-xs text-zinc-600 uppercase tracking-widest">
          Kerne Protocol &copy; 2025 // Secure_Yield_Engine
        </footer>
      </div>
    </main>
  );
}
