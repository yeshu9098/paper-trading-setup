import pyotp
from SmartApi import SmartConnect
import logging
from decouple import config


API_KEY = config('API_KEY')
USERNAME = config('USERNAME')
PASSWORD = config('PASSWORD')
TOKEN = config('TOKEN')


def get_smartapi_session():
    """Initialize SmartAPI session."""
    try:
        totp = pyotp.TOTP(TOKEN).now()
        obj = SmartConnect(API_KEY)
        print(obj)
        data = obj.generateSession(USERNAME, PASSWORD, totp)
        return {
            "obj": obj,
            "authToken": data['data']['jwtToken'],
            "refreshToken": data['data']['refreshToken'],
            "feedToken": obj.getfeedToken()
        }
    except Exception as e:
        return None
