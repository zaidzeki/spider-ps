#!/usr/bin/env python3
import base64
from hashlib import sha1
import json
import logging
import os
import time
from datetime import datetime

import requests
from colorama import init, Fore, Back
from Crypto.Cipher import AES
from Crypto.Hash import MD2

from configurator import *
from sanitize_filename import sanitize
init(autoreset=True)



headers = {
    'Accept-Encoding': 'gzip, deflate',
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept': '*/*',
    'Connection': 'keep-alive',
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    'Cookie':f'MoodleSession={MoodleSession}; MOODLEID1_=%253FhT%2583S%25B0',
    'DNT': '1',
    'Host': 'lms.mcet.edu.er',
    'Origin': 'http://lms.mcet.edu.er',
    'Referer': 'http://lms.mcet.edu.er/user/files.php',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36',
    'X-Requested-With': 'XMLHttpRequest',
}

def get_sourcekey(url):
    verbose and print(Fore.LIGHTBLACK_EX + f"SourceKey: {url}")
    for i in range(MAX_RETRIES):
        try:
            data = f'file={url}&repo_id=6&p=&page=&env=filemanager&sesskey={sesskey}&client_id={client_id}&itemid={itemid}&maxbytes=524288000&areamaxbytes=1073741824&ctx_id=1691'
            resp = requests.post('http://lms.mcet.edu.er/repository/repository_ajax.php', params={'action': 'signin'}, headers=headers, data=data)
            content = str(resp.content, 'utf-8')
            if resp.status_code == 200:
                content = json.loads(content)
                data = content.get('list', [])
                if len(data):
                    return data[0]['source'], data[0]['sourcekey']
                else:
                    error = content.get('error')
                    print(url+Fore.RED + error)
                    if 'HTTP/2' in error and 'DYNAMIC' in error:
                        break
            else:
                logging.error('FAILURE IN GETTING SOURCE KEY', content)
        except Exception as e:
            logging.exception(e)

def get_localurl(url, sourcekey, title):
    verbose and print(Fore.LIGHTBLACK_EX + f"LocalURL: {url}")
    for i in range(MAX_RETRIES):
        try:
            data = f'repo_id=6&p=&page=&env=filemanager&sesskey={sesskey}&client_id={client_id}&itemid={itemid}&maxbytes=524288000&areamaxbytes=1073741824&ctx_id=1691&title={title}&source={url}&savepath=%2F&sourcekey={sourcekey}&license=unknown&author='
            resp = requests.post('http://lms.mcet.edu.er/repository/repository_ajax.php', params={'action':'download'}, headers=headers, data=data, timeout=75)
            content = str(resp.content, 'utf-8')
            if resp.status_code == 200:
                data = json.loads(content)
                return data['url'], data['file']
            else:
                logging.error('FAILURE IN GETTING LOCAL URL', content)
        except Exception as e:
            logging.exception(e)
            logging.error(content)

def delete_file(title):
    verbose and print(Fore.LIGHTBLACK_EX + f"Delete: {title}")
    for i in range(MAX_RETRIES):
        try:
            data = f'sesskey={sesskey}&client_id={client_id}&filepath=%2F&itemid={itemid}&selected=%5B%7B%22filepath%22%3A%22%2F%22%2C%22filename%22%3A%22{title}%22%7D%5D'
            resp = requests.post('http://lms.mcet.edu.er/repository/draftfiles_ajax.php', params={'action':'deleteselected'}, data=data, headers=headers)
            content = str(resp.content, 'utf-8')
            if resp.status_code == 200:
                data = json.loads(content)
                if data is False or data[0] == '/':
                    return
            else:
                logging.error('FAILURE IN DELETING FILES', content)
        except Exception as e:
            logging.exception(e)

def save_file(url, name):
    url = url.replace('http://lms.mcet.edu.er/', 'http://lms.mcet.edu.er/')
    verbose and print(Fore.LIGHTBLACK_EX + f"Saving: {url}")
    for i in range(MAX_RETRIES):
        try:
            resp = requests.get(url, headers=headers)
            with open(name, 'wb') as fp:
                fp.write(requests.get(url, headers=headers).content)
            return
        except Exception as e:
            logging.exception(e)

def download(url, name):
    for i in range(MAX_RETRIES):
        try:
            if 'http://lms.mcet.edu.er' in url:
                return False
            start = datetime.now()
            url, sourcekey = get_sourcekey(url)
            url, file = get_localurl(url, sourcekey, f'{time.time()}.png')
            save_file(url, name)
            delete_file(file)
            verbose and print(Fore.LIGHTBLACK_EX + f"It Took: {datetime.now()-start}")
            return True
        except Exception as e:
            logging.exception(e)
    return False

def convert(url, index=-1, itag=-1, youtube=False):
    def encrypt(key, data):
        """
        Encrypts data using key
        :param key: key to use to encrypt data
        :param data: data to be encrypted
        :return: encrypted data with nonce and MAC tag prepended
        """
        if type(data) == str:
            data = bytes(data, 'utf-8')
        cipher = AES.new(key, AES.MODE_EAX)
        ciphertext, tag = cipher.encrypt_and_digest(data)
        encrypted_data = cipher.nonce + tag + ciphertext
        return encrypted_data
    DOMAIN = config.get('domain')
    BASE_DIRECT = 'direct.jpg'
    BASE_PARTIAL = 'partial.jpg'
    BASE_TUBECHUNK = 'tubechunk.jpg'
    BASE_TUBEINFO = 'tubeinfo.jpg'

    url = bytes(url, 'utf-8')
    url = encrypt(b'0'*16, url)
    url = base64.urlsafe_b64encode(url)
    url = str(url, 'utf-8')
    encodedUrl = url
    # building final program
    url = 'https://'+DOMAIN
    url += '/'+encodedUrl
    if index == -1 and not youtube:
        url += '/'+BASE_DIRECT
    elif itag != -1:
        url += f'/{itag}'
        url += f'/{(index*CHUNK)}/{(index+1)*CHUNK}'
        url += '/'+BASE_TUBECHUNK
    elif youtube:
        url += '/'+BASE_TUBEINFO
    else:
        url += f'/{(index*CHUNK)}/{(index+1)*CHUNK}'
        url += '/'+BASE_PARTIAL
    return url

def direct_download(url, name, proxy=True):
    def decrypt(key, data, return_str=True):
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
                decrypted_data = str(decrypted_data, 'utf-8')
            except UnicodeError as e:
                pass
        return decrypted_data
    def decryptor(src, dest):
        with open(src, 'rb') as fin:
            with open(dest, 'wb') as fout:
                fout.write(decrypt(b'0'*16, fin.read(), False))
    if proxy:
        url = convert(url)
    if os.path.exists(name) and os.path.getsize(name) > 0:
        return True
    downloaded = download(url, name)
    if not downloaded: return False
    filename = name+'.enc'
    os.rename(name, filename)
    decryptor(filename, name)
    os.remove(filename)
    return True

def multipart_download(url, name):
    i = 0
    files = []
    failed = False
    hashed_name = sha1(bytes(name, 'utf-8')).hexdigest()
    if '/' in name: name = sanitize(name)
    while True:
        try:
            if i * CHUNK > 150000000:
                failed = True
                break
            fname = f"{i}.{CHUNK}.{hashed_name}"
            partialUrl = convert(url, i)
            downloaded = direct_download(partialUrl, fname, False)
            if not downloaded:
                failed = True
                logging.error(f'MAX RETRIES: {i} {url}')
            else:
                files.append(fname)
                if os.path.getsize(fname) == 0 or os.path.getsize(fname) < CHUNK//1.2: break
            i += 1
        except Exception as e:
            logging.exception(e)
            i += 1
            failed = True
            logging.error(f'Exception: {i} {e} {url}')

    if not failed:
        with open(name, 'wb') as fp:
            for file in files:
                with open(file, 'rb') as fin:
                    fp.write(fin.read())
        for file in files:
            os.remove(file)
    return True
