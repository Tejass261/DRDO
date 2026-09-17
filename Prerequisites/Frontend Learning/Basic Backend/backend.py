import asyncio
import json
import random
import websockets


async def handle_connection(websocket):
    print("[Python] Electron app connected!")

    try:
        while True:
            # 1. Prepare data payload
            payload = {
                "temperature": round(random.uniform(20.0, 30.0), 1),
                "humidity": round(random.uniform(40.0, 60.0), 1),
                "status": "Active"
            }

            # 2. Send JSON string over WebSocket
            await websocket.send(json.dumps(payload))
            print(f"[Python] Sent: {payload}")

            # 3. Wait 2 seconds before sending next update
            await asyncio.sleep(2)

    except websockets.exceptions.ConnectionClosed:
        print("[Python] Electron app disconnected.")


async def main():
    print("[Python] Starting WebSocket server on ws://localhost:8765...")

    async with websockets.serve(handle_connection, "localhost", 8765):
        await asyncio.Future()  # Keep server running forever


if __name__ == "__main__":
    asyncio.run(main())