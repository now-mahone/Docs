# Created: 2026-01-26
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Any
from web3 import Web3
from web3.contract import Contract

class IntentVenue(Enum):
    COWSWAP = "CowSwap"
    UNISWAPX = "UniswapX"
    FUSION = "1inchFusion"
    LIFI = "LIFI"
    AORI = "Aori"
    DIRECT = "Direct"

@dataclass
class ChainConfig:
    name: str
    chain_id: int
    rpc_urls: List[str]
    executor_address: str
    pool_address: str
    profit_vault_address: Optional[str]
    cowswap_api_base: Optional[str]
    uniswapx_config: Dict[str, Any]
    aerodrome_router: Optional[str]
    token_targets: Dict[str, str]
    explorer_base_url: str
    fusion_settler: Optional[str] = None
    lifi_settler: Optional[str] = None
    aori_settler: Optional[str] = None

@dataclass
class ChainContext:
    config: ChainConfig
    w3: Web3
    zin_executor: Contract
    zin_pool: Contract

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
    chain: str
    signature: str = ""
    encoded_order: str = ""
    raw_order: Dict = field(default_factory=dict)

    @property
    def token_in_symbol(self) -> str:
        return self.raw_order.get("token_in_symbol", "UNKNOWN")

    @property
    def token_out_symbol(self) -> str:
        return self.raw_order.get("token_out_symbol", "UNKNOWN")

class BaseIntentFetcher(ABC):
    """Base class for intent fetchers."""
    @abstractmethod
    async def fetch_intents(self, context: ChainContext) -> List[IntentData]:
        """Fetch intents from the venue."""
        pass
