import asyncio
import os
from web3 import Web3, AsyncWeb3, WebSocketProvider
from loguru import logger
from dotenv import load_dotenv

# Created: 2026-01-23
# Updated: 2026-02-22 (V2: Upgraded to WebSocket-first with HTTP polling fallback)

load_dotenv()

# ERC-4626 / KerneVault event topic signatures
DEPOSIT_TOPIC  = "0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef"
WITHDRAW_TOPIC = "0xfbe9912c4310c28110314c0f7b2291e5b200ac8c7c3b925843392a3516001815"


class VaultEventListener:
    """
    Event listener for the KerneVault contract.
    Primary mode: WebSocket (instant, push-based).
    Fallback mode: HTTP polling every 10s (if WS_URL is missing or unavailable).
    """

    def __init__(
        self,
        vault_address: str,
        abi: list,
        queue: asyncio.Queue,
        rpc_url: str = None,
        ws_url: str = None,
    ):
        self.vault_address = vault_address
        self.abi = abi
        self.queue = queue

        # HTTP RPC (for polling fallback)
        self.rpc_url = rpc_url or os.getenv("RPC_URL", "")
        if self.rpc_url and "," in self.rpc_url:
            self.rpc_url = self.rpc_url.split(",")[0].strip()

        # WebSocket URL (primary)
        self.ws_url = ws_url or os.getenv("WS_URL", "")
        if self.ws_url and "," in self.ws_url:
            self.ws_url = self.ws_url.split(",")[0].strip()

        # Internal state for HTTP fallback
        self._w3_sync: Web3 | None = None
        self._last_block: int | None = None

    # ------------------------------------------------------------------
    # Public entry-point
    # ------------------------------------------------------------------

    async def listen(self):
        """
        Selects the best available transport and starts listening.
        WebSocket → preferred (instant).
        HTTP polling → fallback (if WS_URL is absent or unusable).
        """
        if self.ws_url and self.ws_url.startswith("ws"):
            logger.info("📡 WebSocket URL detected — using WebSocket listener (V2).")
            await self._listen_ws()
        else:
            logger.warning(
                "⚠️ WS_URL not set or invalid. Falling back to HTTP polling. "
                "Set WS_URL=wss://... in .env for instant event detection."
            )
            await self._listen_http()

    # ------------------------------------------------------------------
    # WebSocket listener (primary)
    # ------------------------------------------------------------------

    async def _listen_ws(self):
        """
        Continuously connects to the WebSocket RPC and subscribes to vault logs.
        Reconnects automatically on any error.
        """
        while True:
            try:
                logger.info(f"🔌 Connecting to WebSocket: {self.ws_url}")
                async with AsyncWeb3.persistent_websocket(
                    WebSocketProvider(self.ws_url)
                ) as w3:
                    logger.success(
                        f"✅ WebSocket connected. Subscribing to logs for {self.vault_address}"
                    )

                    # Subscribe to all logs emitted by the vault contract
                    await w3.eth.subscribe("logs", {"address": self.vault_address})
                    logger.info("🔔 Subscription active — awaiting vault events…")

                    async for response in w3.ws.process_subscriptions():
                        await self._handle_ws_log(response)

            except Exception as err:
                logger.error(f"WebSocket error: {err}. Reconnecting in 5 s…")
                await asyncio.sleep(5)

    async def _handle_ws_log(self, response: dict):
        """Parses a raw WebSocket subscription response and enqueues the event."""
        try:
            log = response.get("result", {})
            topics = log.get("topics", [])
            if not topics:
                return

            raw_topic0 = topics[0]
            # Normalise to hex string regardless of what web3 returns
            if isinstance(raw_topic0, bytes):
                topic0 = "0x" + raw_topic0.hex()
            elif isinstance(raw_topic0, str):
                topic0 = raw_topic0 if raw_topic0.startswith("0x") else "0x" + raw_topic0
            else:
                topic0 = str(raw_topic0)

            if topic0 == DEPOSIT_TOPIC:
                logger.info(f"🟢 [WS] Deposit event detected on {self.vault_address}")
                await self.queue.put(("Deposit", log))
            elif topic0 == WITHDRAW_TOPIC:
                logger.info(f"🔴 [WS] Withdraw event detected on {self.vault_address}")
                await self.queue.put(("Withdraw", log))

        except Exception as err:
            logger.warning(f"Failed to parse WS log: {err}")

    # ------------------------------------------------------------------
    # HTTP polling fallback
    # ------------------------------------------------------------------

    def _connect_http_sync(self) -> bool:
        """Establishes a sync HTTP web3 connection for polling."""
        try:
            self._w3_sync = Web3(Web3.HTTPProvider(self.rpc_url))
            if self._w3_sync.is_connected():
                self._last_block = self._w3_sync.eth.block_number
                logger.info(
                    f"✅ HTTP fallback connected to {self.rpc_url} "
                    f"(block #{self._last_block})"
                )
                return True
        except Exception as err:
            logger.error(f"HTTP connection failed: {err}")
        return False

    def _poll_logs_sync(self, from_block: int, to_block: int, topic: str) -> list:
        """Blocking log poll via HTTP provider."""
        return self._w3_sync.eth.get_logs(
            {
                "fromBlock": from_block,
                "toBlock": to_block,
                "address": self.vault_address,
                "topics": [topic],
            }
        )

    async def _listen_http(self):
        """
        HTTP polling fallback.  Polls every 10 seconds for Deposit / Withdraw logs.
        Runs entirely via asyncio.to_thread to keep the event loop unblocked.
        """
        while True:
            connected = await asyncio.to_thread(self._connect_http_sync)
            if not connected:
                await asyncio.sleep(5)
                continue

            logger.info(
                f"📡 [HTTP] Polling for events on {self.vault_address} every 10 s"
            )

            while True:
                try:
                    current_block: int = await asyncio.to_thread(
                        lambda: self._w3_sync.eth.block_number
                    )

                    if self._last_block and current_block > self._last_block:
                        from_block = self._last_block + 1

                        # Deposit events
                        deposit_logs = await asyncio.to_thread(
                            self._poll_logs_sync, from_block, current_block, DEPOSIT_TOPIC
                        )
                        for log in deposit_logs:
                            logger.info(f"🟢 [HTTP] Deposit event detected")
                            await self.queue.put(("Deposit", log))

                        # Withdraw events
                        withdraw_logs = await asyncio.to_thread(
                            self._poll_logs_sync, from_block, current_block, WITHDRAW_TOPIC
                        )
                        for log in withdraw_logs:
                            logger.info(f"🔴 [HTTP] Withdraw event detected")
                            await self.queue.put(("Withdraw", log))

                        self._last_block = current_block

                    await asyncio.sleep(10)

                except Exception as poll_err:
                    logger.error(f"[HTTP] Polling error: {poll_err}. Retrying in 5 s…")
                    await asyncio.sleep(5)
                    # Reconnect on persistent error
                    break