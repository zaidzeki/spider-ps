from base64 import urlsafe_b64decode, urlsafe_b64encode
from typing import Union

from Crypto.Cipher import AES


def aes_decrypt(key, data, return_str=True):
    """
    Decrypts data using key checking data integrity using the embedded MAC tag
    :param key: key to use decrypt data
    :param data: data to be decrypted
    :param return_str: should the data be changed to str
    :return: a str or bytes object
    :raises ValueError: when the encrypted data was modified post encryption
    """
    nonce = data[:16]
    tag = data[16:32]
    ciphertext = data[32:]
    cipher = AES.new(key, AES.MODE_EAX, nonce=nonce)
    decrypted_data = cipher.decrypt_and_verify(ciphertext, tag)
    if return_str:
        try:
            decrypted_data = str(decrypted_data, "utf-8")
        except UnicodeError as e:
            pass
    return decrypted_data


def aes_encrypt(key, data):
    """
    Encrypts data using key
    :param key: key to use to encrypt data
    :param data: data to be encrypted
    :return: encrypted data with nonce and MAC tag prepended
    """
    if type(data) == str:
        data = bytes(data, "utf-8")
    cipher = AES.new(key, AES.MODE_EAX)
    ciphertext, tag = cipher.encrypt_and_digest(data)
    encrypted_data = cipher.nonce + tag + ciphertext
    return encrypted_data


AES_KEY = b"0" * 16


def decrypt(data: Union[bytes, str]) -> Union[bytes, str]:
    if type(data) == str:
        data = bytes(data, "utf-8")
    decoded = urlsafe_b64decode(data)
    plain = aes_decrypt(AES_KEY, decoded)
    return plain


def encrypt(data: Union[bytes, str]) -> Union[bytes, str]:
    encrypted = aes_encrypt(AES_KEY, data)
    encoded = urlsafe_b64encode(encrypted)
    response = str(encoded, "utf-8")
    return response
