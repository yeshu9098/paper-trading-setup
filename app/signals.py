from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Symbol
import requests
import logging

logger = logging.getLogger(__name__)

FLASK_URL = "http://127.0.0.1:5000/update-tokens"

def send_token_list_to_flask():
    try:
        tokens = list(Symbol.objects.values_list('symboltoken', flat=True))
        print(tokens)
        token_list = [
            {
                "exchangeType": 1,
                "tokens": tokens
            }
        ]

        response = requests.post(
            FLASK_URL,
            json={"token_list": token_list},
            timeout=5
        )
        response.raise_for_status()
        logger.info(f"Token list sent successfully to Flask: {response.json()}")
        
    except requests.RequestException as e:
        logger.error(f"Error sending token list to Flask: {e}")


@receiver(post_save, sender=Symbol)
def handle_symbol_save(sender, instance, created, **kwargs):
    """Trigger when a Symbol is added or updated."""
    logger.info(f"Symbol saved: {instance}")
    send_token_list_to_flask()


@receiver(post_delete, sender=Symbol)
def handle_symbol_delete(sender, instance, **kwargs):
    """Trigger when a Symbol is deleted."""
    logger.info(f"Symbol deleted: {instance}")
    send_token_list_to_flask()
