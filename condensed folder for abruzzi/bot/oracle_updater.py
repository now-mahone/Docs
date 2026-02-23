#!/usr/bin/env python3
"""
Kerne Price Oracle Updater

This script updates the TWAP observation on the KernePriceOracle contract.
It should be run periodically (e.g., every 5-10 minutes) to keep the oracle fresh.

Usage:
    python oracle_updater.py [--network base]

Environment Variables:
    PRIVATE_KEY: Private key for the updater account
    RPC_URL: RPC URL for the network (optional, uses default)
"""

import os
import sys
import json
import time
from web3 import Web3
from eth_account import Account

# Network configurations
NETWORKS = {
    'base': {
        'rpc': 'https://mainnet.base.org',
        'chain_id': 8453,
        'oracle_address': None,  # Set after deployment
        'explorer': 'https://basescan.org'
    },
    'base_sepolia': {
        'rpc': 'https://sepolia.base.org',
        'chain_id': 84532,
        'oracle_address': None,
        'explorer': 'https://sepolia.basescan.org'
    }
}

# ABI for KernePriceOracle (minimal - just what we need)
ORACLE_ABI = [
    {
        "inputs": [],
        "name": "updateObservation",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "lastObservation",
        "outputs": [
            {"internalType": "uint256", "name": "timestamp", "type": "uint256"},
            {"internalType": "int56", "name": "tickCumulative", "type": "int56"},
            {"internalType": "uint160", "name": "secondsPerLiquidityCumulativeX128", "type": "uint160"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "isPriceValid",
        "outputs": [{"internalType": "bool", "name": "valid", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "getPrice",
        "outputs": [{"internalType": "uint256", "name": "price", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "getPriceSources",
        "outputs": [
            {"internalType": "uint256", "name": "chainlinkPrice", "type": "uint256"},
            {"internalType": "uint256", "name": "uniswapTwapPrice", "type": "uint256"},
            {"internalType": "uint256", "name": "timestamp", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

class OracleUpdater:
    def __init__(self, network_name: str):
        self.network_name = network_name
        self.config = NETWORKS.get(network_name)
        
        if not self.config:
            raise ValueError(f"Unknown network: {network_name}")
        
        # Initialize Web3
        rpc_url = os.getenv('RPC_URL', self.config['rpc'])
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        if not self.w3.is_connected():
            raise ConnectionError(f"Failed to connect to {rpc_url}")
        
        # Load account
        private_key = os.getenv('PRIVATE_KEY')
        if not private_key:
            raise ValueError("PRIVATE_KEY environment variable not set")
        
        self.account = Account.from_key(private_key)
        print(f"Loaded account: {self.account.address}")
        
        # Load oracle address
        self.oracle_address = os.getenv('ORACLE_ADDRESS', self.config['oracle_address'])
        if not self.oracle_address:
            raise ValueError("ORACLE_ADDRESS not set. Set it in environment or config.")
        
        # Initialize contract
        self.oracle = self.w3.eth.contract(
            address=Web3.to_checksum_address(self.oracle_address),
            abi=ORACLE_ABI
        )
    
    def get_status(self) -> dict:
        """Get current oracle status"""
        try:
            is_valid = self.oracle.functions.isPriceValid().call()
            price = self.oracle.functions.getPrice().call()
            chainlink_price, twap_price, timestamp = self.oracle.functions.getPriceSources().call()
            
            # Convert price from 18 decimals to readable
            price_readable = price / 1e18
            
            return {
                'is_valid': is_valid,
                'price': price_readable,
                'chainlink_price': chainlink_price / 1e18,
                'twap_price': twap_price / 1e18,
                'last_update': timestamp,
                'age_seconds': int(time.time()) - timestamp
            }
        except Exception as e:
            return {'error': str(e)}
    
    def update_observation(self) -> dict:
        """Update the TWAP observation"""
        try:
            # Build transaction
            tx = self.oracle.functions.updateObservation().build_transaction({
                'from': self.account.address,
                'gas': 100000,  # Conservative gas limit
                'gasPrice': self.w3.eth.gas_price,
                'nonce': self.w3.eth.get_transaction_count(self.account.address),
                'chainId': self.config['chain_id']
            })
            
            # Sign and send
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            
            print(f"Transaction sent: {tx_hash.hex()}")
            print(f"Explorer: {self.config['explorer']}/tx/{tx_hash.hex()}")
            
            # Wait for confirmation
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash)
            
            return {
                'success': receipt['status'] == 1,
                'tx_hash': tx_hash.hex(),
                'gas_used': receipt['gasUsed'],
                'block_number': receipt['blockNumber']
            }
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def run(self, dry_run: bool = False):
        """Run the updater"""
        print(f"\n{'='*50}")
        print(f"Kerne Price Oracle Updater")
        print(f"Network: {self.network_name}")
        print(f"{'='*50}\n")
        
        # Get current status
        status = self.get_status()
        
        if 'error' in status:
            print(f"Error getting status: {status['error']}")
            return False
        
        print(f"Current Status:")
        print(f"  Price: ${status['price']:.2f}")
        print(f"  Chainlink: ${status['chainlink_price']:.2f}")
        print(f"  TWAP: ${status['twap_price']:.2f}")
        print(f"  Valid: {status['is_valid']}")
        print(f"  Last Update: {status['age_seconds']} seconds ago")
        
        # Check if update needed (every 10 minutes)
        if status['age_seconds'] < 600:
            print(f"\nObservation is fresh (< 10 minutes old). No update needed.")
            return True
        
        if dry_run:
            print(f"\n[DRY RUN] Would update observation")
            return True
        
        # Update observation
        print(f"\nUpdating observation...")
        result = self.update_observation()
        
        if result['success']:
            print(f"\n✅ Update successful!")
            print(f"  TX: {result['tx_hash']}")
            print(f"  Gas Used: {result['gas_used']}")
            return True
        else:
            print(f"\n❌ Update failed: {result.get('error', 'Unknown error')}")
            return False


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Kerne Price Oracle Updater')
    parser.add_argument('--network', default='base', help='Network to use')
    parser.add_argument('--dry-run', action='store_true', help='Simulate without sending tx')
    parser.add_argument('--status-only', action='store_true', help='Only show status')
    args = parser.parse_args()
    
    try:
        updater = OracleUpdater(args.network)
        
        if args.status_only:
            status = updater.get_status()
            print(json.dumps(status, indent=2))
        else:
            success = updater.run(dry_run=args.dry_run)
            sys.exit(0 if success else 1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()