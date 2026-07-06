import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from app.services import llm_client

async def main():
    try:
        res = llm_client.generate("Say hello", system_instruction=None)
        print("LLM success:", res)
    except Exception as e:
        print("LLM failed:", e)

asyncio.run(main())
