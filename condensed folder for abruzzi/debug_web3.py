import asyncio
import os
from web3 import AsyncWeb3, AsyncWebsocketProvider
from dotenv import load_dotenv
import inspect

load_dotenv()

async def debug():
    wss_url = os.getenv("WSS_URL")
    if not wss_url:
        rpc_url = os.getenv("RPC_URL", "").split(",")[0]
        wss_url = rpc_url.replace("https://", "wss://")
    
    print(f"Connecting to {wss_url}")
    w3 = AsyncWeb3(AsyncWebsocketProvider(wss_url))
    
    print(f"is_connected type: {type(w3.is_connected)}")
    print(f"is_connected is coroutine function: {inspect.iscoroutinefunction(w3.is_connected)}")
    
    try:
        res = w3.is_connected()
        print(f"is_connected() result type: {type(res)}")
        if inspect.iscoroutine(res):
            connected = await res
        else:
            connected = res
        print(f"Connected: {connected}")
    except Exception as e:
        print(f"is_connected failed: {e}")

    print(f"eth.get_block type: {type(w3.eth.get_block)}")
    try:
        res = w3.eth.get_block('latest')
        print(f"eth.get_block('latest') result type: {type(res)}")
        if inspect.iscoroutine(res):
            block = await res
        else:
            block = res
        print(f"Block number: {block['number']}")
    except Exception as e:
        print(f"eth.get_block failed: {e}")

if __name__ == "__main__":
    asyncio.run(debug())