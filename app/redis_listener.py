import redis
import json
from django.conf import settings
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def start_redis_listener():
    redis_client = redis.Redis(
        host='localhost',
        port=6379,
        db=0,
        decode_responses=True
    )
    pubsub = redis_client.pubsub()
    pubsub.subscribe('smartapi_live_data')  # Same channel as your streamer
    
    channel_layer = get_channel_layer()

    for message in pubsub.listen():
        if message['type'] == 'message':
            try:
                data = json.loads(message['data'])
                # Store LTP in Redis
                token = data.get('token')
                ltp = data.get('last_traded_price')
                if token and ltp is not None:
                    redis_client.set(f"stock:ltp:{token}", ltp)
                # Forward to WebSocket group
                async_to_sync(channel_layer.group_send)(
                    "live_prices",
                    {
                        "type": "market_update",
                        "data": data
                    }
                )
            except Exception as e:
                print(f"Error handling Redis message: {e}")