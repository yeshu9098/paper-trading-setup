from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Stock
import requests


FLASK_URL = "http://127.0.0.1:5000/update-tokens"

def send_token_list_to_flask():
    try:
        tokens = list(Stock.objects.values_list('token', flat=True))
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
        print(f"Token list sent successfully to Flask: {response.json()}")
        
    except requests.RequestException as e:
        print(f"Error sending token list to Flask: {e}")

@receiver(post_save, sender=Stock)
def handle_symbol_save(sender, instance, created, **kwargs):
    """Trigger when a Stock is added or updated."""
    print(f"Stock saved: {instance}")
    send_token_list_to_flask()


@receiver(post_delete, sender=Stock)
def handle_symbol_delete(sender, instance, **kwargs):
    """Trigger when a Stock is deleted."""
    print(f"Stock deleted: {instance}")
    send_token_list_to_flask()
