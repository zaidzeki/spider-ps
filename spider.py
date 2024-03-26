#!/usr/bin/env python3

from datetime import date
import json
import logging
import os
import pickle
import re
from hashlib import sha1
from urllib.parse import urljoin, urlparse

import requests
from retrying import retry
from tqdm import tqdm

os.makedirs("spider-logs", exist_ok=True)
logging.basicConfig(
    filename=f"spider-logs/{str(date.today())}.log", level=logging.DEBUG, force=True
)

TOTAL = 2 * 10**8
progressbar = tqdm(
    total=TOTAL,
    colour="#2196F3",
    desc="Scrapping",
    unit="B",
    unit_scale=True
)
frontier = []
visited = []
_exit = exit

def exit():
    with open('out.json', 'w') as fp:
        json.dump({
            'frontier':frontier,
            'visited': visited
        }, fp)
    _exit()

with open("queue.txt") as fp:
    for url in fp:
        url = url.strip().rstrip()
        if url and not url.startswith("!"):
            frontier.append(url)


def run():
    while frontier:
        if progressbar.n > TOTAL: exit()
        process_url(frontier.pop(0))


def process_url(url):
    if url not in visited:
        try:
            download_url(url)
        except Exception as e:
            logging.exception(e)
        visited.append(url)


@retry(
    stop_max_attempt_number=7,
    stop_max_delay=10000,
    retry_on_result=lambda result: result is None,
    retry_on_exception=lambda exception: isinstance(exception, Exception),
)
def download_url(url):
    url_hash = sha1(bytes(url, "utf-8")).hexdigest()
    shard = url_hash[:2]
    subdir = f"downloads/{shard}"
    filepath = f"{subdir}/{url_hash}.pickle"
    os.makedirs(subdir, exist_ok=True)
    response = requests.get(url, allow_redirects=True)
    if len(response.content) <= 10 ** 6:
        progressbar.update(len(response.content))
        progressbar.total = max(progressbar.total, progressbar.n)
    with open(filepath, "wb") as fp:
        fp.write(pickle.dumps(response))
    extract_urls(response.content, response.url)
    return filepath


def extract_urls(html, base_url):
    base_netloc = urlparse(base_url).netloc
    links = extract(str(html, "utf-8"))
    links = [urljoin(base_url, link) for link in links]
    links = [
        link for link in links if base_netloc and urlparse(link).netloc == base_netloc
    ]
    for link in links:
        if link not in visited and link not in frontier:
            frontier.append(link)


def extract(html):
    links = re.findall('href="[^#][^"]*"', html, re.IGNORECASE)
    links = [link for link in links if link and not link.startswith("#")]
    for i, link in enumerate(links):
        links[i] = link[6:-1].partition("#")[0]
    return links


if __name__ == "__main__":
    run()
