"""AES-GCM-salaus, jonka asetussivu osaa purkaa selaimessa (WebCrypto).

Avain johdetaan salasanasta PBKDF2-SHA256:lla (200 000 kierrosta).
Muoto: {"salt": b64, "iv": b64, "data": b64(ciphertext+tag)}
"""
import base64
import json
import os

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

KIERROKSET = 200_000


def _avain(salasana, salt):
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=KIERROKSET)
    return kdf.derive(salasana.encode("utf-8"))


def salaa(olio, salasana):
    salt, iv = os.urandom(16), os.urandom(12)
    data = AESGCM(_avain(salasana, salt)).encrypt(iv, json.dumps(olio, ensure_ascii=False).encode("utf-8"), None)
    b = lambda x: base64.b64encode(x).decode()
    return {"salt": b(salt), "iv": b(iv), "data": b(data)}


def pura(paketti, salasana):
    d = lambda k: base64.b64decode(paketti[k])
    raaka = AESGCM(_avain(salasana, d("salt"))).decrypt(d("iv"), d("data"), None)
    return json.loads(raaka.decode("utf-8"))
