import os
import base64
from py_vapid import Vapid
from cryptography.hazmat.primitives import serialization

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VAPID_PRIVATE_KEY_PATH = os.path.join(BASE_DIR, 'private_key.pem')
VAPID_PUBLIC_KEY_PATH = os.path.join(BASE_DIR, 'public_key.pem')

def ensure_vapid_keys():
    if not os.path.exists(VAPID_PRIVATE_KEY_PATH):
        v = Vapid()
        v.generate_keys()
        v.save_key(VAPID_PRIVATE_KEY_PATH)
        v.save_public_key(VAPID_PUBLIC_KEY_PATH)

def get_vapid_public_key_b64():
    ensure_vapid_keys()
    v = Vapid.from_file(VAPID_PRIVATE_KEY_PATH)
    # Get the uncompressed public key bytes
    public_key_bytes = v.public_key.public_bytes(
        encoding=serialization.Encoding.X962,
        format=serialization.PublicFormat.UncompressedPoint
    )
    # Encode as urlsafe base64 without padding
    return base64.urlsafe_b64encode(public_key_bytes).decode('utf-8').rstrip('=')
