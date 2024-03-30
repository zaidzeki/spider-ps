#!/usr/bin/env python3

import lzma
import os
import pickle

import requests
from flask import Flask, Response, request

from core import decrypt, encrypt


app = Flask(__name__)


@app.route("/single.jpg", methods=["GET", "POST"])
def single():
    url = request.form.get("url") or request.args.get("url")
    url = decrypt(url)
    response = requests.get(url, allow_redirects=True)
    response.content
    data = pickle.dumps(response)
    data = encrypt(data)
    return Response(data, mimetype="image/jpg")


@app.route("/bulk.jpg", methods=["GET", "POST"])
def bulk():
    url = request.form.get("url") or request.args.get("url")
    url = decrypt(url)
    urls = url.split("\n")
    total = b""
    for url in urls:
        if not url:
            continue
        try:
            response = requests.get(url, allow_redirects=True)
            response.content
            total += pickle.dumps(response)
        except: pass
    data = lzma.compress(total)
    data = encrypt(data)
    return Response(data, mimetype="image/jpg")


# ? Bulk Defered API

DEFERED_FILEPATH = "defered.bin"


@app.route("/push.jpg", methods=["GET", "POST"])
def push():
    url = request.form.get("url") or request.args.get("url")
    url = decrypt(url)
    urls = url.split("\n")
    fp = lzma.LZMAFile(DEFERED_FILEPATH, "a")
    for url in urls:
        if not url:
            continue
        response = requests.get(url, allow_redirects=True)
        response.content
        fp.write(pickle.dumps(response))
        fp.flush()
    fp.close()
    data = bytes(f"{os.path.getsize(DEFERED_FILEPATH)}", "utf-8")
    data = encrypt(data)
    return Response(data, mimetype="image/jpg")


@app.route("/pull.jpg", methods=["GET", "POST"])
def pull():
    data = open(DEFERED_FILEPATH, "rb").read()
    data = encrypt(data)
    return Response(data, mimetype="image/jpg")

@app.route("/clear.jpg", methods=["GET", "POST"])
def clear():
    os.system(f'remove {repr(DEFERED_FILEPATH)}')
    data = b'success'
    data = encrypt(data)
    return Response(data, mimetype="image/jpg")


# TODO Add

if __name__ == "__main__":
    app.run(host=os.environ.get("IP", "::"), port=int(os.environ.get("PORT", 8100)))
