# your_app/consumers.py
import json
from channels.generic.websocket import WebsocketConsumer
from redis import Redis
import threading
import time

class LivePriceConsumer(WebsocketConsumer):
    def connect(self):
        self.accept()
        self.redis_client = Redis(host='localhost', port=6379, db=0)
        self.pubsub = self.redis_client.pubsub()
        self.pubsub.subscribe('smartapi_live_data')
        self.running = True
        self.thread = threading.Thread(target=self.listen_to_redis, daemon=True)
        self.thread.start()

    def disconnect(self, close_code):
        self.running = False
        self.pubsub.unsubscribe('smartapi_live_data')
        self.redis_client.close()

    def listen_to_redis(self):
        while self.running:
            message = self.pubsub.get_message()
            if message and message['type'] == 'message':
                data = json.loads(message['data'].decode('utf-8'))
                self.send(text_data=json.dumps(data))
            time.sleep(0.1)