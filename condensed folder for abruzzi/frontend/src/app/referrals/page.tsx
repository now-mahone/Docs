import { ReferralInterface } from '@/components/ReferralInterface';

export default function ReferralsPage() {
  return (
    <main className="min-h-screen bg-black pt-24 pb-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto space-y-12">
        <div className="text-center space-y-4">
          <h1 className="text-4xl md:text-6xl font-black text-white tracking-tighter uppercase">
            Referral <span className="text-zinc-500">Flywheel</span>
          </h1>
          <p className="text-zinc-400 max-w-2xl mx-auto text-lg">
            The Kerne Protocol grows through its partners. Leverage your network to capture a share of the protocol's wealth velocity.
          </p>
        </div>

        <ReferralInterface />

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mt-12">
          <div className="p-8 bg-zinc-900/20 border border-zinc-800 rounded-2xl">
            <h3 className="text-xl font-bold text-white mb-4 uppercase tracking-tight">Genesis Partner Program</h3>
            <p className="text-zinc-400 leading-relaxed">
              During the Genesis phase, all referrers are automatically enrolled as Genesis Partners. 
              This tier grants the highest possible commission rates (10% Tier 1, 5% Tier 2) and early access to the $KERNE governance token airdrop.
            </p>
          </div>
          <div className="p-8 bg-zinc-900/20 border border-zinc-800 rounded-2xl">
            <h3 className="text-xl font-bold text-white mb-4 uppercase tracking-tight">Wealth Velocity</h3>
            <p className="text-zinc-400 leading-relaxed">
              Wealth Velocity is our internal metric for network growth. It measures the rate at which your referred TVL is generating fees. 
              High velocity partners receive exclusive invitations to the Kerne Institutional Council.
            </p>
          </div>
        </div>
      </div>
    </main>
  );
}
