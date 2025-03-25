import json
import logging
import threading
import time
import redis
from SmartApi.smartWebSocketV2 import SmartWebSocketV2
from app.utils import get_smartapi_session  # Your custom session function
from decouple import config

API_KEY = config('API_KEY')
USERNAME = config('USERNAME')

# Django setup
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'strategy.settings')  # Replace with your Django project settings module
django.setup()

from app.models import Stock  # Replace 'your_app' with the app containing the Stock model

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LiveDataStreamer:
    def __init__(self):
        self.sws = None
        self.connected = False
        self.reconnect_attempts = 0
        self.MAX_RECONNECT_ATTEMPTS = 5
        self.RECONNECT_DELAY = 5
        self.redis_client = redis.Redis(host='localhost', port=6379, db=0)
        self.redis_channel = 'smartapi_live_data'
        self.current_tokens = set()  # Track currently subscribed tokens
        self.monitor_thread = None
        self.running = False

    def _get_session_tokens(self):
        """Get fresh session tokens using your custom function"""
        session = get_smartapi_session()
        if not session:
            raise Exception("Failed to get SmartAPI session")
        return {
            'auth_token': session['authToken'],
            'feed_token': session['feedToken'],
        }

    def _on_data(self, wsapp, message):
        """Handle incoming market data"""
        try:
            data = message if isinstance(message, dict) else json.loads(message)
            print(data)
            self.redis_client.publish(self.redis_channel, json.dumps(data))
            logger.debug("Received market data update")
        except Exception as e:
            logger.error(f"Data handling error: {e}")

    def _on_error(self, wsapp, error):
        """Handle WebSocket errors"""
        logger.error(f"WebSocket error: {error}")
        self._reconnect()

    def _on_close(self, wsapp, status_code, close_reason):
        """Handle WebSocket closure"""
        logger.info(f"Connection closed | Status: {status_code} | Reason: {close_reason}")
        self.connected = False
        self._reconnect()

    def _on_open(self, wsapp):
        """Handle WebSocket connection opening"""
        logger.info("WebSocket connection established")
        self.connected = True
        self.reconnect_attempts = 0
        self._subscribe_to_stocks()

    def _get_stock_tokens(self):
        """Fetch tokens from the Stock model"""
        stocks = Stock.objects.all()
        token_list = [{
            "exchangeType": 1,  # Assuming NSE; adjust as needed
            "tokens": [stock.token for stock in stocks]
        }]
        return token_list, set(stock.token for stock in stocks)

    def _subscribe_to_stocks(self):
        """Subscribe to instruments from the Stock model"""
        token_list, new_tokens = self._get_stock_tokens()
        if new_tokens != self.current_tokens:
            if self.current_tokens:
                # Unsubscribe from old tokens if there are changes
                old_token_list = [{"exchangeType": 1, "tokens": list(self.current_tokens)}]
                self.sws.unsubscribe("live_stream", 1, old_token_list)
                logger.info("Unsubscribed from previous tokens")
            
            self.sws.subscribe("live_stream", 1, token_list)
            self.current_tokens = new_tokens
            logger.info(f"Subscribed to updated stock tokens: {self.current_tokens}")
        else:
            logger.info("No changes in stock tokens; subscription unchanged")

    def _monitor_stock_changes(self):
        """Monitor the Stock model for changes and update subscription"""
        while self.running:
            try:
                token_list, new_tokens = self._get_stock_tokens()
                if new_tokens != self.current_tokens and self.connected:
                    logger.info("Detected changes in Stock model; updating subscription")
                    self._subscribe_to_stocks()
                time.sleep(5)  # Check every 5 seconds; adjust as needed
            except Exception as e:
                logger.error(f"Error in stock monitoring: {e}")
                time.sleep(5)

    def _reconnect(self):
        """Handle reconnection logic"""
        if self.reconnect_attempts >= self.MAX_RECONNECT_ATTEMPTS:
            logger.error("Max reconnection attempts reached")
            return

        self.reconnect_attempts += 1
        logger.info(f"Reconnection attempt {self.reconnect_attempts}/{self.MAX_RECONNECT_ATTEMPTS}")
        
        try:
            self.stop()
            time.sleep(self.RECONNECT_DELAY)
            self.start()
        except Exception as e:
            logger.error(f"Reconnection failed: {e}")

    def start(self):
        """Initialize and start WebSocket connection"""
        if self.running:
            logger.info("Streamer already running")
            return

        try:
            tokens = self._get_session_tokens()
            
            self.sws = SmartWebSocketV2(
                auth_token=tokens['auth_token'],
                api_key=API_KEY,  # Replace with your API key
                client_code=USERNAME,  # Replace with your client code
                feed_token=tokens['feed_token']
            )

            # Assign callbacks
            self.sws.on_open = self._on_open
            self.sws.on_data = self._on_data
            self.sws.on_error = self._on_error
            self.sws.on_close = self._on_close

            # Start connection in a thread
            self.ws_thread = threading.Thread(target=self.sws.connect, daemon=True)
            self.ws_thread.start()
            logger.info("WebSocket connection initiated")

            # Start stock monitoring thread
            self.running = True
            self.monitor_thread = threading.Thread(target=self._monitor_stock_changes, daemon=True)
            self.monitor_thread.start()
            logger.info("Stock monitoring thread started")

        except Exception as e:
            logger.error(f"Connection startup failed: {e}")
            self._reconnect()

    def stop(self):
        """Cleanly stop WebSocket connection and monitoring"""
        self.running = False
        if self.sws:
            self.sws.close_connection()
        self.connected = False
        self.current_tokens.clear()
        logger.info("WebSocket connection and monitoring stopped")

# Main execution
if __name__ == '__main__':
    streamer = LiveDataStreamer()
    streamer.start()
    
    try:
        while True:
            # Keep main thread alive
            time.sleep(1)
    except KeyboardInterrupt:
        streamer.stop()
        logger.info("Application terminated")