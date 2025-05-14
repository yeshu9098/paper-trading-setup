import json
from channels.generic.websocket import AsyncWebsocketConsumer
from redis import Redis

class LivePriceConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.redis_client = Redis(host='localhost', port=6379, db=0, decode_responses=True)

    async def connect(self):
        # Join the live_prices group
        await self.channel_layer.group_add("live_prices", self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        # Leave the live_prices group
        await self.channel_layer.group_discard("live_prices", self.channel_name)
        self.redis_client.close()

    async def receive(self, text_data):
        data = json.loads(text_data)
        if data.get('type') == 'fetch_initial_ltp':
            tokens = data.get('tokens', [])
            # Fetch LTPs from Redis
            with self.redis_client.pipeline() as pipe:
                for token in tokens:
                    pipe.get(f"stock:ltp:{token}")
                ltps = pipe.execute()
                for token, ltp in zip(tokens, ltps):
                    if ltp is not None:
                        await self.send(text_data=json.dumps({
                            'token': token,
                            'last_traded_price': float(ltp)
                        }))
                    else:
                        await self.send(text_data=json.dumps({
                            'token': token,
                            'last_traded_price': 0,
                            'error': f'No LTP data for token {token}'
                        }))

    async def market_update(self, event):
        # Forward market updates from the group to the client
        data = event['data']
        await self.send(text_data=json.dumps(data))