// Created: 2026-01-18

# Kerne Lead Outreach Playbook

## The Challenge: How to Contact a Wallet Address

Wallet addresses are anonymous by default. Here's how to find the person behind the wallet and reach them.

---

## 🔍 STEP 1: Research the Wallet

### A. Check ENS / Basename
1. Go to https://app.ens.domains/ 
2. Search the wallet address
3. If they have an ENS (e.g., `whale.eth`), you can often find their Twitter/social linked

**For Base:** Check https://www.base.org/names for Basenames

### B. Check DeBank / Zapper Profile
1. Go to https://debank.com/profile/[ADDRESS]
2. Look for:
   - Social links (Twitter, Discord)
   - Web3 ID / profile name
   - Activity patterns (what protocols they use)

### C. Check Etherscan/Basescan Labels
1. Go to https://basescan.org/address/[ADDRESS]
2. Look for:
   - "Name Tag" (if labeled)
   - Contract interactions (what protocols they use)
   - Token holdings

### D. Reverse Lookup Tools
- **Arkham Intelligence:** https://platform.arkhamintelligence.com/
- **Nansen:** https://app.nansen.ai/ (paid)
- **Breadcrumbs:** https://www.breadcrumbs.app/

---

## 📱 STEP 2: Find Their Social Presence

### If They Have ENS/Basename:
1. Search the ENS name on Twitter/X
2. Search on Farcaster (Warpcast)
3. Check their ENS text records for social links

### If No ENS:
1. Search the wallet address on Twitter (people sometimes post their addresses)
2. Check if they're active in Discord servers of protocols they use
3. Look for governance votes (Snapshot) - voters often have profiles

### Protocol-Specific Discovery:
- **If they use Aave/Compound:** Check governance forums
- **If they use Uniswap:** Check Discord
- **If they stake ETH:** Check Lido/Rocket Pool communities

---

## 💬 STEP 3: Outreach Channels (Ranked by Effectiveness)

### 1. Twitter/X DM (Best)
**Why:** Most crypto-native users are on Twitter
**How:** 
- Follow them first
- Like/reply to a few of their tweets
- Then send a personalized DM

**Template:**
```
Hey! Noticed you're active on Base with a solid ETH position.

We just launched Kerne - a delta-neutral yield protocol doing ~15% APY on ETH with zero directional exposure.

Would love your feedback: https://kerne.ai/terminal

No pressure, just thought it might be relevant to your strategy.
```

### 2. Farcaster / Warpcast
**Why:** Higher signal, less spam than Twitter
**How:** Cast a reply to their posts or send a direct cast

### 3. Discord DM
**Why:** If they're in protocol Discords, they're engaged
**How:** Find them in servers like Base, Aerodrome, Uniswap

### 4. Telegram
**Why:** Some whales prefer Telegram
**How:** Find them in DeFi alpha groups

### 5. On-Chain Message (Last Resort)
**Why:** Guaranteed delivery, but low response rate
**How:** Send a tiny amount (0.0001 ETH) with a message in the transaction data

---

## 🎯 STEP 4: Prioritize Your Leads

### Tier 1: High Priority (Research First)
- Balance > $100k
- Active in last 7 days
- Uses yield protocols (Aave, Compound, Yearn)

### Tier 2: Medium Priority
- Balance $50k - $100k
- Active in last 30 days

### Tier 3: Low Priority (Batch Outreach)
- Balance $10k - $50k
- May be less engaged

---

## 📋 Current Lead List

| Address | Balance | Priority | Research Status |
|---------|---------|----------|-----------------|
| 0xfd38...3561 | $540k USDC | Tier 1 | [ ] Research |
| 0x2d56...beC7 | $803k USDC | Tier 1 | [ ] Research |
| 0xCBBF...eC7C | $360k USDC | Tier 1 | [ ] Research |
| 0x42f3...2273 | $327k USDC | Tier 1 | [ ] Research |
| 0x33bD...281E | $157k USDC | Tier 1 | [ ] Research |

---

## 🚀 Quick Start: Research Your First Lead

Let's research the top lead: `0xfd38C1E85EC5B20BBdd4aF39c4Be7e4D91e43561`

1. **DeBank:** https://debank.com/profile/0xfd38C1E85EC5B20BBdd4aF39c4Be7e4D91e43561
2. **Basescan:** https://basescan.org/address/0xfd38C1E85EC5B20BBdd4aF39c4Be7e4D91e43561
3. **ENS Lookup:** Search on app.ens.domains

---

## 📊 Tracking Outreach

Create a simple spreadsheet:

| Address | Name/Handle | Channel | Date Contacted | Response | Notes |
|---------|-------------|---------|----------------|----------|-------|
| 0xfd38... | @example | Twitter DM | 2026-01-18 | Pending | Uses Aave |

---

## ⚠️ Best Practices

1. **Personalize:** Reference their on-chain activity
2. **Don't Spam:** One message per person, wait for response
3. **Provide Value:** Share something useful, not just a pitch
4. **Be Patient:** Whales get lots of DMs, may take days to respond
5. **Follow Up Once:** If no response in 5-7 days, one polite follow-up

---

## 🔄 Running the Lead Scanner

To find fresh leads, run:
```bash
cd z:\kerne-new
python bot/lead_scanner_v3.py
```

This scans for WETH, cbETH, and wstETH holders with 50+ ETH on Base.
