import json
import asyncio
import requests
from channels.generic.websocket import AsyncWebsocketConsumer
from app.models import Symbol
from asgiref.sync import sync_to_async

FLASK_APP_URL = "http://127.0.0.1:5000/live-data"

class LiveDataConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

        self.keep_sending = True
        self.live_data_task = asyncio.create_task(self.send_live_data())

    async def disconnect(self, close_code):
        # print("Client disconnected")
        self.keep_sending = False
        if hasattr(self, "live_data_task"):
            self.live_data_task.cancel()

    async def send_live_data(self):
        while self.keep_sending:
            try:
                response = requests.get(FLASK_APP_URL, timeout=5)
                response.raise_for_status()
                live_data = response.json()

                await self.send(json.dumps({"live_data": live_data}))
            except requests.RequestException as e:
                await self.send(json.dumps({"error": str(e)}))
            except Exception as e:
                await self.send(json.dumps({"error": f"Unexpected error: {str(e)}"}))

            await asyncio.sleep(2)
