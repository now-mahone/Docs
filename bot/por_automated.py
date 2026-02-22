# Created: 2026-01-21
"""
Kerne Protocol - Automated Proof of Reserve (PoR) System

Institutional-grade solvency attestation that:
1. Aggregates on-chain assets across Base + Arbitrum vaults
2. Verifies off-chain CEX equity (Hyperliquid)
3. Signs cryptographic attestations
4. Generates public JSON output for API consumption
5. Validates solvency invariant (Assets >= Liabilities)

This is the "Glass House Standard" - proving every deposited asset is accounted for.
"""
from __future__ import annotations

import os
import json
import time
import hashlib
from datetime import datetime, timezone
from dataclasses import dataclass, asdict
from typing import Optional, Dict, List, Any
from pathlib import Path

from web3 import Web3
from eth_account.messages import encode_defunct
from dotenv import load_dotenv
from loguru import logger

# Load environment
load_dotenv()


@dataclass
class ChainMetrics:
    """Metrics for a single chain."""
    chain_id: int
    chain_name: str
    vault_address: str
    total_assets_wei: int
    total_assets_eth: float
    total_supply_wei: int
    total_supply_eth: float
    solvency_ratio: float
    rpc_healthy: bool
    timestamp: int


@dataclass
class AggregatedPoR:
    """Aggregated Proof of Reserve across all chains and venues."""
    # Timestamp
    generated_at: str
    unix_timestamp: int
    block_heights: Dict[str, int]
    
    # On-Chain Metrics (by chain)
    chains: List[Dict[str, Any]]
    total_onchain_assets_eth: float
    total_onchain_liabilities_eth: float
    
    # Off-Chain Metrics (CEX)
    offchain_venue: str
    offchain_equity_usd: float
    offchain_equity_eth_equiv: float
    offchain_net_delta: float
    offchain_short_position_eth: float
    
    # Aggregate Solvency
    total_assets_eth: float
    total_liabilities_eth: float
    aggregate_solvency_ratio: float
    is_solvent: bool
    delta_neutral: bool
    
    # Cryptographic Attestation
    attestation_hash: str
    signature: str
    signer: str
    
    # Status
    status: str  # SOLVENT, WARNING, CRITICAL


class AutomatedPoRBot:
    """
    Automated Proof of Reserve (PoR) Attestation Bot.
    Multi-chain, multi-venue solvency verification with public reporting.
    """
    
    # Chain configurations
    CHAINS = {
        "base": {
            "chain_id": 8453,
            "rpc_env": "RPC_URL",
            "vault_env": "VAULT_ADDRESS",
            "name": "Base Mainnet"
        },
        "arbitrum": {
            "chain_id": 42161,
            "rpc_env": "ARBITRUM_RPC_URL", 
            "vault_env": "ARB_VAULT_ADDRESS",
            "name": "Arbitrum One"
        }
    }
    
    # Vault ABI (minimal for PoR)
    VAULT_ABI = [
        {
            "inputs": [],
            "name": "totalAssets",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function"
        },
        {
            "inputs": [],
            "name": "totalSupply",
            "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
            "stateMutability": "view",
            "type": "function"
        }
    ]
    
    # Output directories
    JSON_OUTPUT_DIR = Path("docs/reports/por")
    PUBLIC_JSON_PATH = Path("docs/reports/por/latest.json")
    HISTORY_DIR = Path("docs/reports/por/history")
    
    def __init__(self):
        """Initialize the PoR bot with multi-chain connections."""
        self.private_key = os.getenv("PRIVATE_KEY")
        if not self.private_key:
            raise ValueError("PRIVATE_KEY environment variable required")
        
        # Initialize Web3 connections
        self.web3_connections: Dict[str, Web3] = {}
        self.vault_contracts: Dict[str, Any] = {}
        
        for chain_key, config in self.CHAINS.items():
            rpc_urls = os.getenv(config["rpc_env"], "").split(",")
            vault_address = os.getenv(config["vault_env"])
            
            if rpc_urls and rpc_urls[0] and vault_address:
                for rpc_url in rpc_urls:
                    rpc_url = rpc_url.strip()
                    if not rpc_url:
                        continue
                    try:
                        w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={'timeout': 30}))
                        if w3.is_connected():
                            self.web3_connections[chain_key] = w3
                            self.vault_contracts[chain_key] = w3.eth.contract(
                                address=Web3.to_checksum_address(vault_address),
                                abi=self.VAULT_ABI
                            )
                            logger.info(f"Connected to {config['name']}: {vault_address} via {rpc_url}")
                            break
                        else:
                            logger.warning(f"Could not connect to {config['name']} via {rpc_url}")
                    except Exception as e:
                        logger.warning(f"Failed to initialize {chain_key} via {rpc_url}: {e}")
        
        if not self.web3_connections:
            raise ValueError("No valid Web3 connections established")
        
        # Get signer address from any connection
        first_w3 = list(self.web3_connections.values())[0]
        self.signer = first_w3.eth.account.from_key(self.private_key).address
        logger.info(f"PoR Signer: {self.signer}")
        
        # Initialize exchange manager for off-chain verification
        self.exchange = None
        try:
            from exchange_manager import ExchangeManager
            self.exchange = ExchangeManager()
            logger.info("ExchangeManager initialized for off-chain verification")
        except Exception as e:
            logger.warning(f"ExchangeManager not available: {e}")
        
        # ETH price for USD conversions (fallback)
        self.eth_price_usd = float(os.getenv("ETH_PRICE_USD", "3300"))
        
        # Create output directories
        self.JSON_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        self.HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    
    def get_chain_metrics(self, chain_key: str) -> Optional[ChainMetrics]:
        """Get solvency metrics for a single chain."""
        if chain_key not in self.web3_connections:
            return None
        
        w3 = self.web3_connections[chain_key]
        vault = self.vault_contracts[chain_key]
        config = self.CHAINS[chain_key]
        
        try:
            total_assets_wei = vault.functions.totalAssets().call()
            total_supply_wei = vault.functions.totalSupply().call()
            
            total_assets_eth = float(w3.from_wei(total_assets_wei, 'ether'))
            total_supply_eth = float(w3.from_wei(total_supply_wei, 'ether'))
            
            # Calculate solvency ratio
            if total_supply_eth > 0:
                solvency_ratio = total_assets_eth / total_supply_eth
            else:
                solvency_ratio = 1.0 if total_assets_eth >= 0 else 0.0
            
            return ChainMetrics(
                chain_id=config["chain_id"],
                chain_name=config["name"],
                vault_address=vault.address,
                total_assets_wei=total_assets_wei,
                total_assets_eth=total_assets_eth,
                total_supply_wei=total_supply_wei,
                total_supply_eth=total_supply_eth,
                solvency_ratio=solvency_ratio,
                rpc_healthy=True,
                timestamp=int(time.time())
            )
        except Exception as e:
            logger.error(f"Failed to get metrics for {chain_key}: {e}")
            return ChainMetrics(
                chain_id=config["chain_id"],
                chain_name=config["name"],
                vault_address=os.getenv(config["vault_env"], ""),
                total_assets_wei=0,
                total_assets_eth=0.0,
                total_supply_wei=0,
                total_supply_eth=0.0,
                solvency_ratio=0.0,
                rpc_healthy=False,
                timestamp=int(time.time())
            )
    
    def get_offchain_metrics(self) -> Dict[str, Any]:
        """Get off-chain CEX metrics (Hyperliquid)."""
        if not self.exchange:
            return {
                "venue": "Hyperliquid",
                "equity_usd": 0.0,
                "equity_eth_equiv": 0.0,
                "net_delta": 0.0,
                "short_position_eth": 0.0,
                "available": False
            }
        
        try:
            equity = self.exchange.get_total_equity()
            position = self.exchange.get_aggregate_position("ETH")
            short_size = abs(position.get("size", 0))
            
            return {
                "venue": "Hyperliquid",
                "equity_usd": equity,
                "equity_eth_equiv": equity / self.eth_price_usd if self.eth_price_usd > 0 else 0,
                "net_delta": 0.0,  # Will be calculated based on on-chain assets
                "short_position_eth": short_size,
                "available": True
            }
        except Exception as e:
            logger.warning(f"Failed to get off-chain metrics: {e}")
            return {
                "venue": "Hyperliquid",
                "equity_usd": 0.0,
                "equity_eth_equiv": 0.0,
                "net_delta": 0.0,
                "short_position_eth": 0.0,
                "available": False
            }
    
    def compute_attestation_hash(self, data: Dict) -> str:
        """Compute a deterministic hash of the attestation data."""
        # Create canonical JSON string
        canonical = json.dumps(data, sort_keys=True, separators=(',', ':'))
        return "0x" + hashlib.sha256(canonical.encode()).hexdigest()
    
    def sign_attestation(self, attestation_hash: str) -> str:
        """Sign the attestation hash with the bot's private key."""
        w3 = list(self.web3_connections.values())[0]
        message = encode_defunct(hexstr=attestation_hash)
        signed = w3.eth.account.sign_message(message, private_key=self.private_key)
        return signed.signature.hex()
    
    def generate_por(self) -> AggregatedPoR:
        """Generate a complete Proof of Reserve attestation."""
        timestamp = int(time.time())
        generated_at = datetime.now(tz=timezone.utc).isoformat()
        
        # Collect chain metrics
        chain_metrics: List[ChainMetrics] = []
        block_heights: Dict[str, int] = {}
        
        for chain_key in self.CHAINS.keys():
            metrics = self.get_chain_metrics(chain_key)
            if metrics:
                chain_metrics.append(metrics)
                if chain_key in self.web3_connections:
                    try:
                        block_heights[chain_key] = self.web3_connections[chain_key].eth.block_number
                    except:
                        block_heights[chain_key] = 0
        
        # Aggregate on-chain totals
        total_onchain_assets = sum(m.total_assets_eth for m in chain_metrics)
        total_onchain_liabilities = sum(m.total_supply_eth for m in chain_metrics)
        
        # Get off-chain metrics
        offchain = self.get_offchain_metrics()
        offchain_eth = offchain["equity_eth_equiv"]
        short_position = offchain["short_position_eth"]
        
        # Calculate net delta (deviation from perfect hedge)
        if total_onchain_assets > 0:
            net_delta = abs(1 - (short_position / total_onchain_assets))
        else:
            net_delta = 0.0
        
        offchain["net_delta"] = net_delta
        
        # Calculate aggregate totals
        total_assets = total_onchain_assets + offchain_eth
        total_liabilities = total_onchain_liabilities
        
        if total_liabilities > 0:
            aggregate_solvency_ratio = total_assets / total_liabilities
        else:
            aggregate_solvency_ratio = float('inf') if total_assets > 0 else 1.0
        
        # Determine status
        is_solvent = total_assets >= total_liabilities
        delta_neutral = net_delta <= 0.05  # 5% tolerance
        
        if is_solvent and delta_neutral:
            status = "SOLVENT"
        elif is_solvent:
            status = "WARNING_DELTA"
        elif aggregate_solvency_ratio >= 0.95:
            status = "WARNING_SOLVENCY"
        else:
            status = "CRITICAL"
        
        # Create data for hashing (before signature)
        pre_sign_data = {
            "timestamp": timestamp,
            "total_assets_eth": round(total_assets, 8),
            "total_liabilities_eth": round(total_liabilities, 8),
            "solvency_ratio": round(aggregate_solvency_ratio, 6),
            "chains": [asdict(m) for m in chain_metrics],
            "offchain": offchain
        }
        
        attestation_hash = self.compute_attestation_hash(pre_sign_data)
        signature = self.sign_attestation(attestation_hash)
        
        return AggregatedPoR(
            generated_at=generated_at,
            unix_timestamp=timestamp,
            block_heights=block_heights,
            chains=[asdict(m) for m in chain_metrics],
            total_onchain_assets_eth=round(total_onchain_assets, 8),
            total_onchain_liabilities_eth=round(total_onchain_liabilities, 8),
            offchain_venue=offchain["venue"],
            offchain_equity_usd=round(offchain["equity_usd"], 2),
            offchain_equity_eth_equiv=round(offchain_eth, 8),
            offchain_net_delta=round(net_delta, 6),
            offchain_short_position_eth=round(short_position, 8),
            total_assets_eth=round(total_assets, 8),
            total_liabilities_eth=round(total_liabilities, 8),
            aggregate_solvency_ratio=round(aggregate_solvency_ratio, 6) if aggregate_solvency_ratio != float('inf') else 999999.0,
            is_solvent=is_solvent,
            delta_neutral=delta_neutral,
            attestation_hash=attestation_hash,
            signature=signature,
            signer=self.signer,
            status=status
        )
    
    def validate_invariant(self, por: AggregatedPoR) -> bool:
        """
        Validate the core solvency invariant: Total Assets >= Total Liabilities
        This is the "Kerne Invariant" - the mathematical guarantee of solvency.
        """
        invariant_holds = por.total_assets_eth >= por.total_liabilities_eth
        
        if not invariant_holds:
            logger.critical(
                f"SOLVENCY INVARIANT VIOLATED! "
                f"Assets: {por.total_assets_eth:.4f} ETH < "
                f"Liabilities: {por.total_liabilities_eth:.4f} ETH"
            )
            # Could trigger alerts, pause deposits, etc.
        
        return invariant_holds
    
    def save_por_json(self, por: AggregatedPoR) -> tuple[Path, Path]:
        """Save PoR to latest.json and a timestamped history file."""
        por_dict = asdict(por)
        
        # Pretty-print JSON for readability
        json_content = json.dumps(por_dict, indent=2)
        
        # Save to latest.json (public endpoint source)
        with open(self.PUBLIC_JSON_PATH, 'w') as f:
            f.write(json_content)
        logger.info(f"Saved latest PoR to {self.PUBLIC_JSON_PATH}")
        
        # Save to history
        history_filename = f"por_{datetime.now(tz=timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
        history_path = self.HISTORY_DIR / history_filename
        with open(history_path, 'w') as f:
            f.write(json_content)
        logger.info(f"Saved PoR history to {history_path}")
        
        return self.PUBLIC_JSON_PATH, history_path
    
    def generate_markdown_report(self, por: AggregatedPoR) -> Path:
        """Generate a human-readable markdown report."""
        report_date = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        filename = f"solvency_report_{datetime.now(tz=timezone.utc).strftime('%Y_%m_%d')}.md"
        report_path = Path("docs/reports") / filename
        
        status_emoji = "✅" if por.status == "SOLVENT" else "⚠️" if "WARNING" in por.status else "🚨"
        
        content = f"""# Kerne Protocol - Proof of Reserve Report

**Generated:** {report_date}
**Status:** {status_emoji} {por.status}

---

## Aggregate Solvency

| Metric | Value |
|--------|-------|
| **Total Assets** | {por.total_assets_eth:.6f} ETH |
| **Total Liabilities** | {por.total_liabilities_eth:.6f} ETH |
| **Solvency Ratio** | {por.aggregate_solvency_ratio:.2%} |
| **Is Solvent** | {por.is_solvent} |
| **Delta Neutral** | {por.delta_neutral} (deviation: {por.offchain_net_delta:.2%}) |

---

## On-Chain Assets (by Chain)

"""
        for chain in por.chains:
            content += f"""### {chain['chain_name']}
- **Vault:** `{chain['vault_address']}`
- **Total Assets:** {chain['total_assets_eth']:.6f} ETH
- **Total Supply:** {chain['total_supply_eth']:.6f} ETH  
- **Chain Solvency:** {chain['solvency_ratio']:.2%}
- **RPC Healthy:** {'✅' if chain['rpc_healthy'] else '❌'}

"""
        
        content += f"""---

## Off-Chain Assets (CEX)

| Venue | Equity (USD) | Equity (ETH) | Short Position |
|-------|-------------|--------------|----------------|
| {por.offchain_venue} | ${por.offchain_equity_usd:,.2f} | {por.offchain_equity_eth_equiv:.6f} ETH | {por.offchain_short_position_eth:.6f} ETH |

---

## Cryptographic Attestation

| Field | Value |
|-------|-------|
| **Hash** | `{por.attestation_hash}` |
| **Signature** | `{por.signature[:20]}...{por.signature[-20:]}` |
| **Signer** | `{por.signer}` |

---

## Verification

To verify this attestation:

1. Re-compute the hash from the JSON data (excluding signature)
2. Verify the signature using `ecrecover(hash, signature)` returns `{por.signer}`

**Public JSON Endpoint:** `/api/proof-of-reserve` or `docs/reports/por/latest.json`

---

*Generated by Kerne Automated PoR Bot - Institutional Hardening Mode*
"""
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.info(f"Generated markdown report: {report_path}")
        return report_path
    
    def submit_onchain(self, por: AggregatedPoR):
        """Submit the attestation to the KerneVerificationNode smart contract."""
        verification_node_address = os.getenv("VERIFICATION_NODE_ADDRESS")
        if not verification_node_address:
            logger.warning("VERIFICATION_NODE_ADDRESS not set, skipping on-chain submission")
            return

        # We'll submit to the first available chain (usually Base)
        chain_key = list(self.web3_connections.keys())[0]
        w3 = self.web3_connections[chain_key]
        vault_address = os.getenv(self.CHAINS[chain_key]["vault_env"])

        node_abi = [
            {
                "inputs": [
                    {"internalType": "address", "name": "vault", "type": "address"},
                    {"internalType": "uint256", "name": "offChainAssets", "type": "uint256"},
                    {"internalType": "uint256", "name": "netDelta", "type": "uint256"},
                    {"internalType": "uint256", "name": "exchangeEquity", "type": "uint256"},
                    {"internalType": "uint256", "name": "timestamp", "type": "uint256"},
                    {"internalType": "bytes", "name": "signature", "type": "bytes"}
                ],
                "name": "submitVerifiedAttestation",
                "outputs": [],
                "stateMutability": "nonpayable",
                "type": "function"
            },
            {
                "inputs": [
                    {"internalType": "uint32", "name": "_dstEid", "type": "uint32"},
                    {"internalType": "address", "name": "_vault", "type": "address"},
                    {"internalType": "bytes", "name": "_options", "type": "bytes"}
                ],
                "name": "syncAttestation",
                "outputs": [],
                "stateMutability": "payable",
                "type": "function"
            },
            {
                "inputs": [
                    {"internalType": "uint32", "name": "_dstEid", "type": "uint32"},
                    {"internalType": "address", "name": "_vault", "type": "address"},
                    {"internalType": "bytes", "name": "_options", "type": "bytes"},
                    {"internalType": "bool", "name": "_payInLzToken", "type": "bool"}
                ],
                "name": "quote",
                "outputs": [
                    {
                        "components": [
                            {"internalType": "uint256", "name": "nativeFee", "type": "uint256"},
                            {"internalType": "uint256", "name": "lzTokenFee", "type": "uint256"}
                        ],
                        "internalType": "struct MessagingFee",
                        "name": "fee",
                        "type": "tuple"
                    }
                ],
                "stateMutability": "view",
                "type": "function"
            }
        ]
        
        try:
            node = w3.eth.contract(address=Web3.to_checksum_address(verification_node_address), abi=node_abi)
            
            assets_wei = w3.to_wei(por.offchain_equity_eth_equiv, 'ether')
            delta_wei = int(por.offchain_net_delta * 1e18)
            equity_wei = w3.to_wei(por.offchain_equity_eth_equiv, 'ether')
            
            sig = por.signature
            
            tx = node.functions.submitVerifiedAttestation(
                Web3.to_checksum_address(vault_address),
                assets_wei,
                delta_wei,
                equity_wei,
                por.unix_timestamp,
                bytes.fromhex(sig[2:] if sig.startswith("0x") else sig)
            ).build_transaction({
                'from': self.signer,
                'nonce': w3.eth.get_transaction_count(self.signer),
                'gas': 300000,
                'gasPrice': w3.eth.gas_price
            })
            
            signed_tx = w3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
            logger.success(f"Attestation published on-chain ({chain_key}): {tx_hash.hex()}")
            
            # Sync to Arbitrum if on Base
            chain_id = w3.eth.chain_id
            if chain_id == 8453: # Base
                arb_eid = 30110
                options = bytes.fromhex("00030100110100000000000000000000000000030d40")
                
                fee = node.functions.quote(arb_eid, Web3.to_checksum_address(vault_address), options, False).call()
                native_fee = fee[0]
                
                sync_tx = node.functions.syncAttestation(
                    arb_eid,
                    Web3.to_checksum_address(vault_address),
                    options
                ).build_transaction({
                    'from': self.signer,
                    'nonce': w3.eth.get_transaction_count(self.signer),
                    'value': native_fee,
                    'gas': 500000,
                    'gasPrice': w3.eth.gas_price
                })
                
                signed_sync_tx = w3.eth.account.sign_transaction(sync_tx, self.private_key)
                sync_tx_hash = w3.eth.send_raw_transaction(signed_sync_tx.rawTransaction)
                logger.success(f"Attestation synced to Arbitrum: {sync_tx_hash.hex()}")
                
        except Exception as e:
            logger.error(f"Failed to publish attestation on-chain: {e}")

    def run(self, save_json: bool = True, save_markdown: bool = True, validate: bool = True) -> AggregatedPoR:
        """
        Run a complete PoR attestation cycle.
        
        Returns the AggregatedPoR object. Raises if validation fails and validate=True.
        """
        logger.info("=" * 60)
        logger.info("KERNE PROOF OF RESERVE - ATTESTATION CYCLE")
        logger.info("=" * 60)
        
        # Generate PoR
        por = self.generate_por()
        
        # Log summary
        logger.info(f"Status: {por.status}")
        logger.info(f"Total Assets: {por.total_assets_eth:.6f} ETH")
        logger.info(f"Total Liabilities: {por.total_liabilities_eth:.6f} ETH")
        logger.info(f"Solvency Ratio: {por.aggregate_solvency_ratio:.2%}")
        logger.info(f"Delta Deviation: {por.offchain_net_delta:.2%}")
        
        # Validate invariant
        if validate:
            invariant_ok = self.validate_invariant(por)
            if not invariant_ok:
                logger.critical("INVARIANT VALIDATION FAILED - REPORT NOT PUBLISHED")
                # In production, could send emergency alerts here
                raise ValueError("Solvency invariant violated - aborting PoR publication")
        
        # Save outputs
        if save_json:
            self.save_por_json(por)
        
        if save_markdown:
            self.generate_markdown_report(por)
            
        # Submit on-chain
        self.submit_onchain(por)
        
        logger.success(f"PoR attestation complete: {por.status}")
        logger.info("=" * 60)
        
        return por


def main():
    """CLI entry point for manual PoR generation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Kerne Proof of Reserve Attestation")
    parser.add_argument("--no-json", action="store_true", help="Skip JSON output")
    parser.add_argument("--no-markdown", action="store_true", help="Skip markdown report")
    parser.add_argument("--no-validate", action="store_true", help="Skip invariant validation")
    args = parser.parse_args()
    
    bot = AutomatedPoRBot()
    por = bot.run(
        save_json=not args.no_json,
        save_markdown=not args.no_markdown,
        validate=not args.no_validate
    )
    
    print(f"\n✅ PoR Status: {por.status}")
    print(f"   Solvency Ratio: {por.aggregate_solvency_ratio:.2%}")
    print(f"   Attestation Hash: {por.attestation_hash}")


if __name__ == "__main__":
    main()
