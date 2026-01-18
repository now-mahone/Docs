# Created: 2026-01-17
"""
Kerne Zero-Fee Intent Network (ZIN) Solver - Complete CowSwap/UniswapX Integration
Transforms Kerne into Base's primary execution engine for high-volume trading.

This bot:
1. Monitors intent-based trading protocols (CowSwap, UniswapX)
2. Uses Kerne's internal liquidity to fulfill intents at zero cost
3. Captures the spread as profit
4. Routes profits to the profit vault

Every trade filled shows "Filled by Kerne" for organic awareness.
"""

import os
from pathlib import Path

# Load .env file from bot directory
def _load_env():
    """Load environment variables from bot/.env file."""
    # Try multiple possible locations for .env
    possible_paths = [
        Path(__file__).parent.parent / ".env",  # bot/.env from solver/
        Path.cwd() / "bot" / ".env",            # bot/.env from project root
        Path.cwd() / ".env",                     # .env in current dir
    ]
    
    for env_path in possible_paths:
        if env_path.exists():
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, _, value = line.partition('=')
                        key = key.strip()
                        value = value.strip()
                        # Don't override existing env vars
                        if key and key not in os.environ:
                            os.environ[key] = value
            return str(env_path)
    return None

_env_path = _load_env()
import asyncio
import json
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger
from web3 import Web3
from web3.contract import Contract
from eth_account import Account
from eth_abi import encode
import aiohttp

# =============================================================================
# CONFIGURATION
# =============================================================================

# RPC Configuration with fallback
RPC_URLS = [
    os.getenv("BASE_RPC_URL"),
    os.getenv("RPC_URL"),
    "https://mainnet.base.org",
    "https://base.llamarpc.com",
    "https://base.drpc.org",
]
RPC_URLS = [url for url in RPC_URLS if url]  # Filter None values

PRIVATE_KEY = os.getenv("PRIVATE_KEY")
ZIN_EXECUTOR_ADDRESS = os.getenv("ZIN_EXECUTOR_ADDRESS", "0x04F52F9F4dAb1ba2330841Af85dAeeB8eaC9E995")
ZIN_POOL_ADDRESS = os.getenv("ZIN_POOL_ADDRESS", "0xB9BdF6F3Fc3819b61f6fE799bE1395501822d0c7")
PROFIT_VAULT_ADDRESS = os.getenv("PROFIT_VAULT_ADDRESS")
ONE_INCH_API_KEY = os.getenv("ONE_INCH_API_KEY")
ZIN_SOLVER_LIVE = os.getenv("ZIN_SOLVER_LIVE", "false").lower() == "true"
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")

# Micro-cap live-run guardrails
ZIN_MIN_PROFIT_BPS = int(os.getenv("ZIN_MIN_PROFIT_BPS", "8"))
ZIN_MAX_INTENT_AMOUNT = int(os.getenv("ZIN_MAX_INTENT_AMOUNT", "0"))
ZIN_MAX_GAS_PRICE_GWEI = int(os.getenv("ZIN_MAX_GAS_PRICE_GWEI", "40"))
ZIN_MAX_INTENTS_PER_CYCLE = int(os.getenv("ZIN_MAX_INTENTS_PER_CYCLE", "2"))
ZIN_MIN_ORDER_TTL_SECONDS = int(os.getenv("ZIN_MIN_ORDER_TTL_SECONDS", "30"))
ZIN_MAX_PRICE_IMPACT_BPS = int(os.getenv("ZIN_MAX_PRICE_IMPACT_BPS", "75"))
ZIN_MAX_INTENT_AMOUNT_BY_TOKEN = os.getenv("ZIN_MAX_INTENT_AMOUNT_BY_TOKEN", "")

# Chain Configuration
CHAIN_ID = 8453  # Base Mainnet

# =============================================================================
# CONSTANTS - Base Mainnet Addresses
# =============================================================================

# Aggregator Routers
ONE_INCH_ROUTER = "0x111111125421cA6dc452d289314280a0f8842A65"
UNISWAP_UNIVERSAL_ROUTER = "0x3fC91A3afd70395Cd496C647d5a6CC9D4B2b7FAD"
UNISWAP_V3_ROUTER = "0xE592427A0AEce92De3Edee1F18E0157C05861564"
AERODROME_ROUTER = "0xcF77a3Ba9A5CA399B7c97c478569a74DD55C726f"

# Token Addresses (Base Mainnet)
WETH = "0x4200000000000000000000000000000000000006"
USDC = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
WSTETH = "0xc1CBa3fCea344f92D9239c08C0568f6F2F0ee452"
CBETH = "0x2Ae3F1Ec7F1F5012CFEab0185bfc7aa3cf0DEc22"
RETH = "0xB6fe221Fe9EeF5aBa221c348bA20A1Bf5e73624c"

# CowSwap API
COWSWAP_API_BASE = "https://api.cow.fi/base/api/v1"

# UniswapX API Configuration per chain
UNISWAPX_API_CONFIG = {
    "base": {
        "api_url": "https://api.uniswap.org/v2/orders",
        "chain_id": 8453,
        "order_type": "Priority",
        "reactor": "0x000000001Ec5656dcdB24D90DFa42742738De729"
    },
    "unichain": {
        "api_url": "https://api.uniswap.org/v2/orders",
        "chain_id": 130,
        "order_type": "Priority",
        "reactor": "0x00000006021a6Bce796be7ba509BBBA71e956e37"
    },
    "arbitrum": {
        "api_url": "https://api.uniswap.org/v2/orders",
        "chain_id": 42161,
        "order_type": "Dutch_V2",
        "reactor": "0x1bd1aAdc9E230626C44a139d7E70d842749351eb"
    },
    "mainnet": {
        "api_url": "https://api.uniswap.org/v2/orders",
        "chain_id": 1,
        "order_type": "Dutch_V2",
        "reactor": "0x6000da47483062A0D734Ba3dc7576Ce6A0B645C4"
    }
}

# LST Targets - tokens we want to fulfill intents for
LST_TARGETS = {
    WSTETH.lower(): "wstETH",
    CBETH.lower(): "cbETH",
    RETH.lower(): "rETH",
    WETH.lower(): "WETH",
    USDC.lower(): "USDC",
}

# =============================================================================
# CONTRACT ABIs
# =============================================================================

ZIN_EXECUTOR_ABI = [
    {
        "inputs": [
            {"name": "lender", "type": "address"},
            {"name": "tokenIn", "type": "address"},
            {"name": "tokenOut", "type": "address"},
            {"name": "amount", "type": "uint256"},
            {"name": "user", "type": "address"},
            {"name": "aggregatorData", "type": "bytes"},
            {"name": "safetyParams", "type": "bytes"}
        ],
        "name": "fulfillIntent",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "getZINMetrics",
        "outputs": [
            {"name": "totalSpread", "type": "uint256"},
            {"name": "totalIntents", "type": "uint256"},
            {"name": "currentVault", "type": "address"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"name": "token", "type": "address"}],
        "name": "getTokenSpread",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
]

VAULT_ABI = [
    {
        "inputs": [{"name": "token", "type": "address"}],
        "name": "maxFlashLoan",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"name": "token", "type": "address"}, {"name": "amount", "type": "uint256"}],
        "name": "flashFee",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "totalAssets",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
]

ERC20_ABI = [
    {
        "inputs": [{"name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "stateMutability": "view",
        "type": "function"
    }
]


# =============================================================================
# DATA CLASSES
# =============================================================================

class IntentVenue(Enum):
    COWSWAP = "CowSwap"
    UNISWAPX = "UniswapX"
    DIRECT = "Direct"


@dataclass
class IntentData:
    """Represents a user intent to be fulfilled."""
    order_id: str
    venue: IntentVenue
    user: str
    token_in: str
    token_out: str
    amount_in: int
    amount_out: int
    price_limit: int
    deadline: int
    signature: str = ""
    encoded_order: str = ""
    raw_order: Dict = field(default_factory=dict)
    
    @property
    def token_in_symbol(self) -> str:
        return LST_TARGETS.get(self.token_in.lower(), "UNKNOWN")
    
    @property
    def token_out_symbol(self) -> str:
        return LST_TARGETS.get(self.token_out.lower(), "UNKNOWN")


@dataclass
class QuoteResult:
    """Result from an aggregator quote."""
    aggregator: str
    calldata: bytes
    expected_output: int
    gas_estimate: int
    price_impact_bps: int


@dataclass
class FulfillmentResult:
    """Result of intent fulfillment."""
    success: bool
    tx_hash: Optional[str]
    profit_captured: int
    profit_bps: int
    gas_used: int
    error: Optional[str] = None


# =============================================================================
# ZIN SOLVER - MAIN CLASS
# =============================================================================

class ZINSolver:
    """
    Zero-Fee Intent Network Solver - Complete CowSwap/UniswapX Integration
    
    Core responsibilities:
    - Detect profitable intents from CowSwap/UniswapX
    - Fulfill intents using Kerne's internal liquidity (zero-fee flash loans)
    - Capture spread profit and route to profit vault
    - Monitor and report ZIN performance
    
    Every trade filled shows "Filled by Kerne" for organic awareness.
    """
    
    def __init__(self):
        self.w3 = self._init_web3()
        self.account = Account.from_key(PRIVATE_KEY) if PRIVATE_KEY else None
        self.live_mode = ZIN_SOLVER_LIVE
        self.active_chain = os.getenv("ACTIVE_CHAIN", "base").lower()
        self.uniswapx_config = UNISWAPX_API_CONFIG.get(self.active_chain, UNISWAPX_API_CONFIG["base"])
        
        self._validate_config()
        self._init_contracts()
        self._init_logging()
        
        # Performance tracking
        self.total_intents_processed = 0
        self.total_profit_captured = 0
        self.failed_intents = 0
        self.intents_by_venue: Dict[str, int] = {"CowSwap": 0, "UniswapX": 0}
        
        # Health check flags
        self._cowswap_health_logged = False
        self._uniswapx_health_logged = False
        
        # Rate limiting
        self._last_cowswap_fetch = 0
        self._last_uniswapx_fetch = 0
        self._min_fetch_interval = 2.0  # seconds
        self._token_amount_caps = self._parse_token_amount_caps()
        
        # Auto-scaling configuration
        self._auto_scale_enabled = os.getenv("ZIN_AUTO_SCALE", "true").lower() == "true"
        self._min_liquidity_ratio = float(os.getenv("ZIN_MIN_LIQUIDITY_RATIO", "0.1"))  # Min 10% of pool
        self._max_liquidity_ratio = float(os.getenv("ZIN_MAX_LIQUIDITY_RATIO", "0.5"))  # Max 50% of pool
        self._scale_factor_base = float(os.getenv("ZIN_SCALE_FACTOR", "1.0"))  # Multiplier for position sizing
        self._liquidity_cache: Dict[str, Tuple[int, float]] = {}  # token -> (liquidity, timestamp)
        self._liquidity_cache_ttl = 30.0  # seconds
        
        logger.info("=" * 60)
        logger.info("ZIN Solver Initialized - Kerne Intent Execution Engine")
        logger.info("=" * 60)
        logger.info(f"Account: {self.account.address if self.account else 'NOT SET'}")
        logger.info(f"ZIN Executor: {ZIN_EXECUTOR_ADDRESS}")
        logger.info(f"ZIN Pool: {ZIN_POOL_ADDRESS}")
        logger.info(f"Profit Vault: {PROFIT_VAULT_ADDRESS}")
        logger.info(f"Live Mode: {self.live_mode}")
        logger.info(f"Active Chain: {self.active_chain}")
        logger.info(
            "Guardrails: min_profit_bps={} max_intent_amount={} max_gas_price_gwei={} max_intents_per_cycle={}"
            .format(
                ZIN_MIN_PROFIT_BPS,
                ZIN_MAX_INTENT_AMOUNT,
                ZIN_MAX_GAS_PRICE_GWEI,
                ZIN_MAX_INTENTS_PER_CYCLE
            )
        )
        logger.info(
            "Guardrails: min_ttl_seconds={} max_price_impact_bps={} per_token_caps={}"
            .format(
                ZIN_MIN_ORDER_TTL_SECONDS,
                ZIN_MAX_PRICE_IMPACT_BPS,
                self._token_amount_caps
            )
        )
        logger.info("=" * 60)
    
    def _init_web3(self) -> Web3:
        """Initialize Web3 with RPC fallback."""
        for rpc_url in RPC_URLS:
            try:
                w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={'timeout': 30}))
                if w3.is_connected():
                    logger.info(f"Connected to RPC: {rpc_url[:50]}...")
                    return w3
            except Exception as e:
                logger.warning(f"Failed to connect to {rpc_url}: {e}")
        
        raise ConnectionError("Failed to connect to any RPC endpoint")
    
    def _validate_config(self):
        """Validate required environment configuration."""
        missing = []
        if not PRIVATE_KEY:
            missing.append("PRIVATE_KEY")
        if not ZIN_EXECUTOR_ADDRESS:
            missing.append("ZIN_EXECUTOR_ADDRESS")
        
        if self.live_mode:
            # 1inch is OPTIONAL - Aerodrome on-chain quoting is the primary source
            if not ONE_INCH_API_KEY:
                logger.info("Running in Aerodrome-only mode (no 1inch API key)")
            if not PROFIT_VAULT_ADDRESS:
                missing.append("PROFIT_VAULT_ADDRESS")
        
        if ZIN_MIN_PROFIT_BPS < 0:
            missing.append("ZIN_MIN_PROFIT_BPS")
        if ZIN_MAX_INTENT_AMOUNT < 0:
            missing.append("ZIN_MAX_INTENT_AMOUNT")
        if ZIN_MAX_GAS_PRICE_GWEI <= 0:
            missing.append("ZIN_MAX_GAS_PRICE_GWEI")
        if ZIN_MAX_INTENTS_PER_CYCLE <= 0:
            missing.append("ZIN_MAX_INTENTS_PER_CYCLE")
        if ZIN_MIN_ORDER_TTL_SECONDS < 0:
            missing.append("ZIN_MIN_ORDER_TTL_SECONDS")
        if ZIN_MAX_PRICE_IMPACT_BPS < 0:
            missing.append("ZIN_MAX_PRICE_IMPACT_BPS")
        
        if missing:
            raise ValueError(f"Missing required env vars: {', '.join(missing)}")
    
    def _init_contracts(self):
        """Initialize contract instances."""
        self.zin_executor = self.w3.eth.contract(
            address=Web3.to_checksum_address(ZIN_EXECUTOR_ADDRESS),
            abi=ZIN_EXECUTOR_ABI
        )
        
        self.zin_pool = self.w3.eth.contract(
            address=Web3.to_checksum_address(ZIN_POOL_ADDRESS),
            abi=VAULT_ABI
        )
    
    def _init_logging(self):
        """Initialize profit log file."""
        self.profit_log_path = "bot/solver/zin_profit_log.csv"
        log_dir = os.path.dirname(self.profit_log_path)
        
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        
        if not os.path.exists(self.profit_log_path):
            with open(self.profit_log_path, "w") as f:
                f.write("timestamp,venue,order_id,token_in,token_out,amount_out,profit_bps,gas_used,tx_hash,status\n")

    def _parse_token_amount_caps(self) -> Dict[str, int]:
        """Parse per-token intent caps from env."""
        caps: Dict[str, int] = {}
        if not ZIN_MAX_INTENT_AMOUNT_BY_TOKEN:
            return caps

        symbol_to_address = {symbol.upper(): address for address, symbol in LST_TARGETS.items()}
        entries = [item.strip() for item in ZIN_MAX_INTENT_AMOUNT_BY_TOKEN.split(",") if item.strip()]

        for entry in entries:
            if ":" in entry:
                key, value = entry.split(":", 1)
            elif "=" in entry:
                key, value = entry.split("=", 1)
            else:
                logger.warning(f"Invalid token cap entry: {entry}")
                continue

            key = key.strip()
            value = value.strip()
            if not key or not value:
                continue

            try:
                cap = int(value)
            except ValueError:
                logger.warning(f"Invalid cap value for {key}: {value}")
                continue

            token_key = key.lower()
            if token_key in LST_TARGETS:
                caps[token_key] = cap
                continue

            symbol_key = key.upper()
            address = symbol_to_address.get(symbol_key)
            if address:
                caps[address] = cap
            else:
                logger.warning(f"Unknown token cap key: {key}")

        return caps

    def _get_intent_cap(self, intent: IntentData) -> int:
        """Resolve the max allowed intent size for the token out."""
        token_out_key = intent.token_out.lower()
        if token_out_key in self._token_amount_caps:
            return self._token_amount_caps[token_out_key]

        return ZIN_MAX_INTENT_AMOUNT

    def _is_gas_price_ok(self) -> bool:
        """Check if current gas price is within guardrails."""
        gas_price_gwei = self.w3.eth.gas_price / 1e9
        if gas_price_gwei > ZIN_MAX_GAS_PRICE_GWEI:
            logger.debug(f"Gas price too high: {gas_price_gwei:.2f} gwei")
            return False
        return True

    # =========================================================================
    # COWSWAP INTEGRATION
    # =========================================================================
    
    async def fetch_cowswap_orders(self) -> List[IntentData]:
        """
        Fetch open orders from CowSwap auction API.
        
        CowSwap uses a batch auction model where solvers compete to fill orders.
        We monitor the auction endpoint for orders we can profitably fill.
        
        API Docs: https://docs.cow.fi/cow-protocol/reference/apis/orderbook
        """
        # Rate limiting
        now = time.time()
        if now - self._last_cowswap_fetch < self._min_fetch_interval:
            return []
        self._last_cowswap_fetch = now
        
        intents = []
        
        async with aiohttp.ClientSession() as session:
            try:
                # Fetch current auction
                async with session.get(
                    f"{COWSWAP_API_BASE}/auction",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if not self._cowswap_health_logged:
                        self._cowswap_health_logged = True
                        if resp.status == 200:
                            logger.info(f"CowSwap: API reachable (endpoint={COWSWAP_API_BASE})")
                        elif resp.status == 403:
                            logger.info("CowSwap: Auction API requires solver registration (403) - using UniswapX only")
                        else:
                            logger.warning(f"CowSwap: API health check failed (status={resp.status})")
                    
                    if resp.status == 200:
                        auction_data = await resp.json()
                        orders = auction_data.get('orders', [])
                        
                        if orders:
                            logger.debug(f"CowSwap: Fetched {len(orders)} orders from auction")
                        
                        for order in orders:
                            intent = self._normalize_cowswap_order(order)
                            if intent:
                                intents.append(intent)
                    
                    elif resp.status == 429:
                        logger.warning("CowSwap: Rate limited (429). Backing off...")
                    else:
                        logger.debug(f"CowSwap: API returned status {resp.status}")
                        
            except asyncio.TimeoutError:
                logger.warning("CowSwap: Request timeout")
            except aiohttp.ClientError as e:
                logger.error(f"CowSwap: Network error: {e}")
            except Exception as e:
                logger.error(f"CowSwap: Unexpected error: {e}")
        
        return intents
    
    def _normalize_cowswap_order(self, order: Dict) -> Optional[IntentData]:
        """
        Normalize CowSwap order to internal IntentData format.
        
        CowSwap Order Structure:
        {
            "uid": "0x...",
            "sellToken": "0x...",
            "buyToken": "0x...",
            "sellAmount": "1000000000000000000",
            "buyAmount": "2000000000",
            "validTo": 1234567890,
            "owner": "0x...",
            "signature": "0x...",
            ...
        }
        """
        try:
            order_id = order.get('uid', '')
            sell_token = order.get('sellToken', '').lower()
            buy_token = order.get('buyToken', '').lower()
            sell_amount = int(order.get('sellAmount', 0))
            buy_amount = int(order.get('buyAmount', 0))
            valid_to = int(order.get('validTo', 0))
            owner = order.get('owner', '')
            signature = order.get('signature', '')
            
            # Skip if missing critical data
            if not all([order_id, sell_token, buy_token, sell_amount, buy_amount, owner]):
                return None
            
            # Skip expired orders
            if valid_to < int(time.time()):
                return None
            
            # Check if this is a token pair we're interested in
            if not self._is_target_pair(sell_token, buy_token):
                return None
            
            return IntentData(
                order_id=order_id,
                venue=IntentVenue.COWSWAP,
                user=owner,
                token_in=sell_token,
                token_out=buy_token,
                amount_in=sell_amount,
                amount_out=buy_amount,
                price_limit=buy_amount,  # Minimum output expected
                deadline=valid_to,
                signature=signature,
                raw_order=order
            )
            
        except Exception as e:
            logger.error(f"CowSwap: Error normalizing order: {e}")
            return None

    # =========================================================================
    # UNISWAPX INTEGRATION
    # =========================================================================
    
    async def fetch_uniswapx_orders(self) -> List[IntentData]:
        """
        Fetch open orders from UniswapX API.
        
        UniswapX supports different order types per chain:
        - Base/Unichain: Priority Orders
        - Arbitrum/Mainnet: Dutch V2 Orders
        
        API Docs: https://api.uniswap.org/v2/uniswapx/docs
        """
        # Rate limiting
        now = time.time()
        if now - self._last_uniswapx_fetch < self._min_fetch_interval:
            return []
        self._last_uniswapx_fetch = now
        
        intents = []
        config = self.uniswapx_config
        
        params = {
            "orderStatus": "open",
            "chainId": config["chain_id"],
            "orderType": config["order_type"],
            "limit": 100,
        }
        
        headers = {
            "Accept": "application/json",
            "Origin": "https://app.uniswap.org"
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    config["api_url"],
                    params=params,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if not self._uniswapx_health_logged:
                        self._uniswapx_health_logged = True
                        if resp.status == 200:
                            logger.info(
                                f"UniswapX: API reachable (chainId={config['chain_id']}, "
                                f"orderType={config['order_type']})"
                            )
                        else:
                            logger.warning(
                                f"UniswapX: API health check failed (status={resp.status})"
                            )
                    
                    if resp.status == 200:
                        data = await resp.json()
                        orders = data.get('orders', [])
                        
                        if orders:
                            logger.debug(f"UniswapX: Fetched {len(orders)} open orders")
                        
                        for order in orders:
                            intent = self._normalize_uniswapx_order(order)
                            if intent:
                                intents.append(intent)
                    
                    elif resp.status == 429:
                        logger.warning("UniswapX: Rate limited (429). Backing off...")
                    else:
                        logger.debug(f"UniswapX: API returned status {resp.status}")
                        
            except asyncio.TimeoutError:
                logger.warning("UniswapX: Request timeout")
            except aiohttp.ClientError as e:
                logger.error(f"UniswapX: Network error: {e}")
            except Exception as e:
                logger.error(f"UniswapX: Unexpected error: {e}")
        
        return intents
    
    def _normalize_uniswapx_order(self, order: Dict) -> Optional[IntentData]:
        """
        Normalize UniswapX order to internal IntentData format.
        
        UniswapX Order Structure (Priority/Dutch):
        {
            "orderHash": "0x...",
            "orderStatus": "open",
            "chainId": 8453,
            "input": {"token": "0x...", "amount": "1000000000000000000"},
            "outputs": [{"token": "0x...", "amount": "..."}],
            "swapper": "0x...",
            "createdAt": 1234567890,
            "encodedOrder": "0x..."
        }
        """
        try:
            order_hash = order.get('orderHash', '')
            
            # Extract input (what the user is selling)
            input_data = order.get('input', {})
            sell_token = input_data.get('token', '').lower()
            sell_amount = int(input_data.get('amount', 0))
            
            # Extract outputs (what the user wants to buy)
            outputs = order.get('outputs', [])
            if not outputs:
                return None
            
            primary_output = outputs[0]
            buy_token = primary_output.get('token', '').lower()
            buy_amount = int(primary_output.get('amount', 0))
            
            swapper = order.get('swapper', '')
            created_at = order.get('createdAt', 0)
            encoded_order = order.get('encodedOrder', '')
            
            # Skip if missing critical data
            if not all([order_hash, sell_token, buy_token, sell_amount, buy_amount, swapper]):
                return None
            
            # Check if this is a token pair we're interested in
            if not self._is_target_pair(sell_token, buy_token):
                return None
            
            # Calculate deadline (UniswapX orders typically have ~2 min validity)
            deadline = int(time.time()) + 120
            
            return IntentData(
                order_id=order_hash,
                venue=IntentVenue.UNISWAPX,
                user=swapper,
                token_in=sell_token,
                token_out=buy_token,
                amount_in=sell_amount,
                amount_out=buy_amount,
                price_limit=buy_amount,
                deadline=deadline,
                encoded_order=encoded_order,
                raw_order=order
            )
            
        except Exception as e:
            logger.error(f"UniswapX: Error normalizing order: {e}")
            return None
    
    def _is_target_pair(self, token_in: str, token_out: str) -> bool:
        """Check if this token pair is one we want to fulfill."""
        token_in = token_in.lower()
        token_out = token_out.lower()
        
        # We're interested in pairs involving our target tokens
        return token_in in LST_TARGETS or token_out in LST_TARGETS

    # =========================================================================
    # AGGREGATOR QUOTING
    # =========================================================================
    
    async def get_best_quote(
        self,
        token_in: str,
        token_out: str,
        amount_in: int
    ) -> Optional[QuoteResult]:
        """
        Get the best quote from available aggregators.
        
        Aerodrome-first mode: Uses on-chain quoting (no API key needed).
        Falls back to 1inch only if configured and Aerodrome fails.
        """
        # Try Aerodrome first (on-chain, no API key needed)
        quote = await self._get_aerodrome_quote(token_in, token_out, amount_in)
        if quote:
            return quote
        
        # Fallback to 1inch if API key is configured
        if ONE_INCH_API_KEY:
            quote = await self._get_1inch_quote(token_in, token_out, amount_in)
            if quote:
                return quote
        
        logger.warning(f"No quote available for {token_in[:10]}... -> {token_out[:10]}...")
        return None
    
    async def _get_1inch_quote(
        self,
        token_in: str,
        token_out: str,
        amount_in: int
    ) -> Optional[QuoteResult]:
        """
        Get swap quote from 1inch API.
        
        1inch provides the best aggregated liquidity across DEXs.
        API Docs: https://portal.1inch.dev/documentation/swap/swagger
        """
        if not ONE_INCH_API_KEY:
            logger.debug("1inch: API key not configured")
            return None
        
        url = f"https://api.1inch.dev/swap/v6.0/{CHAIN_ID}/swap"
        
        params = {
            "src": Web3.to_checksum_address(token_in),
            "dst": Web3.to_checksum_address(token_out),
            "amount": str(amount_in),
            "from": self.account.address if self.account else ZIN_EXECUTOR_ADDRESS,
            "slippage": "0.5",
            "disableEstimate": "true",
            "allowPartialFill": "false",
        }
        
        headers = {
            "Authorization": f"Bearer {ONE_INCH_API_KEY}",
            "Accept": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    url,
                    params=params,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        
                        tx_data = data.get("tx", {})
                        calldata = tx_data.get("data", "")
                        output_amount = int(data.get("dstAmount", 0))
                        gas_estimate = int(tx_data.get("gas", 300000))
                        
                        # Calculate price impact
                        price_impact_bps = 0
                        if "protocols" in data:
                            # 1inch provides price impact in some responses
                            pass
                        
                        if calldata and output_amount > 0:
                            return QuoteResult(
                                aggregator="1inch",
                                calldata=bytes.fromhex(calldata[2:]) if calldata.startswith("0x") else bytes.fromhex(calldata),
                                expected_output=output_amount,
                                gas_estimate=gas_estimate,
                                price_impact_bps=price_impact_bps
                            )
                    
                    elif resp.status == 400:
                        error_data = await resp.json()
                        logger.debug(f"1inch: Bad request - {error_data.get('description', 'Unknown error')}")
                    elif resp.status == 429:
                        logger.warning("1inch: Rate limited")
                    else:
                        logger.debug(f"1inch: API returned status {resp.status}")
                        
            except Exception as e:
                logger.error(f"1inch: Error getting quote: {e}")
        
        return None
    
    async def _get_aerodrome_quote(
        self,
        token_in: str,
        token_out: str,
        amount_in: int
    ) -> Optional[QuoteResult]:
        """
        Get quote from Aerodrome (Base's primary DEX).
        
        Uses on-chain quoting via the router contract.
        """
        try:
            # Aerodrome Router ABI for getAmountsOut
            router_abi = [
                {
                    "inputs": [
                        {"name": "amountIn", "type": "uint256"},
                        {"components": [
                            {"name": "from", "type": "address"},
                            {"name": "to", "type": "address"},
                            {"name": "stable", "type": "bool"},
                            {"name": "factory", "type": "address"}
                        ], "name": "routes", "type": "tuple[]"}
                    ],
                    "name": "getAmountsOut",
                    "outputs": [{"name": "amounts", "type": "uint256[]"}],
                    "stateMutability": "view",
                    "type": "function"
                }
            ]
            
            router = self.w3.eth.contract(
                address=Web3.to_checksum_address(AERODROME_ROUTER),
                abi=router_abi
            )
            
            # Try both stable and volatile pools
            factory = "0x420DD381b31aEf6683db6B902084cB0FFECe40Da"  # Aerodrome factory
            
            for stable in [False, True]:
                try:
                    routes = [(
                        Web3.to_checksum_address(token_in),
                        Web3.to_checksum_address(token_out),
                        stable,
                        Web3.to_checksum_address(factory)
                    )]
                    
                    amounts = router.functions.getAmountsOut(amount_in, routes).call()
                    
                    if len(amounts) >= 2 and amounts[-1] > 0:
                        # Build swap calldata
                        swap_abi = [
                            {
                                "inputs": [
                                    {"name": "amountIn", "type": "uint256"},
                                    {"name": "amountOutMin", "type": "uint256"},
                                    {"components": [
                                        {"name": "from", "type": "address"},
                                        {"name": "to", "type": "address"},
                                        {"name": "stable", "type": "bool"},
                                        {"name": "factory", "type": "address"}
                                    ], "name": "routes", "type": "tuple[]"},
                                    {"name": "to", "type": "address"},
                                    {"name": "deadline", "type": "uint256"}
                                ],
                                "name": "swapExactTokensForTokens",
                                "outputs": [{"name": "amounts", "type": "uint256[]"}],
                                "stateMutability": "nonpayable",
                                "type": "function"
                            }
                        ]
                        
                        swap_router = self.w3.eth.contract(
                            address=Web3.to_checksum_address(AERODROME_ROUTER),
                            abi=swap_abi
                        )
                        
                        min_out = int(amounts[-1] * 0.995)  # 0.5% slippage
                        deadline = int(time.time()) + 300
                        
                        calldata = swap_router.encodeABI(
                            fn_name="swapExactTokensForTokens",
                            args=[
                                amount_in,
                                min_out,
                                routes,
                                ZIN_EXECUTOR_ADDRESS,
                                deadline
                            ]
                        )
                        
                        return QuoteResult(
                            aggregator="Aerodrome",
                            calldata=bytes.fromhex(calldata[2:]),
                            expected_output=amounts[-1],
                            gas_estimate=200000,
                            price_impact_bps=0
                        )
                        
                except Exception as e:
                    logger.debug(f"Aerodrome: No {'stable' if stable else 'volatile'} route: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Aerodrome: Error getting quote: {e}")
        
        return None

    # =========================================================================
    # PROFITABILITY ANALYSIS
    # =========================================================================
    
    def calculate_profit_potential(
        self,
        intent: IntentData,
        quote: QuoteResult
    ) -> Tuple[int, int, bool]:
        """
        Calculate profit potential for fulfilling an intent.
        
        Args:
            intent: The user's intent
            quote: Quote from aggregator
            
        Returns:
            Tuple of (profit_amount, profit_bps, is_profitable)
        """
        # The user wants `amount_out` of token_out
        # We can get `quote.expected_output` from the aggregator
        # Profit = what we get - what we give to user
        
        user_wants = intent.amount_out
        we_can_get = quote.expected_output
        
        if we_can_get <= user_wants:
            # No profit - we can't get more than user wants
            return (0, 0, False)
        
        profit_amount = we_can_get - user_wants
        profit_bps = (profit_amount * 10000) // user_wants if user_wants > 0 else 0
        
        # Estimate gas cost in token terms
        gas_price = self.w3.eth.gas_price
        gas_cost_wei = gas_price * quote.gas_estimate
        
        # Check if profit exceeds minimum threshold
        min_profit_bps = max(ZIN_MIN_PROFIT_BPS, 0)
        is_profitable = profit_bps >= min_profit_bps
        
        return (profit_amount, profit_bps, is_profitable)
    
    async def check_vault_liquidity(self, token: str) -> int:
        """Check available liquidity in the ZIN pool for a token."""
        try:
            liquidity = self.zin_pool.functions.maxFlashLoan(
                Web3.to_checksum_address(token)
            ).call()
            return liquidity
        except Exception as e:
            logger.error(f"Error checking vault liquidity: {e}")
            return 0

    # =========================================================================
    # AUTO-SCALING POSITION SIZING
    # =========================================================================
    
    async def _get_cached_liquidity(self, token: str) -> int:
        """Get liquidity with caching to reduce RPC calls."""
        token_key = token.lower()
        now = time.time()
        
        # Check cache
        if token_key in self._liquidity_cache:
            cached_liq, cached_time = self._liquidity_cache[token_key]
            if now - cached_time < self._liquidity_cache_ttl:
                return cached_liq
        
        # Fetch fresh liquidity
        liquidity = await self.check_vault_liquidity(token)
        self._liquidity_cache[token_key] = (liquidity, now)
        return liquidity
    
    def _calculate_scaled_position(
        self,
        intent: IntentData,
        pool_liquidity: int
    ) -> Tuple[int, str]:
        """
        Calculate dynamically scaled position size based on pool liquidity.
        
        Auto-scaling rules:
        1. Never use more than max_liquidity_ratio (50%) of pool
        2. Never use less than min_liquidity_ratio (10%) of pool
        3. Scale based on intent profitability and pool depth
        4. Apply scale_factor multiplier for aggressive/conservative modes
        
        Returns:
            Tuple of (scaled_amount, scaling_reason)
        """
        if not self._auto_scale_enabled:
            return (intent.amount_out, "auto_scale_disabled")
        
        if pool_liquidity == 0:
            return (0, "no_liquidity")
        
        # Calculate liquidity bounds
        min_position = int(pool_liquidity * self._min_liquidity_ratio)
        max_position = int(pool_liquidity * self._max_liquidity_ratio)
        
        # Start with the intent's requested amount
        requested = intent.amount_out
        
        # Apply scale factor
        scaled = int(requested * self._scale_factor_base)
        
        # Clamp to liquidity bounds
        if scaled > max_position:
            return (max_position, f"clamped_to_max_{self._max_liquidity_ratio*100:.0f}%")
        
        if scaled < min_position and requested >= min_position:
            # Intent is large enough but scaling reduced it too much
            return (min_position, f"floor_at_min_{self._min_liquidity_ratio*100:.0f}%")
        
        if scaled < min_position:
            # Intent itself is smaller than minimum - allow it if profitable
            return (scaled, "below_min_but_allowed")
        
        return (scaled, "scaled_normally")
    
    async def get_auto_scaled_intent_cap(self, intent: IntentData) -> Tuple[int, str]:
        """
        Get the auto-scaled maximum intent amount for a token.
        
        This combines:
        1. Static per-token caps from env
        2. Dynamic scaling based on current pool liquidity
        3. Global max intent amount
        
        Returns:
            Tuple of (max_amount, reason)
        """
        # Get pool liquidity
        pool_liquidity = await self._get_cached_liquidity(intent.token_out)
        
        # Calculate scaled position
        scaled_amount, scale_reason = self._calculate_scaled_position(intent, pool_liquidity)
        
        # Apply static caps
        static_cap = self._get_intent_cap(intent)
        
        if static_cap > 0 and scaled_amount > static_cap:
            return (static_cap, f"static_cap_applied")
        
        return (scaled_amount, scale_reason)

    # =========================================================================
    # INTENT FULFILLMENT
    # =========================================================================
    
    async def fulfill_intent(
        self,
        intent: IntentData,
        quote: QuoteResult
    ) -> FulfillmentResult:
        """
        Fulfill a user intent using Kerne's internal liquidity.
        
        Flow:
        1. Flash loan tokenOut from ZIN Pool (zero fee for SOLVER_ROLE)
        2. Send tokenOut to user
        3. Execute aggregator swap (tokenIn -> tokenOut)
        4. Repay flash loan
        5. Keep spread as profit
        """
        if not self.live_mode:
            logger.warning(f"[DRY RUN] Would fulfill intent {intent.order_id[:16]}...")
            logger.info(f"  Venue: {intent.venue.value}")
            logger.info(f"  User: {intent.user[:16]}...")
            logger.info(f"  Swap: {intent.token_in_symbol} -> {intent.token_out_symbol}")
            logger.info(f"  Amount: {intent.amount_out}")
            logger.info(f"  Aggregator: {quote.aggregator}")
            
            self._log_trade(intent, 0, 0, "DRY_RUN", "dry_run")
            return FulfillmentResult(
                success=True,
                tx_hash=None,
                profit_captured=0,
                profit_bps=0,
                gas_used=0
            )
        
        try:
            # Prepare safety parameters for Sentinel V2
            safety_params = encode(
                ["uint256", "uint256", "uint256"],
                [
                    intent.deadline,
                    intent.price_limit,
                    5  # Minimum profit in bps
                ]
            )
            
            # Build the fulfillIntent transaction
            tx = self.zin_executor.functions.fulfillIntent(
                Web3.to_checksum_address(ZIN_POOL_ADDRESS),  # lender
                Web3.to_checksum_address(intent.token_in),
                Web3.to_checksum_address(intent.token_out),
                intent.amount_out,
                Web3.to_checksum_address(intent.user),
                quote.calldata,
                safety_params
            ).build_transaction({
                "from": self.account.address,
                "nonce": self.w3.eth.get_transaction_count(self.account.address),
                "gas": quote.gas_estimate + 200000,  # Add buffer for flash loan overhead
                "gasPrice": self.w3.eth.gas_price,
                "chainId": CHAIN_ID
            })
            
            # Sign and send
            signed_tx = self.w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            
            logger.info(f"Intent fulfillment submitted: {tx_hash.hex()}")
            
            # Wait for confirmation
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
            
            if receipt.status == 1:
                # Calculate actual profit from logs
                profit_captured, profit_bps = self._parse_profit_from_receipt(receipt)
                
                logger.success(f"Intent fulfilled successfully!")
                logger.info(f"  TX: {tx_hash.hex()}")
                logger.info(f"  Gas Used: {receipt.gasUsed}")
                logger.info(f"  Profit: {profit_bps} bps")
                
                self.total_intents_processed += 1
                self.total_profit_captured += profit_captured
                self.intents_by_venue[intent.venue.value] += 1
                
                self._log_trade(intent, profit_bps, receipt.gasUsed, tx_hash.hex(), "SUCCESS")
                await self._send_discord_alert(intent, profit_bps, tx_hash.hex())
                
                return FulfillmentResult(
                    success=True,
                    tx_hash=tx_hash.hex(),
                    profit_captured=profit_captured,
                    profit_bps=profit_bps,
                    gas_used=receipt.gasUsed
                )
            else:
                logger.error(f"Transaction failed: {tx_hash.hex()}")
                self.failed_intents += 1
                self._log_trade(intent, 0, receipt.gasUsed, tx_hash.hex(), "FAILED")
                
                return FulfillmentResult(
                    success=False,
                    tx_hash=tx_hash.hex(),
                    profit_captured=0,
                    profit_bps=0,
                    gas_used=receipt.gasUsed,
                    error="Transaction reverted"
                )
                
        except Exception as e:
            logger.error(f"Error fulfilling intent: {e}")
            self.failed_intents += 1
            self._log_trade(intent, 0, 0, "", f"ERROR: {str(e)[:50]}")
            
            return FulfillmentResult(
                success=False,
                tx_hash=None,
                profit_captured=0,
                profit_bps=0,
                gas_used=0,
                error=str(e)
            )
    
    def _parse_profit_from_receipt(self, receipt) -> Tuple[int, int]:
        """Parse profit from transaction receipt logs."""
        try:
            # Look for IntentFulfilled event
            # Event signature: IntentFulfilled(address,address,address,uint256,uint256,uint256)
            intent_fulfilled_topic = self.w3.keccak(
                text="IntentFulfilled(address,address,address,uint256,uint256,uint256)"
            )
            
            for log in receipt.logs:
                if log.topics and log.topics[0] == intent_fulfilled_topic:
                    # Decode the log data
                    # spreadCaptured is the 5th parameter (index 4)
                    data = log.data
                    if len(data) >= 128:  # 4 * 32 bytes
                        spread_captured = int.from_bytes(data[64:96], 'big')
                        amount_out = int.from_bytes(data[32:64], 'big')
                        
                        profit_bps = (spread_captured * 10000) // amount_out if amount_out > 0 else 0
                        return (spread_captured, profit_bps)
                        
        except Exception as e:
            logger.debug(f"Could not parse profit from receipt: {e}")
        
        return (0, 0)
    
    def _log_trade(
        self,
        intent: IntentData,
        profit_bps: int,
        gas_used: int,
        tx_hash: str,
        status: str
    ):
        """Log trade to CSV file."""
        timestamp = int(time.time())
        line = (
            f"{timestamp},{intent.venue.value},{intent.order_id[:32]},"
            f"{intent.token_in[:16]},{intent.token_out[:16]},"
            f"{intent.amount_out},{profit_bps},{gas_used},{tx_hash},{status}\n"
        )
        
        try:
            with open(self.profit_log_path, "a") as f:
                f.write(line)
        except Exception as e:
            logger.error(f"Error writing to profit log: {e}")
    
    async def _send_discord_alert(
        self,
        intent: IntentData,
        profit_bps: int,
        tx_hash: str
    ):
        """Send Discord alert for successful fulfillment."""
        if not DISCORD_WEBHOOK_URL:
            return
        
        try:
            embed = {
                "title": "🎯 ZIN Intent Fulfilled!",
                "color": 0x00ff00,
                "fields": [
                    {"name": "Venue", "value": intent.venue.value, "inline": True},
                    {"name": "Profit", "value": f"{profit_bps} bps", "inline": True},
                    {"name": "Pair", "value": f"{intent.token_in_symbol} → {intent.token_out_symbol}", "inline": True},
                    {"name": "TX", "value": f"[View on BaseScan](https://basescan.org/tx/{tx_hash})", "inline": False}
                ],
                "footer": {"text": "Filled by Kerne ZIN"}
            }
            
            payload = {"embeds": [embed]}
            
            async with aiohttp.ClientSession() as session:
                await session.post(DISCORD_WEBHOOK_URL, json=payload)
                
        except Exception as e:
            logger.debug(f"Failed to send Discord alert: {e}")

    # =========================================================================
    # METRICS & MONITORING
    # =========================================================================
    
    async def get_zin_metrics(self) -> Dict[str, Any]:
        """
        Get ZIN performance metrics from the executor contract and local stats.
        """
        try:
            # On-chain metrics
            metrics = self.zin_executor.functions.getZINMetrics().call()
            
            # Get token-specific spreads
            token_spreads = {}
            for token_addr, token_name in LST_TARGETS.items():
                try:
                    spread = self.zin_executor.functions.getTokenSpread(
                        Web3.to_checksum_address(token_addr)
                    ).call()
                    if spread > 0:
                        token_spreads[token_name] = spread
                except:
                    pass
            
            return {
                "on_chain": {
                    "total_spread_captured": metrics[0],
                    "total_intents_fulfilled": metrics[1],
                    "profit_vault": metrics[2],
                    "token_spreads": token_spreads
                },
                "bot_stats": {
                    "intents_processed": self.total_intents_processed,
                    "profit_captured": self.total_profit_captured,
                    "failed_intents": self.failed_intents,
                    "intents_by_venue": self.intents_by_venue,
                    "success_rate": (
                        self.total_intents_processed / 
                        (self.total_intents_processed + self.failed_intents) * 100
                        if (self.total_intents_processed + self.failed_intents) > 0 
                        else 0
                    )
                },
                "config": {
                    "live_mode": self.live_mode,
                    "active_chain": self.active_chain,
                    "executor_address": ZIN_EXECUTOR_ADDRESS,
                    "pool_address": ZIN_POOL_ADDRESS
                }
            }
        except Exception as e:
            logger.error(f"Error fetching ZIN metrics: {e}")
            return {
                "error": str(e),
                "bot_stats": {
                    "intents_processed": self.total_intents_processed,
                    "profit_captured": self.total_profit_captured,
                    "failed_intents": self.failed_intents
                }
            }
    
    async def log_metrics(self):
        """Log current metrics to console."""
        metrics = await self.get_zin_metrics()
        
        logger.info("=" * 40)
        logger.info("ZIN Solver Metrics")
        logger.info("=" * 40)
        
        if "on_chain" in metrics:
            on_chain = metrics["on_chain"]
            logger.info(f"On-Chain Total Spread: {on_chain['total_spread_captured']}")
            logger.info(f"On-Chain Total Intents: {on_chain['total_intents_fulfilled']}")
        
        bot_stats = metrics.get("bot_stats", {})
        logger.info(f"Bot Intents Processed: {bot_stats.get('intents_processed', 0)}")
        logger.info(f"Bot Profit Captured: {bot_stats.get('profit_captured', 0)}")
        logger.info(f"Failed Intents: {bot_stats.get('failed_intents', 0)}")
        logger.info(f"Success Rate: {bot_stats.get('success_rate', 0):.1f}%")
        logger.info(f"By Venue: {bot_stats.get('intents_by_venue', {})}")
        logger.info("=" * 40)

    # =========================================================================
    # MAIN LOOP
    # =========================================================================
    
    async def process_intent(self, intent: IntentData) -> bool:
        """
        Process a single intent: check profitability and fulfill if profitable.
        
        Returns True if intent was fulfilled successfully.
        """
        try:
            logger.info(f"Processing intent from {intent.venue.value}: {intent.order_id[:16]}...")

            if not self._is_gas_price_ok():
                return False

            if intent.deadline - int(time.time()) < ZIN_MIN_ORDER_TTL_SECONDS:
                logger.debug("Order TTL below guardrail")
                return False

            # Use auto-scaling to determine max intent amount
            scaled_cap, scale_reason = await self.get_auto_scaled_intent_cap(intent)
            if scaled_cap == 0:
                logger.debug(f"Auto-scale rejected: {scale_reason}")
                return False
            
            if intent.amount_out > scaled_cap:
                logger.debug(
                    f"Intent amount above auto-scaled cap: {intent.amount_out} > {scaled_cap} ({scale_reason})"
                )
                return False
            
            logger.debug(f"Auto-scale: cap={scaled_cap}, reason={scale_reason}")
            
            # 1. Check vault liquidity (already cached by auto-scaling)
            liquidity = await self._get_cached_liquidity(intent.token_out)
            if liquidity < intent.amount_out:
                logger.debug(f"Insufficient liquidity: {liquidity} < {intent.amount_out}")
                return False
            
            # 2. Get best quote from aggregators
            quote = await self.get_best_quote(
                intent.token_in,
                intent.token_out,
                intent.amount_in
            )
            
            if not quote:
                logger.debug("No quote available")
                return False

            if quote.price_impact_bps > ZIN_MAX_PRICE_IMPACT_BPS:
                logger.debug(
                    f"Price impact too high: {quote.price_impact_bps} bps"
                )
                return False
            
            # 3. Calculate profitability
            profit_amount, profit_bps, is_profitable = self.calculate_profit_potential(
                intent, quote
            )
            
            if profit_bps < ZIN_MIN_PROFIT_BPS:
                logger.debug(f"Profit below guardrail: {profit_bps} bps")
                return False
            
            if not is_profitable:
                logger.debug(f"Not profitable: {profit_bps} bps")
                return False
            
            logger.info(f"Profitable intent found! Expected profit: {profit_bps} bps")
            
            # 4. Fulfill the intent
            result = await self.fulfill_intent(intent, quote)
            
            return result.success
            
        except Exception as e:
            logger.error(f"Error processing intent: {e}")
            return False
    
    async def run_cycle(self) -> int:
        """
        Run one cycle of intent fetching and processing.
        
        Returns number of intents processed.
        """
        processed = 0
        
        # Fetch intents from all venues
        cowswap_intents = await self.fetch_cowswap_orders()
        uniswapx_intents = await self.fetch_uniswapx_orders()
        
        all_intents = cowswap_intents + uniswapx_intents
        if ZIN_MAX_INTENTS_PER_CYCLE > 0:
            all_intents = all_intents[:ZIN_MAX_INTENTS_PER_CYCLE]
        
        if all_intents:
            logger.info(f"Found {len(all_intents)} potential intents "
                       f"(CowSwap: {len(cowswap_intents)}, UniswapX: {len(uniswapx_intents)})")
        
        # Process each intent
        for intent in all_intents:
            success = await self.process_intent(intent)
            if success:
                processed += 1
        
        return processed
    
    async def run(self, interval: float = 5.0):
        """
        Main solver loop.
        
        Args:
            interval: Seconds between cycles
        """
        logger.info("Starting ZIN Solver main loop...")
        logger.info(f"Monitoring CowSwap and UniswapX for profitable intents")
        logger.info(f"Cycle interval: {interval}s")
        
        cycle_count = 0
        metrics_interval = 60  # Log metrics every 60 seconds
        last_metrics_log = time.time()
        
        while True:
            try:
                cycle_count += 1
                
                # Run one cycle
                processed = await self.run_cycle()
                
                if processed > 0:
                    logger.success(f"Cycle {cycle_count}: Processed {processed} intents")
                
                # Log metrics periodically
                if time.time() - last_metrics_log >= metrics_interval:
                    await self.log_metrics()
                    last_metrics_log = time.time()
                
                # Sleep before next cycle
                await asyncio.sleep(interval)
                
            except KeyboardInterrupt:
                logger.info("Shutting down ZIN Solver...")
                break
            except Exception as e:
                logger.error(f"Error in solver loop: {e}")
                await asyncio.sleep(interval * 2)  # Back off on error


# =============================================================================
# CLI ENTRY POINT
# =============================================================================

async def main():
    """Main entry point for the ZIN Solver."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Kerne ZIN Solver - Intent Execution Engine")
    parser.add_argument(
        "--interval",
        type=float,
        default=5.0,
        help="Seconds between cycles (default: 5.0)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run in dry-run mode (no actual transactions)"
    )
    parser.add_argument(
        "--metrics-only",
        action="store_true",
        help="Just print current metrics and exit"
    )
    
    args = parser.parse_args()
    
    # Override live mode if dry-run flag is set
    if args.dry_run:
        os.environ["ZIN_SOLVER_LIVE"] = "false"
    
    try:
        solver = ZINSolver()
        
        if args.metrics_only:
            await solver.log_metrics()
            return
        
        await solver.run(interval=args.interval)
        
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        logger.info("Please check your .env file and ensure all required variables are set.")
        raise SystemExit(1)
    except ConnectionError as e:
        logger.error(f"Connection error: {e}")
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
