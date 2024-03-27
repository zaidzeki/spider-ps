#!/usr/bin/env python3

import io
import lzma
import pickle
from typing import List
from urllib.parse import urlencode
from humanfriendly import format_size
import requests

from core import encrypt, decrypt

from puddle import download as backend_download

API_ENDPOINT = "http://localhost:8100/"


def download(url, params=None):
    if params:
        params = urlencode(params)
    built_url = f'{url}{f"?{params}" if params else ""}'
    print(built_url)
    response = requests.get(built_url)
    return response.content


def get(url: str):
    url = encrypt(url)
    content = download(f"{API_ENDPOINT}single.jpg", params={"url": url})
    content = decrypt(content)
    return content


def bulk(urls: List[str]):
    url = "\n".join(urls)
    url = encrypt(url)
    response = requests.get(f"{API_ENDPOINT}bulk.jpg", params={"url": url})
    content = decrypt(response.content)
    compressed = len(content)
    content = lzma.decompress(content)
    uncompressed = len(content)
    print(f"{format_size(compressed)} / {format_size(uncompressed)}")

    results = []

    with io.BytesIO(content) as fp:
        while True:
            try:
                results += [pickle.dumps(pickle.load(fp))]
            except Exception as e:
                break
    return results


def bulk_defered(urls: List[str]):
    url = "\n".join(urls)
    url = encrypt(url)
    response = requests.get(f"{API_ENDPOINT}push.jpg", params={"url": url})
    content = decrypt(response.content)
    print(content)

    response = requests.get(f"{API_ENDPOINT}pull.jpg")
    content = decrypt(response.content)
    compressed = len(content)
    content = lzma.decompress(content)
    uncompressed = len(content)
    print(f"{format_size(compressed)} / {format_size(uncompressed)}")

    results = []

    with io.BytesIO(content) as fp:
        while True:
            try:
                results += [pickle.dumps(pickle.load(fp))]
            except Exception as e:
                print(e)
                break
    return results
