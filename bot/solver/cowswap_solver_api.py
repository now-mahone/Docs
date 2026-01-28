# Created: 2026-01-27
"""
Kerne CoW Swap Solver API
HTTP endpoint for CoW Protocol solver competition.

This API receives auction batches from CoW Swap's driver and returns solutions
using Kerne's ZIN (Zero-Fee Intent Network) infrastructure.

Endpoint: POST /solve
"""

import os
import time
import json
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from decimal import Decimal

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from loguru import logger
from web3 import Web3

# Load environment
def _load_env():
    """Load environment variables from bot/.env file."""
    from pathlib import Path
    possible_paths = [
        Path(__file__).parent.parent / ".env",
        Path.cwd() / "bot" / ".env",
        Path.cwd() / ".env",
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
                        if key and key not in os.environ:
                            os.environ[key] = value
            return str(env_path)
    return None

_load_env()

# =============================================================================
# CONFIGURATION
# =============================================================================

SOLVER_NAME = "Kerne"
SOLVER_VERSION = "1.0.0"

# Base Mainnet Addresses
BASE_WETH = "0x4200000000000000000000000000000000000006"
BASE_USDC = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
BASE_WSTETH = "0xc1CBa3fCea344f92D9239c08C0568f6F2F0ee452"
BASE_CBETH = "0x2Ae3F1Ec7F1F5012CFEab0185bfc7aa3cf0DEc22"

# Aerodrome Router (Base)
AERODROME_ROUTER = "0xcF77a3Ba9A5CA399B7c97c478569a74DD55C726f"
AERODROME_FACTORY = "0x420DD381b31aEf6683db6B902084cB0FFECe40Da"

# CoW Protocol Settlement Contract (Base)
COW_SETTLEMENT = "0x9008D19f58AAbD9eD0D60971565AA8510560ab41"

# ZIN Infrastructure
ZIN_EXECUTOR = os.getenv("ZIN_EXECUTOR_ADDRESS", "0x04F52F9F4dAb1ba2330841Af85dAeeB8eaC9E995")
ZIN_POOL = os.getenv("ZIN_POOL_ADDRESS", "0xB9BdF6F3Fc3819b61f6fE799bE1395501822d0c7")

# RPC Configuration
BASE_RPC_URL = os.getenv("BASE_RPC_URL") or os.getenv("RPC_URL", "").split(",")[0] or "https://mainnet.base.org"

# Solver Configuration
MIN_PROFIT_BPS = int(os.getenv("ZIN_MIN_PROFIT_BPS", "5"))
MAX_GAS_PRICE_GWEI = int(os.getenv("ZIN_MAX_GAS_PRICE_GWEI", "50"))

# Supported tokens we can provide liquidity for
SUPPORTED_TOKENS = {
    BASE_USDC.lower(): {"symbol": "USDC", "decimals": 6},
    BASE_WETH.lower(): {"symbol": "WETH", "decimals": 18},
    BASE_WSTETH.lower(): {"symbol": "wstETH", "decimals": 18},
    BASE_CBETH.lower(): {"symbol": "cbETH", "decimals": 18},
}

# =============================================================================
# PYDANTIC MODELS (CoW Protocol API Schema)
# =============================================================================

class TokenAmount(BaseModel):
    """Token amount in an order."""
    token: str
    amount: str

class Order(BaseModel):
    """CoW Protocol order."""
    uid: str
    sellToken: str
    buyToken: str
    sellAmount: str
    buyAmount: str
    validTo: int
    appData: str = "0x0000000000000000000000000000000000000000000000000000000000000000"
    feeAmount: str = "0"
    kind: str = "sell"
    partiallyFillable: bool = False
    sellTokenBalance: str = "erc20"
    buyTokenBalance: str = "erc20"
    signingScheme: str = "eip712"
    signature: str = ""
    receiver: Optional[str] = None
    owner: str = ""
    
class AuctionInstance(BaseModel):
    """CoW Protocol auction instance."""
    id: int = 0
    orders: List[Order] = Field(default_factory=list)
    tokens: Dict[str, Any] = Field(default_factory=dict)
    
class SolveRequest(BaseModel):
    """Request body for /solve endpoint."""
    id: int = 0
    tokens: Dict[str, Any] = Field(default_factory=dict)
    orders: List[Order] = Field(default_factory=list)
    liquidity: List[Any] = Field(default_factory=list)
    effectiveGasPrice: str = "0"
    deadline: str = ""

class Trade(BaseModel):
    """A trade in the solution."""
    kind: str = "fulfillment"
    order: str  # Order UID
    executedAmount: str

class Interaction(BaseModel):
    """An interaction (contract call) in the solution."""
    target: str
    value: str = "0"
    callData: str

class Solution(BaseModel):
    """A solution to the auction."""
    id: int = 0
    prices: Dict[str, str] = Field(default_factory=dict)
    trades: List[Trade] = Field(default_factory=list)
    interactions: List[List[Interaction]] = Field(default_factory=list)  # [pre, intra, post]
    score: str = "0"

class SolveResponse(BaseModel):
    """Response body for /solve endpoint."""
    solutions: List[Solution] = Field(default_factory=list)

# =============================================================================
# SOLVER LOGIC
# =============================================================================

class KerneSolver:
    """
    Kerne CoW Swap Solver
    
    Uses Kerne's ZIN infrastructure to provide liquidity for CoW Protocol auctions.
    """
    
    def __init__(self):
        self.w3 = Web3(Web3.HTTPProvider(BASE_RPC_URL, request_kwargs={'timeout': 30}))
        self.solution_counter = 0
        
        # Aerodrome Router ABI for quoting
        self.router_abi = [
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
        
        # ZIN Pool ABI for liquidity checks
        self.pool_abi = [
            {
                "inputs": [{"name": "token", "type": "address"}],
                "name": "maxFlashLoan",
                "outputs": [{"name": "", "type": "uint256"}],
                "stateMutability": "view",
                "type": "function"
            }
        ]
        
        logger.info(f"Kerne Solver initialized")
        logger.info(f"  RPC: {BASE_RPC_URL[:50]}...")
        logger.info(f"  ZIN Executor: {ZIN_EXECUTOR}")
        logger.info(f"  ZIN Pool: {ZIN_POOL}")
        
    def _is_supported_pair(self, sell_token: str, buy_token: str) -> bool:
        """Check if we support this token pair."""
        sell_lower = sell_token.lower()
        buy_lower = buy_token.lower()
        
        # We need at least one token to be in our supported list
        return sell_lower in SUPPORTED_TOKENS or buy_lower in SUPPORTED_TOKENS
    
    def _get_aerodrome_quote(
        self,
        token_in: str,
        token_out: str,
        amount_in: int
    ) -> Optional[int]:
        """Get quote from Aerodrome."""
        try:
            router = self.w3.eth.contract(
                address=Web3.to_checksum_address(AERODROME_ROUTER),
                abi=self.router_abi
            )
            
            # Try both stable and volatile pools
            for stable in [False, True]:
                try:
                    routes = [(
                        Web3.to_checksum_address(token_in),
                        Web3.to_checksum_address(token_out),
                        stable,
                        Web3.to_checksum_address(AERODROME_FACTORY)
                    )]
                    
                    amounts = router.functions.getAmountsOut(amount_in, routes).call()
                    
                    if len(amounts) >= 2 and amounts[-1] > 0:
                        return amounts[-1]
                        
                except Exception:
                    continue
                    
        except Exception as e:
            logger.debug(f"Aerodrome quote error: {e}")
            
        return None
    
    def _check_pool_liquidity(self, token: str) -> int:
        """Check available liquidity in ZIN pool."""
        try:
            pool = self.w3.eth.contract(
                address=Web3.to_checksum_address(ZIN_POOL),
                abi=self.pool_abi
            )
            return pool.functions.maxFlashLoan(
                Web3.to_checksum_address(token)
            ).call()
        except Exception as e:
            logger.debug(f"Liquidity check error: {e}")
            return 0
    
    def _build_swap_calldata(
        self,
        token_in: str,
        token_out: str,
        amount_in: int,
        min_amount_out: int,
        recipient: str
    ) -> str:
        """Build Aerodrome swap calldata."""
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
        
        router = self.w3.eth.contract(
            address=Web3.to_checksum_address(AERODROME_ROUTER),
            abi=swap_abi
        )
        
        routes = [(
            Web3.to_checksum_address(token_in),
            Web3.to_checksum_address(token_out),
            False,  # volatile pool
            Web3.to_checksum_address(AERODROME_FACTORY)
        )]
        
        deadline = int(time.time()) + 300  # 5 minutes
        
        calldata = router.encodeABI(
            fn_name="swapExactTokensForTokens",
            args=[amount_in, min_amount_out, routes, recipient, deadline]
        )
        
        return calldata
    
    async def solve(self, request: SolveRequest) -> SolveResponse:
        """
        Solve a CoW Protocol auction.
        
        This is the main entry point called by CoW Protocol's driver.
        """
        logger.info(f"Received auction {request.id} with {len(request.orders)} orders")
        
        solutions = []
        
        # Check gas price
        try:
            gas_price_gwei = self.w3.eth.gas_price / 1e9
            if gas_price_gwei > MAX_GAS_PRICE_GWEI:
                logger.warning(f"Gas price too high: {gas_price_gwei:.2f} gwei")
                return SolveResponse(solutions=[])
        except Exception as e:
            logger.warning(f"Could not check gas price: {e}")
        
        # Process each order
        for order in request.orders:
            try:
                solution = await self._solve_order(order, request)
                if solution:
                    solutions.append(solution)
            except Exception as e:
                logger.error(f"Error solving order {order.uid[:16]}: {e}")
                continue
        
        logger.info(f"Returning {len(solutions)} solutions")
        return SolveResponse(solutions=solutions)
    
    async def _solve_order(
        self,
        order: Order,
        request: SolveRequest
    ) -> Optional[Solution]:
        """Attempt to solve a single order."""
        
        # Check if we support this pair
        if not self._is_supported_pair(order.sellToken, order.buyToken):
            logger.debug(f"Unsupported pair: {order.sellToken[:10]} -> {order.buyToken[:10]}")
            return None
        
        # Check order validity
        if order.validTo < int(time.time()):
            logger.debug(f"Order expired: {order.uid[:16]}")
            return None
        
        sell_amount = int(order.sellAmount)
        buy_amount = int(order.buyAmount)
        
        # Get quote from Aerodrome
        quote_output = self._get_aerodrome_quote(
            order.sellToken,
            order.buyToken,
            sell_amount
        )
        
        if not quote_output:
            logger.debug(f"No quote available for order {order.uid[:16]}")
            return None
        
        # Check if we can fulfill the order (output >= required)
        if quote_output < buy_amount:
            logger.debug(f"Quote insufficient: {quote_output} < {buy_amount}")
            return None
        
        # Calculate profit
        profit = quote_output - buy_amount
        profit_bps = (profit * 10000) // buy_amount if buy_amount > 0 else 0
        
        if profit_bps < MIN_PROFIT_BPS:
            logger.debug(f"Profit too low: {profit_bps} bps")
            return None
        
        # Check liquidity
        liquidity = self._check_pool_liquidity(order.buyToken)
        if liquidity < buy_amount:
            logger.debug(f"Insufficient liquidity: {liquidity} < {buy_amount}")
            return None
        
        logger.info(f"Found profitable order: {order.uid[:16]}, profit: {profit_bps} bps")
        
        # Build solution
        self.solution_counter += 1
        
        # Calculate clearing prices
        # Price is expressed as: how much of token B per unit of token A
        # For a sell order: sellToken price = buyAmount / sellAmount
        sell_price = str((buy_amount * 10**18) // sell_amount) if sell_amount > 0 else "0"
        buy_price = str((sell_amount * 10**18) // buy_amount) if buy_amount > 0 else "0"
        
        # Build swap interaction
        min_out = int(buy_amount * 0.995)  # 0.5% slippage buffer
        swap_calldata = self._build_swap_calldata(
            order.sellToken,
            order.buyToken,
            sell_amount,
            min_out,
            COW_SETTLEMENT  # Tokens go to settlement contract
        )
        
        # Pre-interaction: approve tokens if needed (usually not needed for CoW)
        pre_interactions: List[Interaction] = []
        
        # Intra-interaction: the actual swap
        intra_interactions: List[Interaction] = [
            Interaction(
                target=AERODROME_ROUTER,
                value="0",
                callData=swap_calldata
            )
        ]
        
        # Post-interaction: none needed
        post_interactions: List[Interaction] = []
        
        solution = Solution(
            id=self.solution_counter,
            prices={
                order.sellToken: sell_price,
                order.buyToken: buy_price,
            },
            trades=[
                Trade(
                    kind="fulfillment",
                    order=order.uid,
                    executedAmount=order.sellAmount
                )
            ],
            interactions=[pre_interactions, intra_interactions, post_interactions],
            score=str(profit)  # Score is the surplus we generate
        )
        
        return solution

# =============================================================================
# FASTAPI APPLICATION
# =============================================================================

app = FastAPI(
    title="Kerne CoW Swap Solver",
    description="Solver endpoint for CoW Protocol solver competition",
    version=SOLVER_VERSION
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize solver
solver = KerneSolver()

@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "solver": SOLVER_NAME,
        "version": SOLVER_VERSION,
        "status": "healthy",
        "timestamp": int(time.time())
    }

@app.get("/health")
async def health():
    """Health check for monitoring."""
    return {"status": "ok"}

@app.get("/info")
async def info():
    """Solver information."""
    return {
        "name": SOLVER_NAME,
        "version": SOLVER_VERSION,
        "supported_chains": [8453],  # Base
        "supported_tokens": list(SUPPORTED_TOKENS.keys()),
        "zin_executor": ZIN_EXECUTOR,
        "zin_pool": ZIN_POOL,
        "min_profit_bps": MIN_PROFIT_BPS
    }

@app.post("/solve")
async def solve(request: SolveRequest):
    """
    Main solver endpoint.
    
    Receives auction batches from CoW Protocol's driver and returns solutions.
    """
    try:
        response = await solver.solve(request)
        return response
    except Exception as e:
        logger.error(f"Solve error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/quote")
async def quote(request: Request):
    """
    Quote endpoint for testing.
    
    Returns a quote for a single order without committing to solve.
    """
    try:
        body = await request.json()
        sell_token = body.get("sellToken", "")
        buy_token = body.get("buyToken", "")
        sell_amount = int(body.get("sellAmount", 0))
        
        if not all([sell_token, buy_token, sell_amount]):
            raise HTTPException(status_code=400, detail="Missing required fields")
        
        quote_output = solver._get_aerodrome_quote(sell_token, buy_token, sell_amount)
        
        if not quote_output:
            return {"quote": None, "reason": "No route available"}
        
        return {
            "sellToken": sell_token,
            "buyToken": buy_token,
            "sellAmount": str(sell_amount),
            "buyAmount": str(quote_output),
            "aggregator": "Aerodrome"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Quote error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics")
async def metrics():
    """Solver metrics for monitoring."""
    return {
        "solutions_generated": solver.solution_counter,
        "solver": SOLVER_NAME,
        "version": SOLVER_VERSION
    }

# =============================================================================
# CLI ENTRY POINT
# =============================================================================

def main():
    """Run the solver API server."""
    import uvicorn
    
    host = os.getenv("SOLVER_HOST", "0.0.0.0")
    port = int(os.getenv("SOLVER_PORT", "8080"))
    
    logger.info(f"Starting Kerne CoW Swap Solver API on {host}:{port}")
    
    uvicorn.run(
        "bot.solver.cowswap_solver_api:app",
        host=host,
        port=port,
        reload=False,
        log_level="info"
    )

if __name__ == "__main__":
    main()
