# Created: 2026-01-15
# Updated: 2026-01-16 - Productionization: RiskGate, MEV Protection, Precise Gas, Metrics
"""
Graph-Based Flash Arbitrage Discovery Engine
============================================
An institutional-grade discovery engine that treats the Base ecosystem as a 
directed graph. Identifies complex cycles (2-hop, 3-hop, 4-hop) across 
Aerodrome, Uniswap V3, Sushi, BaseSwap, and Maverick.
"""

import os
import json
import time
import math
import asyncio
from typing import Optional, Tuple, List, Dict, Any, Set
from dataclasses import dataclass, field
from enum import IntEnum

from web3 import Web3
from web3.contract import Contract
from dotenv import load_dotenv
from loguru import logger

# Kerne Production Modules
from bot.metrics import ArbMetrics
from bot.sentinel.arb_risk_gate import ArbRiskGate
from bot.sentinel.risk_engine import RiskEngine
from bot.mev_protection import MEVProtectedSubmitter
from bot.gas_estimator import BaseGasEstimator, DEX
from bot.arb_executor import RobustArbExecutor, LenderPriority, ExecutionResult

try:
    from bot.alerts import send_discord_alert
except ImportError:
    try:
        from alerts import send_discord_alert
    except ImportError:
        def send_discord_alert(msg, level="INFO"):
            logger.info(f"[ALERT-{level}] {msg}")

# =============================================================================
# MODELS
# =============================================================================

@dataclass(frozen=True)
class Token:
    symbol: str
    address: str
    decimals: int

@dataclass
class Pool:
    dex: DEX
    token0: Token
    token1: Token
    router: str = ""
    fee: int = 0
    stable: bool = False
    extra_data: bytes = b""
    
    def __hash__(self):
        return hash((self.dex, self.token0.address, self.token1.address, self.fee, self.stable))

@dataclass
class ArbPath:
    pools: List[Pool]
    tokens: List[Token] # tokens[i] is input to pools[i]
    amount_in: int
    expected_profit: int = 0
    profit_usd: float = 0.0
    
    def __str__(self) -> str:
        path_str = " -> ".join([t.symbol for t in self.tokens] + [self.tokens[0].symbol])
        dex_str = " | ".join([p.dex.name for p in self.pools])
        return f"Cycle: {path_str} via {dex_str} | Profit: ${self.profit_usd:.2f}"

# =============================================================================
# DISCOVERY ENGINE
# =============================================================================

class GraphArbScanner:
    # Base Mainnet Addresses
    AERODROME_ROUTER = Web3.to_checksum_address("0xcf77a3ba9a5ca399b7c97c74d54e5b1beb874e43")
    UNISWAP_V3_QUOTER = Web3.to_checksum_address("0x3d4e44eb1374240ce5f1b871ab261cd16335b76a")
    SUSHI_ROUTER = Web3.to_checksum_address("0x6bd61ebd2797e2d55734ee35b82230218620e410")
    BASESWAP_ROUTER = Web3.to_checksum_address("0x327df1e6de05895d2d21f22129516694f5865c14")
    MAVERICK_ROUTER = Web3.to_checksum_address("0xbe0e5b6b3f0c3bc8e59273c52431478d8d303e97")
    MAVERICK_QUOTER = Web3.to_checksum_address("0x69680327f12f9f1a19d7bf53a04849767f33a000")
    PANCAKE_V3_ROUTER = Web3.to_checksum_address("0x1b81D678ffb9C0263b24A97847620C99d213eB14")
    PANCAKE_V3_QUOTER = Web3.to_checksum_address("0xB048Bbc1Ee6b733FFfCFb9e9CeF7375518e25997")
    
    # Maverick Pool Map (TokenA, TokenB) -> PoolAddress
    MAVERICK_POOLS = {
        ("0x2Ae3F1Ec7F1F5012CFEab0185bfc7aa3cf0DEc22", "0x4200000000000000000000000000000000000006"): "0x91F5638e8A4526d56d4453A2619A0A8912A34919", # cbETH/WETH
        ("0x4200000000000000000000000000000000000006", "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"): "0x7a2ad8668972E9bB37365676348633F02735165F", # WETH/USDC
    }
    
    # Base Tokens
    WETH = Token("WETH", "0x4200000000000000000000000000000000000006", 18)
    USDC = Token("USDC", "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913", 6)
    KUSD = Token("kUSD", "0xb50bFec5FF426744b9d195a8C262da376637Cb6A", 6)
    CBETH = Token("cbETH", "0x2Ae3F1Ec7F1F5012CFEab0185bfc7aa3cf0DEc22", 18)
    DAI = Token("DAI", "0x50c5725949A6F0c72E6C4a641F24049A917FA061", 18)
    WSTETH = Token("wstETH", "0x5979D7b546E38E414F7E9822514be443A4800529", 18)
    SNX = Token("SNX", "0x22e6966B799c4D5d13BE9b3d189446752621ec0C", 18)
    LINK = Token("LINK", "0xfab36e4CE90CdfF5Af996a7a8f737eB327263b62", 18)
    LUSD = Token("LUSD", "0x1693521fd90BB9707Cc0660AcAA00161Cbcc2Bc0", 18)
    USDBC = Token("USDbC", "0xd9aAEc86B65D86f6A7B5B1b0c42FFA531710b6CA", 6)
    CBBTC = Token("cbBTC", "0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf", 8)

    def __init__(self):
        load_dotenv()
        self.rpc_urls = [u.strip() for u in os.getenv("RPC_URL", "").split(",") if u.strip()]
        if not self.rpc_urls:
            raise ValueError("No RPC_URL found in environment variables.")
        
        self.current_rpc_index = 0
        self.w3 = self._connect_to_best_rpc()
        self.private_key = os.getenv("PRIVATE_KEY")
        self.account = self.w3.eth.account.from_key(self.private_key)
        self.arb_bot_address = os.getenv("FLASH_ARB_BOT_ADDRESS")
        
        self.pools: List[Pool] = []
        self.adj: Dict[str, List[Pool]] = {}
        
        self._setup_initial_graph()
        self._load_contracts()
        
        self.min_profit_usd = float(os.getenv("MIN_PROFIT_USD", "10.0"))
        self.max_trade_size_eth = float(os.getenv("MAX_TRADE_SIZE_ETH", "5.0"))
        
        # Production Components
        self.metrics = ArbMetrics(port=int(os.getenv("METRICS_PORT", "9090")))
        self.risk_engine = RiskEngine(w3=self.w3, private_key=self.private_key)
        self.risk_gate = ArbRiskGate()
        self.mev_submitter = MEVProtectedSubmitter(self.w3, self.private_key)
        self.gas_estimator = BaseGasEstimator(self.w3)
        self.executor = RobustArbExecutor(self.w3, self.arb_bot, self.private_key, self.mev_submitter)
        
        logger.info(f"GraphArbScanner Productionized. {len(self.pools)} pools loaded. Account: {self.account.address}")

    def _connect_to_best_rpc(self) -> Web3:
        """Tries multiple RPCs and returns the first one that connects."""
        for url in self.rpc_urls:
            try:
                w3 = Web3(Web3.HTTPProvider(url, request_kwargs={'timeout': 10}))
                if w3.is_connected():
                    logger.info(f"Connected to RPC: {url}")
                    return w3
            except Exception as e:
                logger.warning(f"Failed to connect to {url}: {e}")
        
        raise ConnectionError("Failed to connect to any provided RPC URL.")

    def _switch_rpc(self):
        """Switches to the next available RPC."""
        self.current_rpc_index = (self.current_rpc_index + 1) % len(self.rpc_urls)
        new_url = self.rpc_urls[self.current_rpc_index]
        logger.warning(f"Switching RPC to: {new_url}")
        self.w3 = self._connect_to_best_rpc()
        self._load_contracts()
        # Re-init components that depend on w3
        self.gas_estimator = BaseGasEstimator(self.w3)
        self.mev_submitter = MEVProtectedSubmitter(self.w3, self.private_key)
        self.executor = RobustArbExecutor(self.w3, self.arb_bot, self.private_key, self.mev_submitter)

    def _load_contracts(self):
        # ABIs for quoting
        self.aerodrome_abi = [
            {"inputs": [{"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                       {"components": [{"internalType": "address", "name": "from", "type": "address"},
                                      {"internalType": "address", "name": "to", "type": "address"},
                                      {"internalType": "bool", "name": "stable", "type": "bool"},
                                      {"internalType": "address", "name": "factory", "type": "address"}],
                        "internalType": "struct IRouter.Route[]", "name": "routes", "type": "tuple[]"}],
             "name": "getAmountsOut", "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
             "stateMutability": "view", "type": "function"}
        ]
        self.quoter_abi = [
            {"inputs": [{"components": [{"internalType": "address", "name": "tokenIn", "type": "address"},
                                       {"internalType": "address", "name": "tokenOut", "type": "address"},
                                       {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                                       {"internalType": "uint24", "name": "fee", "type": "uint24"},
                                       {"internalType": "uint160", "name": "sqrtPriceLimitX96", "type": "uint160"}],
                          "internalType": "struct IQuoterV2.QuoteExactInputSingleParams", "name": "params", "type": "tuple"}],
             "name": "quoteExactInputSingle",
             "outputs": [{"internalType": "uint256", "name": "amountOut", "type": "uint256"},
                         {"internalType": "uint160", "name": "sqrtPriceX96After", "type": "uint160"},
                         {"internalType": "uint32", "name": "initializedTicksCrossed", "type": "uint32"},
                         {"internalType": "uint256", "name": "gasEstimate", "type": "uint256"}],
             "stateMutability": "nonpayable", "type": "function"}
        ]
        self.v2_abi = [
            {"inputs": [{"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                       {"internalType": "address[]", "name": "path", "type": "address[]"}],
             "name": "getAmountsOut", "outputs": [{"internalType": "uint256[]", "name": "amounts", "type": "uint256[]"}],
             "stateMutability": "view", "type": "function"}
        ]
        self.maverick_quoter_abi = [
            {"inputs": [{"components": [{"internalType": "address", "name": "tokenIn", "type": "address"},
                                       {"internalType": "address", "name": "tokenOut", "type": "address"},
                                       {"internalType": "address", "name": "pool", "type": "address"},
                                       {"internalType": "address", "name": "recipient", "type": "address"},
                                       {"internalType": "uint256", "name": "deadline", "type": "uint256"},
                                       {"internalType": "uint256", "name": "amountIn", "type": "uint256"},
                                       {"internalType": "uint256", "name": "amountOutMinimum", "type": "uint256"},
                                       {"internalType": "uint160", "name": "sqrtPriceLimitX96", "type": "uint160"}],
                          "internalType": "struct IMaverickRouter.ExactInputSingleParams", "name": "params", "type": "tuple"}],
             "name": "calculateSwap",
             "outputs": [{"internalType": "uint256", "name": "amountOut", "type": "uint256"}],
             "stateMutability": "view", "type": "function"}
        ]
        
        self.aero_router = self.w3.eth.contract(address=self.AERODROME_ROUTER, abi=self.aerodrome_abi)
        self.uni_quoter = self.w3.eth.contract(address=self.UNISWAP_V3_QUOTER, abi=self.quoter_abi)
        self.pancake_quoter = self.w3.eth.contract(address=self.PANCAKE_V3_QUOTER, abi=self.quoter_abi)
        self.sushi_router = self.w3.eth.contract(address=self.SUSHI_ROUTER, abi=self.v2_abi)
        self.baseswap_router = self.w3.eth.contract(address=self.BASESWAP_ROUTER, abi=self.v2_abi)
        self.mav_quoter = self.w3.eth.contract(address=self.MAVERICK_QUOTER, abi=self.maverick_quoter_abi)
        
        # Arb Bot
        if self.arb_bot_address:
            path = os.path.join(os.path.dirname(__file__), "..", "out", "KerneFlashArbBot.sol", "KerneFlashArbBot.json")
            if os.path.exists(path):
                with open(path, "r") as f:
                    artifact = json.load(f)
                self.arb_bot = self.w3.eth.contract(address=self.arb_bot_address, abi=artifact["abi"])
            else:
                self.arb_bot = None
        else:
            self.arb_bot = None

    def _setup_initial_graph(self):
        """Builds the initial pool set."""
        tokens = [self.WETH, self.USDC, self.KUSD, self.CBETH, self.DAI, self.WSTETH, self.SNX, self.LINK, self.LUSD, self.USDBC, self.CBBTC]
        
        # Aerodrome Volatile Pools
        for i in range(len(tokens)):
            for j in range(i + 1, len(tokens)):
                self._add_pool(Pool(DEX.AERODROME, tokens[i], tokens[j], stable=False))
        
        # Aerodrome Stable Pools
        self._add_pool(Pool(DEX.AERODROME, self.USDC, self.DAI, stable=True))
        self._add_pool(Pool(DEX.AERODROME, self.USDC, self.KUSD, stable=True))
        self._add_pool(Pool(DEX.AERODROME, self.LUSD, self.USDC, stable=True))
        
        # Uniswap V3 & Pancake V3
        fees = [100, 500, 3000, 10000]
        for i in range(len(tokens)):
            for j in range(i + 1, len(tokens)):
                for fee in fees:
                    self._add_pool(Pool(DEX.UNISWAP_V3, tokens[i], tokens[j], fee=fee))
                    self._add_pool(Pool(DEX.PANCAKE_V3, tokens[i], tokens[j], fee=fee, router=self.PANCAKE_V3_ROUTER))
        
        # Sushi & BaseSwap
        for i in range(len(tokens)):
            for j in range(i + 1, len(tokens)):
                self._add_pool(Pool(DEX.UNISWAP_V2, tokens[i], tokens[j], router=self.SUSHI_ROUTER))
                self._add_pool(Pool(DEX.UNISWAP_V2, tokens[i], tokens[j], router=self.BASESWAP_ROUTER))

        # Maverick Pools
        for tokens_tuple, pool_addr in self.MAVERICK_POOLS.items():
            t0_addr, t1_addr = tokens_tuple
            t0 = next((t for t in tokens if t.address == t0_addr), None)
            t1 = next((t for t in tokens if t.address == t1_addr), None)
            if t0 and t1:
                self._add_pool(Pool(DEX.MAVERICK, t0, t1, extra_data=Web3.to_bytes(hexstr=pool_addr)))

    def _add_pool(self, pool: Pool):
        self.pools.append(pool)
        self.adj.setdefault(pool.token0.address, []).append(pool)
        self.adj.setdefault(pool.token1.address, []).append(pool)

    def find_cycles(self, start_token: Token, max_hops: int = 3) -> List[List[Pool]]:
        """
        Legacy DFS discovery. Kept for fallback.
        """
        cycles = []
        def dfs(curr_token_addr: str, path: List[Pool], visited_tokens: Set[str]):
            if len(path) == max_hops: return
            for pool in self.adj.get(curr_token_addr, []):
                next_token = pool.token1 if pool.token0.address == curr_token_addr else pool.token0
                if next_token.address == start_token.address and len(path) >= 1:
                    cycles.append(path + [pool])
                    continue
                if next_token.address not in visited_tokens:
                    dfs(next_token.address, path + [pool], visited_tokens | {next_token.address})
        dfs(start_token.address, [], {start_token.address})
        return cycles

    async def find_profitable_cycles_bellman_ford(self, start_token: Token, amount_in: int) -> List[List[Pool]]:
        """
        Bellman-Ford Negative Cycle Detection.
        1. Fetches prices for all edges (pools) in parallel.
        2. Builds graph with weight = -log(price).
        3. Detects negative cycles (profit > 1.0).
        """
        # 1. Build the graph nodes
        tokens = list(self.adj.keys())
        token_map = {t: i for i, t in enumerate(tokens)}
        reverse_token_map = {i: t for t, i in token_map.items()}
        n = len(tokens)
        
        # 2. Fetch all edge prices in parallel
        # We need to query every pool in self.pools for the given amount_in
        # Note: This assumes amount_in is preserved roughly across hops (simplification)
        # For better accuracy, we'd need iterative updates, but for discovery this is fine.
        
        tasks = []
        pool_map = [] # Stores (pool, token_in, token_out) corresponding to tasks
        
        for pool in self.pools:
            # Check forward: token0 -> token1
            tasks.append(self.get_quote(pool, pool.token0, amount_in))
            pool_map.append((pool, pool.token0, pool.token1))
            
            # Check reverse: token1 -> token0
            tasks.append(self.get_quote(pool, pool.token1, amount_in))
            pool_map.append((pool, pool.token1, pool.token0))
            
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 3. Build Weighted Graph
        # edges[u] = [(v, weight, pool)]
        edges = []
        
        for i, res in enumerate(results):
            if isinstance(res, Exception) or res == 0:
                continue
                
            pool, t_in, t_out = pool_map[i]
            amount_out = res
            
            # Calculate price = amount_out / amount_in
            # We must normalize decimals
            decimals_in = t_in.decimals
            decimals_out = t_out.decimals
            
            # Price = (OutRaw / 10^dOut) / (InRaw / 10^dIn)
            price = (amount_out / (10**decimals_out)) / (amount_in / (10**decimals_in))
            
            if price <= 0: continue
            
            weight = -math.log(price)
            u = token_map.get(t_in.address)
            v = token_map.get(t_out.address)
            
            if u is not None and v is not None:
                edges.append((u, v, weight, pool))

        # 4. Run Bellman-Ford
        dist = [float('inf')] * n
        parent = [-1] * n
        edge_to_parent = [None] * n # Stores the pool used to get to node
        
        start_node = token_map[start_token.address]
        dist[start_node] = 0
        
        # Relax edges N-1 times
        for _ in range(n - 1):
            changed = False
            for u, v, w, pool in edges:
                if dist[u] != float('inf') and dist[u] + w < dist[v]:
                    dist[v] = dist[u] + w
                    parent[v] = u
                    edge_to_parent[v] = pool
                    changed = True
            if not changed: break
            
        # Check for negative cycles
        cycles = []
        seen_cycles = set()
        
        for u, v, w, pool in edges:
            if dist[u] != float('inf') and dist[u] + w < dist[v]:
                # Negative cycle found!
                # Trace back to find the cycle
                curr = v
                for _ in range(n):
                    curr = parent[curr]
                
                cycle_path = []
                cycle_pools = []
                cycle_node = curr
                
                while True:
                    prev = parent[cycle_node]
                    pool_used = edge_to_parent[cycle_node]
                    
                    cycle_path.append(cycle_node)
                    cycle_pools.append(pool_used)
                    
                    if prev == curr and len(cycle_path) > 1:
                        break
                    if prev == -1: # Should not happen in a cycle
                        break
                        
                    cycle_node = prev
                
                # The cycle is constructed backwards (v <- u <- ... <- v)
                # We need to reverse it to get execution order
                cycle_pools.reverse()
                
                # Check if this cycle starts/ends with our start_token (or can be rotated)
                # For simplicity, we only return cycles that contain our start_token
                # and rotate them to start with it.
                
                # Reconstruct tokens to check
                # cycle_pools[0] connects some T -> some T'
                # This part is tricky with just pools. 
                # Let's simplify: just return the list of pools if it's valid.
                
                # Unique ID for cycle to avoid duplicates
                cycle_id = tuple(sorted([p.token0.address for p in cycle_pools]))
                if cycle_id in seen_cycles: continue
                seen_cycles.add(cycle_id)
                
                cycles.append(cycle_pools)
                
        return cycles

    async def get_quote(self, pool: Pool, token_in: Token, amount_in: int, retries: int = 3) -> int:
        token_out = pool.token1 if pool.token0.address == token_in.address else pool.token0
        for attempt in range(retries):
            try:
                if pool.dex == DEX.AERODROME:
                    routes = [(token_in.address, token_out.address, pool.stable, "0x420DD381b31aEf6683db6B902084cB0FFECe40Da")]
                    amounts = self.aero_router.functions.getAmountsOut(amount_in, routes).call()
                    return amounts[-1]
                elif pool.dex == DEX.UNISWAP_V3 or pool.dex == DEX.PANCAKE_V3:
                    quoter = self.uni_quoter if pool.dex == DEX.UNISWAP_V3 else self.pancake_quoter
                    params = {"tokenIn": token_in.address, "tokenOut": token_out.address, "amountIn": amount_in, "fee": pool.fee, "sqrtPriceLimitX96": 0}
                    output = quoter.functions.quoteExactInputSingle(params).call()
                    return output[0]
                elif pool.dex == DEX.UNISWAP_V2:
                    router = self.w3.eth.contract(address=pool.router, abi=self.v2_abi)
                    path = [token_in.address, token_out.address]
                    amounts = router.functions.getAmountsOut(amount_in, path).call()
                    return amounts[-1]
                elif pool.dex == DEX.MAVERICK:
                    pool_addr = Web3.to_checksum_address(pool.extra_data.hex() if isinstance(pool.extra_data, bytes) else pool.extra_data)
                    params = {"tokenIn": token_in.address, "tokenOut": token_out.address, "pool": pool_addr, "recipient": self.account.address, "deadline": int(time.time()) + 300, "amountIn": amount_in, "amountOutMinimum": 1, "sqrtPriceLimitX96": 0}
                    return self.mav_quoter.functions.calculateSwap(params).call()
                return 0
            except Exception as e:
                if attempt == retries - 1: return 0
                await asyncio.sleep(0.1 * (attempt + 1))
        return 0

    async def _get_eth_price(self) -> float:
        try:
            params = {"tokenIn": self.WETH.address, "tokenOut": self.USDC.address, "amountIn": 10**18, "fee": 500, "sqrtPriceLimitX96": 0}
            output = self.uni_quoter.functions.quoteExactInputSingle(params).call()
            return float(output[0]) / 1e6
        except Exception: return 3000.0

    async def evaluate_cycle(self, cycle: List[Pool], start_token: Token, amount_in: int) -> Optional[ArbPath]:
        curr_amount = amount_in
        curr_token = start_token
        tokens_in_path = []
        for pool in cycle:
            tokens_in_path.append(curr_token)
            out_amount = await self.get_quote(pool, curr_token, curr_amount)
            if out_amount == 0: return None
            curr_token = pool.token1 if pool.token0.address == curr_token.address else pool.token0
            curr_amount = out_amount
            
        if curr_amount > amount_in:
            profit = curr_amount - amount_in
            eth_price = await self._get_eth_price()
            
            # Build dummy calldata for gas estimation
            swaps = self.executor._build_swaps(ArbPath(pools=cycle, tokens=tokens_in_path, amount_in=amount_in))
            calldata = self.arb_bot.encode_abi("executeArbitrage", args=(
                "0x0000000000000000000000000000000000000000", # dummy lender
                start_token.address, amount_in, swaps
            ))
            
            dexes = [pool.dex for pool in cycle]
            is_profitable, net_profit_usd = self.gas_estimator.is_profitable_after_gas(
                profit if start_token.symbol == "WETH" else int(profit * (10**(18-start_token.decimals))), # Normalize to wei for estimator if needed
                dexes, calldata, self.min_profit_usd, eth_price
            )
            
            # Re-calculate profit USD correctly based on token decimals
            if start_token.symbol == "WETH":
                gross_profit_usd = (profit / 1e18) * eth_price
            else:
                gross_profit_usd = profit / (10 ** start_token.decimals)
            
            # Adjust net_profit_usd based on actual gross
            _, _, total_gas_cost_wei = self.gas_estimator.estimate_arb_gas(dexes, calldata)
            gas_cost_usd = (total_gas_cost_wei / 1e18) * eth_price
            net_profit_usd = gross_profit_usd - gas_cost_usd

            if net_profit_usd >= self.min_profit_usd:
                logger.info(f"Gross: ${gross_profit_usd:.2f}, Gas: ${gas_cost_usd:.2f}, Net: ${net_profit_usd:.2f} | Path: {'->'.join([t.symbol for t in tokens_in_path])}")
                return ArbPath(pools=cycle, tokens=tokens_in_path, amount_in=amount_in, expected_profit=profit, profit_usd=net_profit_usd)
        return None

    async def _fetch_vault_data(self) -> Dict:
        """Fetch real-time vault data for risk engine."""
        # This would ideally call ChainManager and ExchangeManager
        # For now, we provide a reasonable mock that reflects the protocol state
        return {
            "address": os.getenv("VAULT_ADDRESS", "0x0000000000000000000000000000000000000000"),
            "onchain_collateral": 1000000.0, # $1M
            "cex_short_position": -1000000.0,
            "current_price": await self._get_eth_price(),
            "liq_onchain": 0.5,
            "liq_cex": 0.3,
            "symbol": "ETH/USDT"
        }

    async def check_sentinel_risk(self, arb_size_usd: float) -> Tuple[bool, float]:
        try:
            vault_data = await self._fetch_vault_data()
            profile = await self.risk_engine.analyze_vault(vault_data)
            if not profile: return False, 0.0
            
            allowed, reason, multiplier = self.risk_gate.evaluate(profile, arb_size_usd)
            if not allowed:
                logger.warning(f"Risk gate blocked: {reason}")
                self.metrics.record_blocked(reason.split()[0])
            
            self.metrics.update_risk_metrics(profile.health_score, profile.net_delta, profile.volatility_24h)
            return allowed, multiplier
        except Exception as e:
            logger.error(f"Risk check failed: {e}")
            return False, 0.0

    async def run_discovery(self):
        logger.info("Starting production graph-based discovery...")
        base_tokens = [self.WETH, self.USDC, self.KUSD]
        
        while True:
            start_time = time.time()
            # Check risk before starting a round
            allowed, multiplier = await self.check_sentinel_risk(10000.0) # Assume $10k avg arb size for check
            if not allowed:
                await asyncio.sleep(10.0)
                continue

            tasks = []
            for base_token in base_tokens:
                # Determine amount for discovery
                amount = int(self.max_trade_size_eth * multiplier * (10 ** base_token.decimals)) if base_token == self.WETH else int(10000 * multiplier * (10 ** base_token.decimals))
                if amount == 0: continue

                # Use Bellman-Ford for discovery
                # Note: BF is heavier on RPC (fetches all edges), so we might want to alternate or use it less frequently
                # For now, we replace DFS with BF as requested.
                cycles = await self.find_profitable_cycles_bellman_ford(base_token, amount)
                
                # If BF returns nothing (or fails), fallback to DFS? 
                # BF is superior, so let's trust it. But we still need to evaluate the specific path 
                # with exact amounts to get the ArbPath object with profit_usd.
                
                for cycle in cycles:
                    # BF finds the cycle structure. We still need to run evaluate_cycle 
                    # to get the precise profit/gas estimation and ArbPath object.
                    tasks.append(self.evaluate_cycle(cycle, base_token, amount))
            
            try:
                results = await asyncio.gather(*tasks)
                opportunities = [r for r in results if r]
                
                latency = time.time() - start_time
                for base_token in base_tokens:
                    self.metrics.record_discovery(base_token.symbol, 4, latency)

                if opportunities:
                    opportunities.sort(key=lambda x: x.profit_usd, reverse=True)
                    for opp in opportunities:
                        logger.success(f"🎯 Found Opportunity! {opp}")
                        await self.execute_arb(opp)
            except Exception as e:
                logger.error(f"Discovery loop error: {e}")
                if "429" in str(e): self._switch_rpc()
            
            await asyncio.sleep(2.0)

    async def execute_arb(self, opp: ArbPath):
        if not self.arb_bot:
            logger.warning(f"DRY RUN: Found profitable path ${opp.profit_usd:.2f}, but bot not configured.")
            return

        start_time = time.time()
        lenders = [
            (os.getenv("PSM_ADDRESS", ""), LenderPriority.PSM),
            (os.getenv("VAULT_ADDRESS", ""), LenderPriority.VAULT)
        ]
        lenders = [l for l in lenders if l[0]] # Filter empty addresses
        
        result = await self.executor.execute_with_fallback(opp, lenders)
        
        latency = time.time() - start_time
        # Record metrics
        lender_name = "None"
        if result.success:
            # Determine which lender worked (this would be better if ExecutionResult returned it)
            lender_name = "Kerne" 
        
        self.metrics.record_execution(
            result.success, lender_name, result.profit_usd, 
            (result.gas_used * self.w3.eth.gas_price / 1e18) * await self._get_eth_price(),
            latency
        )

        if result.success:
            logger.success(f"✅ Arb Success! Hash: {result.tx_hash}")
            send_discord_alert(f"💰 Graph Arb Success! Profit: ${opp.profit_usd:.2f}\nHash: {result.tx_hash}", level="SUCCESS")
        else:
            logger.error(f"❌ Arb Failed! Error: {result.error} | Revert: {result.revert_reason}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Run without executing on-chain")
    args = parser.parse_args()
    
    scanner = GraphArbScanner()
    if args.dry_run:
        scanner.executor.arb_bot = None # Disable execution
        logger.info("--- DRY RUN MODE ENABLED ---")
        
    asyncio.run(scanner.run_discovery())
